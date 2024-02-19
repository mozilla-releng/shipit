# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import backend_common
from shipit_api.common.config import APP_NAME


def create_app(config=None):
    """
    Create public API Flask application

    The corresponding OpenAPI spec is generated as a subset of the main api.yml
    file. In case the main spec is changed, you may want to regenerate the
    subset API spec by running `python ../../scripts/openapi_subset.py api.yml
    api_public.yml`
    """
    app = backend_common.create_app(
        project_name=__name__,
        app_name=APP_NAME,
        config=config,
        extensions=["log", "security", "cors", "api", "db", "dockerflow"],
        root_path=os.path.dirname(__file__),
    )
    app.api.register(os.path.join(os.path.dirname(__file__), "api.yml"))
    return app
