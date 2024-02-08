# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib
import logging
import os
from functools import cache
from pathlib import PosixPath

import flask
import yaml
from deepmerge import merge_or_raise

EXTENSIONS = ["dockerflow", "log", "security", "cors", "api", "auth", "pulse", "db"]

logger = logging.getLogger(__name__)


def create_app(project_name, app_name, root_path, extensions=[], config=None, redirect_root_to_api=True, **kwargs):
    """
    Create a new Flask backend application
    app_name is the Python application name, used as Flask import_name
    project_name is a "nice" name, used to identify the application
    """
    logger.debug("Initializing %s", app_name)

    app = flask.Flask(import_name=app_name, root_path=root_path, **kwargs)
    app.name = project_name
    app.__extensions = extensions

    if config:
        if isinstance(config, str):
            app.config.from_pyfile(config)
        elif isinstance(config, PosixPath):
            app.config.from_pyfile(str(config))
        else:
            app.config.from_mapping(config)

    for extension_name in EXTENSIONS:
        if app.config.get("TESTING") and extension_name in ["security", "cors"]:
            continue

        if extension_name not in extensions:
            logger.debug("Skipping extension %s", extension_name)
            continue

        logger.debug("Initializing extension %s", extension_name)

        extension_init_app = getattr(importlib.import_module(f"backend_common.{extension_name}"), "init_app", None)
        if extension_init_app is None:
            raise RuntimeError(f"Could not find {extension_name}.init_app function")

        extension = extension_init_app(app)
        if extension and extension_name is not None:
            setattr(app, extension_name, extension)

        logger.debug("Extension %s initialized", extension_name)

    if redirect_root_to_api:
        app.add_url_rule("/", "root", lambda: flask.redirect(app.api.swagger_url))

    app.api.register(build_api_specification(root_path))
    logger.debug("Initialized %s", app.name)
    return app


def build_api_specification(root_path):
    openapi_spec = _get_specifications_from_openapi_yaml_files(root_path)
    schemas = openapi_spec["components"]["schemas"]
    schemas["ProductInput"]["enum"] = get_product_names()
    schemas["ProductOutput"]["enum"] = get_product_names(include_legacy=True)
    return openapi_spec


def _get_specifications_from_openapi_yaml_files(root_path):
    common_api = os.path.join(os.path.dirname(__file__), "api.yml")
    specific_api = os.path.join(root_path, "api.yml")
    return merge_or_raise.merge(
        _read_specification_file(common_api),
        _read_specification_file(specific_api),
    )


def get_product_names(include_legacy=False):
    products_config = get_products_config()
    return [product_name for product_name, product_config in products_config.items() if not product_config["legacy"] or include_legacy]


@cache
def get_products_config():
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "products.yml")) as f:
        products_config = yaml.safe_load(f)

    _set_products_config_default_values(products_config)
    return products_config


def _set_products_config_default_values(products_config):
    for product_config in products_config.values():
        product_config.setdefault("legacy", False)
        product_config.setdefault("phases", [])


def _read_specification_file(path):
    with open(path) as f:
        return yaml.safe_load(f)
