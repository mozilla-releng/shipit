# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib
import os

import flask

import backend_common.dockerflow
import cli_common.log

EXTENSIONS = ["log", "security", "cors", "api", "auth", "cache", "pulse", "db"]

logger = cli_common.log.get_logger(__name__)


def create_app(project_name, app_name, extensions=[], config=None, redirect_root_to_api=True, enable_dockerflow=True, **kw):
    """
    Create a new Flask backend application
    app_name is the Python application name, used as Flask import_name
    project_name is a "nice" name, used to identify the application
    """
    logger.debug("Initializing", app=app_name)

    app = flask.Flask(import_name=app_name, **kw)
    app.name = project_name
    app.__extensions = extensions

    if config:
        app.config.update(**config)

    if not app.config.get("TESTING") and os.environ.get("APP_SETTINGS"):
        app.config.from_envvar("APP_SETTINGS")

    if config:
        app.config.update(**config)

    for extension_name in EXTENSIONS:
        if app.config.get("TESTING") and extension_name in ["security", "cors"]:
            continue

        if extension_name not in extensions:
            continue

        logger.debug("Initializing extension", extension=extension_name, app=app.name)

        extension_init_app = None
        try:
            extension_init_app = getattr(importlib.import_module("backend_common." + extension_name), "init_app")
        except Exception as e:
            logger.exception(e)
            pass

        if extension_init_app is None:
            raise Exception(f"Could not import backend_common extension: {extension_name}")

        extension = extension_init_app(app)
        if extension and extension_name is not None:
            setattr(app, extension_name, extension)

        logger.debug("Extension initialized", extension=extension_name, app=app.name)

    if redirect_root_to_api:
        app.add_url_rule("/", "root", lambda: flask.redirect(app.api.swagger_url))

    if enable_dockerflow:
        app.add_url_rule("/__heartbeat__", view_func=backend_common.dockerflow.heartbeat_response)
        app.add_url_rule("/__lbheartbeat__", view_func=backend_common.dockerflow.lbheartbeat_response)
        app.add_url_rule("/__version__", view_func=backend_common.dockerflow.get_version)

    logger.debug("Initialized", app=app.name)
    return app
