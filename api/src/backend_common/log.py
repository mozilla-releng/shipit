# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import sys

import sentry_sdk
from dockerflow.logging import JsonLogFormatter
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_app(app):
    """
    Init logger from a Flask Application
    """
    configure_logging()
    # Log to sentry
    environment = app.config.get("APP_CHANNEL")
    sentry_dsn = app.config.get("SENTRY_DSN")
    if environment and sentry_dsn:
        configure_sentry(environment, sentry_dsn)


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    level = logging.DEBUG if os.environ.get("DEBUG") else logging.INFO
    if os.environ.get("LOG_FORMAT") == "plain":
        handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(levelname)s: %(message)s"))
        # The request.summary logger heavily uses the `extra` dict. As a result
        # the default formatter prints only empty messages.
        summary_logger = logging.getLogger("request.summary")
        summary_logger.setLevel(logging.ERROR)
    else:
        handler.setFormatter(JsonLogFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


def configure_sentry(environment, sentry_dsn):
    sentry_sdk.init(dsn=sentry_dsn, environment=environment, integrations=[LoggingIntegration(), FlaskIntegration()])
