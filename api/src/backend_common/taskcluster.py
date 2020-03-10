# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import taskcluster
from flask import current_app

TC_SERVICES_REQUIRE_AUTH = ["auth", "hooks", "notify", "secrets"]


def get_root_url():
    return current_app.config["TASKCLUSTER_ROOT_URL"]


def get_options(service_name):
    """
    Build Taskcluster credentials options
    """

    tc_options = {"rootUrl": get_root_url(), "maxRetries": 12}
    if service_name in TC_SERVICES_REQUIRE_AUTH:
        client_id = current_app.config["TASKCLUSTER_CLIENT_ID"]
        access_token = current_app.config["TASKCLUSTER_ACCESS_TOKEN"]
        tc_options.update({"credentials": {"clientId": client_id, "accessToken": access_token}})

    return tc_options


def get_service(service_name):
    """
    Build a Taskcluster service instance
    """
    options = get_options(service_name)
    return getattr(taskcluster, service_name.capitalize())(options)
