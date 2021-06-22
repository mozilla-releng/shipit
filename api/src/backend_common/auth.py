# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import enum
import functools
import json
import logging
import tempfile

import flask
import flask_login
import flask_oidc
import requests
from dockerflow.flask import checks

from backend_common.dockerflow import dockerflow
from backend_common.taskcluster import get_service

logger = logging.getLogger(__name__)

UNAUTHORIZED_JSON = {
    "status": 401,
    "title": "401 Unauthorized: Invalid user permissions",
    "detail": "Invalid user permissions",
    "instance": "about:blank",
    "type": "about:blank",
}


@enum.unique
class AuthType(enum.Enum):
    NONE = None
    ANONYMOUS = "anonymous"
    AUTH0 = "auth0"


class BaseUser(object):

    anonymous = False
    type = AuthType.NONE

    def __eq__(self, other):
        return isinstance(other, BaseUser) and self.get_email() == other.get_email()

    @property
    def is_authenticated(self):
        return not self.anonymous

    @property
    def is_active(self):
        return not self.anonymous

    @property
    def is_anonymous(self):
        return self.anonymous

    @property
    def permissions(self):
        return self.get_permissions()

    def get_permissions(self):
        return set()

    def get_ldap_groups(self):
        raise NotImplementedError

    def get_email(self):
        raise NotImplementedError

    # Flask internals is looking for get_id()
    def get_id(self):
        return self.get_email()

    def has_permissions(self, permissions):

        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]

        user_permissions = self.get_permissions()

        return all([permission in list(user_permissions) for permission in permissions])

    def __str__(self):
        return self.get_ldap_groups()


def create_auth0_secrets_file(auth_client_id, auth_client_secret, auth_domain):
    _, secrets_file = tempfile.mkstemp()
    with open(secrets_file, "w+") as f:
        f.write(
            json.dumps(
                {
                    "web": {
                        "auth_uri": f"https://{auth_domain}/authorize",
                        "issuer": f"https://{auth_domain}/",
                        "client_id": auth_client_id,
                        "client_secret": auth_client_secret,
                        "token_uri": f"https://{auth_domain}/oauth/token",
                        "userinfo_uri": f"https://{auth_domain}/userinfo",
                    }
                }
            )
        )
    return secrets_file


class AnonymousUser(BaseUser):

    anonymous = True
    type = AuthType.ANONYMOUS

    def get_ldap_groups(self):
        return "anonymous:"

    def get_email(self):
        return "anonymous:"


class Auth0User(BaseUser):

    type = AuthType.AUTH0

    def __init__(self, token, userinfo):
        if not isinstance(token, str):
            raise Exception("token should be a string")

        if "email" not in userinfo:
            raise Exception("userinfo should contain email")

        if not isinstance(userinfo["email"], str):
            raise Exception('userinfo["email"] should be a string')

        self.token = token
        self.userinfo = userinfo

        logger.info("Init user %s", self.get_email())

    def get_email(self):
        return self.userinfo["email"]

    def get_ldap_groups(self):
        return self.userinfo["https://sso.mozilla.com/claim/groups"]

    def get_permissions(self):
        user_ldap_groups = self.get_ldap_groups()
        all_permissions = flask.current_app.config.get("AUTH0_AUTH_SCOPES", dict())
        return [permission for permission, permission_groups in all_permissions.items() if set(user_ldap_groups).intersection(set(permission_groups))]

    def has_permissions(self, permissions):
        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]
        user_permissions = self.get_permissions()
        return all(map(lambda p: p in user_permissions, permissions))


class Auth(object):
    def __init__(self, anonymous_user):
        self.login_manager = flask_login.LoginManager()
        self.login_manager.anonymous_user = anonymous_user
        self.app = None

    def init_app(self, app):
        self.app = app
        self.login_manager.init_app(app)

    def _require_login(self):
        with flask.current_app.app_context():
            try:
                return flask_login.current_user.is_authenticated
            except Exception as e:
                logger.info("Invalid authentication: %s", e)
                return False

    def _require_permissions(self, permissions):
        if not self._require_login():
            return False

        with flask.current_app.app_context():
            if not flask_login.current_user.has_permissions(permissions):
                users_email = flask_login.current_user.get_email()
                user_permissions = flask_login.current_user.get_permissions()
                diff = " OR ".join([", ".join(set(p).difference(user_permissions)) for p in permissions])
                logger.info("User %s misses some permissions: %s", users_email, diff)
                return False

        return True

    def require_permissions(self, permissions):
        """Decorator to check if user has required permissions or set of
        permissions
        """

        def decorator(method):
            @functools.wraps(method)
            def wrapper(*args, **kwargs):
                logger.info("Checking permissions %s", permissions)
                if self._require_permissions(permissions):
                    # Validated permissions, running method
                    logger.info("Validated permissions, processing api request")
                    return method(*args, **kwargs)
                else:
                    # Abort with a 401 status code
                    return flask.jsonify(UNAUTHORIZED_JSON), 401

            return wrapper

        return decorator


auth0 = flask_oidc.OpenIDConnect()
auth = Auth(anonymous_user=AnonymousUser)


@auth.login_manager.request_loader
def parse_header(request):
    """Parse header and try to authenticate"""
    if "access_token" in request.form:
        token = request.form["access_token"]
    elif "access_token" in request.args:
        token = request.args["access_token"]
    else:
        auth = request.headers.get("Authorization")
        if not auth:
            return None

        parts = auth.split()

        if parts[0].lower() != "bearer" or len(parts) == 1 or len(parts) > 2:
            return None

        token = parts[1]

    auth_domain = flask.current_app.config.get("AUTH_DOMAIN")
    url = auth0.client_secrets.get("userinfo_uri", f"https://{auth_domain}/userinfo")

    payload = {"access_token": token}
    response = requests.get(url, params=payload)

    # Because auth0 returns http 200 even if the token is invalid.
    if response.content == b"Unauthorized" or not response.ok:
        return None

    userinfo = json.loads(str(response.content, "utf-8"))

    return Auth0User(token, userinfo)


def get_permissions():
    response = dict(description="Permissions of a logged in user", user_id=None, permissions=[])
    user = flask_login.current_user

    if user.is_authenticated:
        response["user_id"] = user.get_ldap_groups()
        response["permissions"] = user.get_permissions()

    return flask.Response(status=200, response=json.dumps(response), headers={"Content-Type": "application/json", "Cache-Control": "public, max-age=60"})


def init_app(app):
    if app.config.get("SECRET_KEY") is None:
        raise Exception("When using `auth` extention you need to specify SECRET_KEY.")

    auth0.init_app(app)
    auth.init_app(app)

    app.add_url_rule("/__permissions__", view_func=get_permissions)

    return auth


@dockerflow.check(name="auth")
def app_heartbeat():
    config = flask.current_app.config
    results = []

    try:
        auth_domain = config.get("AUTH_DOMAIN")
        r = requests.get(f"https://{auth_domain}/test")
        assert "clock" in r.json()
    except Exception:
        logger.info("Auth0 heartbeat error")
        results.append(checks.Error("Cannot connect to the mozilla auth0 service.", id="auth.auth0"))

    auth = get_service("auth")
    try:
        ping = auth.ping()
        assert ping["alive"] is True
    except Exception:
        logger.info("Taskcluster heartbeat error")
        results.append(checks.Error("Cannot connect to the Taskcluster service.", id="auth.taskcluster"))

    return results
