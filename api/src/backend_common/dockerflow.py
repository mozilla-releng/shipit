# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Provide API endpoint for Dockerflow
https://github.com/mozilla-services/Dockerflow
"""
import logging

from dockerflow.flask import Dockerflow

dockerflow = Dockerflow(version_path="/app")


def init_app(app):
    # Suppress heartbeat logs
    dockerflow.logger.setLevel(logging.ERROR)
    dockerflow.init_app(app)
    return dockerflow
