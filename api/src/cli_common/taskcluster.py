# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import os

import click
import taskcluster


def get_options(root_url, client_id, access_token):
    """
    Build Taskcluster credentials options
    """

    tc_options = {"credentials": {"clientId": client_id, "accessToken": access_token}, "rootUrl": root_url, "maxRetries": 12}

    return tc_options


def get_root_url():
    """Return Taskcluster Root URL specified by command line or environment
       variable."""
    root_url = None
    try:
        ctx = click.get_current_context()
        root_url = ctx.params.get("taskcluster_root_url")
    except RuntimeError:
        pass  # no active context

    if not root_url:
        root_url = os.environ.get("TASKCLUSTER_ROOT_URL")

    return root_url


def get_service(service_name, client_id=None, access_token=None):
    """
    Build a Taskcluster service instance from the environment
    Supports:
     * directly provided credentials
     * credentials from click
     * credentials from environment variables
    """
    # Credentials preference: Use click variables
    if client_id is None and access_token is None:
        try:
            ctx = click.get_current_context()
            client_id = ctx.params.get("taskcluster_client_id")
            access_token = ctx.params.get("taskcluster_access_token")
        except RuntimeError:
            pass  # no active context

    # Credentials preference: Use env. variables
    if client_id is None and access_token is None:
        client_id = os.environ.get("TASKCLUSTER_CLIENT_ID")
        access_token = os.environ.get("TASKCLUSTER_ACCESS_TOKEN")

    # Instanciate service
    options = get_options(get_root_url(), client_id, access_token)
    return getattr(taskcluster, service_name.capitalize())(options)


def get_secrets(name, project_name, required=[], existing=dict(), taskcluster_client_id=None, taskcluster_access_token=None):
    """
    Fetch a specific set of secrets by name and verify that the required
    secrets exist.

    Merge secrets in the following order (the latter overrides the former):
        - `existing` argument
        - common secrets, specified under the `common` key in the secrets
          object
        - project specific secrets, specified under the `project_name` key in
          the secrets object
    """

    secrets = dict()
    if existing:
        secrets = copy.deepcopy(existing)

    all_secrets = dict()
    if name:
        secrets_service = get_service("secrets", taskcluster_client_id, taskcluster_access_token)
        all_secrets = secrets_service.get(name).get("secret", dict())

    secrets_common = all_secrets.get("common", dict())
    secrets.update(secrets_common)

    secrets_app = all_secrets.get(project_name, dict())
    secrets.update(secrets_app)

    for required_secret in required:
        if required_secret not in secrets:
            raise Exception(f"Missing value {required_secret} in secrets.")

    return secrets
