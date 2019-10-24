# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import functools
import json
import os
import time

import flask
import flask_login
import flask_oidc
import itsdangerous
import pytz
import requests
import sqlalchemy as sa
import taskcluster.utils

import backend_common.db
import backend_common.dockerflow
import cli_common.log
import cli_common.taskcluster

logger = cli_common.log.get_logger(__name__)

UNAUTHORIZED_JSON = {
    "status": 401,
    "title": "401 Unauthorized: Invalid user permissions",
    "detail": "Invalid user permissions",
    "instance": "about:blank",
    "type": "about:blank",
}


class BaseUser(object):

    anonymous = False
    type = None

    def __eq__(self, other):
        return isinstance(other, BaseUser) and self.get_id() == other.get_id()

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

    def get_id(self):
        raise NotImplementedError

    def has_permissions(self, permissions):

        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]

        user_permissions = self.get_permissions()

        return all([permission in list(user_permissions) for permission in permissions])

    def __str__(self):
        return self.get_id()


class AnonymousUser(BaseUser):

    anonymous = True
    type = "anonymous"

    def get_id(self):
        return "anonymous:"


class TaskclusterUser(BaseUser):

    type = "taskcluster"

    def __init__(self, credentials):
        if not isinstance(credentials, dict):
            raise Exception("credentials should be a dict")

        if "clientId" not in credentials:
            raise Exception(f"credentials should contain clientId, {credentials}")

        if not isinstance(credentials["clientId"], str):
            raise Exception('credentials["clientId"] should be a string')

        if "scopes" not in credentials:
            raise Exception("credentials should contain scopes")

        if not isinstance(credentials["scopes"], list):
            raise Exception('credentials["scopes"] should be a list')

        self.credentials = credentials

        logger.info(f"Init user {self.get_id()}")

    def get_id(self):
        return self.credentials["clientId"]

    def get_permissions(self):
        return self.credentials["scopes"]

    def has_permissions(self, permissions):
        """
        Check user has some required permissions
        Using Taskcluster comparison algorithm
        """
        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]

        if not isinstance(permissions[0], (tuple, list)):
            permissions = [permissions]

        return taskcluster.utils.scopeMatch(self.get_permissions(), permissions)


class Auth0User(BaseUser):

    type = "auth0"

    def __init__(self, token, userinfo):
        if not isinstance(token, str):
            raise Exception("token should be a string")

        if "email" not in userinfo:
            raise Exception("userinfo should contain email")

        if not isinstance(userinfo["email"], str):
            raise Exception('userinfo["email"] should be a string')

        self.token = token
        self.userinfo = userinfo

        logger.info("Init user {}".format(self.get_id()))

    def get_id(self):
        return self.userinfo["email"]

    def get_permissions(self):
        user = self.get_id()
        all_permissions = flask.current_app.config.get("AUTH0_AUTH_SCOPES", dict())
        return [permission for permission, users in all_permissions.items() if user in users]

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
                logger.error(f"Invalid authentication: {e}")
                return False

    def require_login(self, method):
        """Decorator to check if user is authenticated
        """

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            if self._require_login():
                return method(*args, **kwargs)
            return "Unauthorized", 401

        return wrapper

    def _require_permissions(self, permissions):
        if not self._require_login():
            return False

        with flask.current_app.app_context():
            if not flask_login.current_user.has_permissions(permissions):
                user = flask_login.current_user.get_id()
                user_permissions = flask_login.current_user.get_permissions()
                diff = " OR ".join([", ".join(set(p).difference(user_permissions)) for p in permissions])
                logger.error(f"User {user} misses some permissions: {diff}")
                return False

        return True

    def require_permissions(self, permissions):
        """Decorator to check if user has required permissions or set of
           permissions
        """

        def decorator(method):
            @functools.wraps(method)
            def wrapper(*args, **kwargs):
                logger.info("Checking permissions", permissions=permissions)
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
NO_AUTH = object()


def parse_header_taskcluster(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        auth_header = request.headers.get("Authentication")
    if not auth_header:
        return NO_AUTH
    if not auth_header.startswith("Hawk"):
        return NO_AUTH

    # Get Endpoint configuration
    if ":" in request.host:
        host, port = request.host.split(":")
    else:
        host = request.host
        port = request.environ.get("HTTP_X_FORWARDED_PORT")
        if port is None:
            port = request.scheme == "https" and 443 or 80
    method = request.method.lower()

    # Build taskcluster payload
    payload = {"resource": request.path, "method": method, "host": host, "port": int(port), "authorization": auth_header}

    # Auth with taskcluster
    auth = cli_common.taskcluster.get_service("auth", **get_taskcluster_credentials())
    try:
        resp = auth.authenticateHawk(payload)
        if not resp.get("status") == "auth-success":
            raise Exception("Taskcluster rejected the authentication")
    except Exception as e:
        logger.error(f"TC auth error: {e}")
        logger.error(f"TC auth details: {payload}")
        return NO_AUTH

    return TaskclusterUser(resp)


def parse_header_auth0(request):
    if "access_token" in request.form:
        token = request.form["access_token"]
    elif "access_token" in request.args:
        token = request.args["access_token"]
    else:
        auth = request.headers.get("Authorization")
        if not auth:
            return NO_AUTH

        parts = auth.split()

        if parts[0].lower() != "bearer" or len(parts) == 1 or len(parts) > 2:
            return NO_AUTH

        token = parts[1]

    auth_domain = flask.current_app.config.get("AUTH_DOMAIN")
    url = auth0.client_secrets.get("userinfo_uri", f"https://{auth_domain}/userinfo")

    payload = {"access_token": token}
    response = requests.get(url, params=payload)

    # Because auth0 returns http 200 even if the token is invalid.
    if response.content == b"Unauthorized" or not response.ok:
        return NO_AUTH

    userinfo = json.loads(str(response.content, "utf-8"))

    return Auth0User(token, userinfo)


def get_taskcluster_credentials():
    if flask.current_app.config["TESTING"] is True:
        return dict(client_id="XXX", access_token="YYY")
    return dict(
        client_id=os.environ.get("TASKCLUSTER_CLIENT_ID", flask.current_app.config.get("TASKCLUSTER_CLIENT_ID")),
        access_token=os.environ.get("TASKCLUSTER_ACCESS_TOKEN", flask.current_app.config.get("TASKCLUSTER_ACCESS_TOKEN")),
    )


@auth.login_manager.request_loader
def parse_header(request):
    """Parse header and try to authenticate
    """
    if flask.current_app.config.get("AUTH0_AUTH") is True:
        user = parse_header_auth0(request)
        if user != NO_AUTH:
            return user

    if flask.current_app.config.get("TASKCLUSTER_AUTH", True) is True:
        user = parse_header_taskcluster(request)
        if user != NO_AUTH:
            return user


def get_permissions():
    response = dict(description="Permissions of a logged in user", user_id=None, permissions=[])
    user = flask_login.current_user

    if user.is_authenticated:
        response["user_id"] = user.get_id()
        response["permissions"] = user.get_permissions()

    return flask.Response(status=200, response=json.dumps(response), headers={"Content-Type": "application/json", "Cache-Control": "public, max-age=60"})


def init_app(app):
    if app.config.get("SECRET_KEY") is None:
        raise Exception("When using `auth` extention you need to specify SECRET_KEY.")

    if app.config.get("AUTH0_AUTH") is True:
        auth0.init_app(app)

    auth.init_app(app)

    app.add_url_rule("/__permissions__", view_func=get_permissions)

    return auth


def app_heartbeat():
    config = flask.current_app.config

    if config.get("AUTH0_AUTH") is True:
        try:
            r = requests.get("https://auth.mozilla.auth0.com/test")
            assert "clock" in r.json()
        except Exception as e:
            logger.exception(e)
            raise backend_common.dockerflow.HeartbeatException("Cannot connect to the mozilla auth0 service.")

    if config.get("TASKCLUSTER_AUTH") is True:
        auth = cli_common.taskcluster.get_service("auth", **get_taskcluster_credentials())
        try:
            ping = auth.ping()
            assert ping["alive"] is True
        except Exception as e:
            logger.exception(e)
            raise backend_common.dockerflow.HeartbeatException("Cannot connect to the taskcluster auth service.")
