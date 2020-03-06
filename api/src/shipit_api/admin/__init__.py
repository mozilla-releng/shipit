# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import backend_common
import shipit_api.admin.models  # noqa
import shipit_api.common.models  # noqa
from shipit_api.admin.worker import cmd
from shipit_api.common.config import APP_NAME


def create_app(config=None):
    app = backend_common.create_app(
        project_name=__name__,
        app_name=APP_NAME,
        config=config,
        extensions=["dockerflow", "log", "security", "cors", "api", "auth", "db", "pulse"],
        root_path=os.path.dirname(__file__),
    )
    app.api.register(os.path.join(os.path.dirname(__file__), "api.yml"))
    app.cli.add_command(cmd, "worker")

    return app
