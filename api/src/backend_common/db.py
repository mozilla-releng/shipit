# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

import flask
import flask_migrate
import flask_sqlalchemy
from dockerflow.flask import checks

from backend_common.dockerflow import dockerflow

logger = logging.getLogger(__name__)
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate(db=db)


def init_database(app):
    """
    Run Migrations through Alembic
    """
    migrations_dir = os.path.abspath(os.path.join(app.root_path, "..", "migrations"))

    with app.app_context():

        if os.path.isdir(migrations_dir):
            # Needed to init potential migrations later on
            # Use a separate alembic_version table per app
            options = {"version_table": "{app.import_name}_alembic_version"}
            migrate.init_app(app, directory=migrations_dir, **options)

            logger.info("Starting migrations %s", app.name)
            try:
                flask_migrate.upgrade()
                logger.info("Completed migrations %s", app.name)
            except Exception:
                logger.exception("Migrations failure %s", app.name)

        else:
            if flask.current_app.config.get("READONLY_API"):
                logger.info("Skipping DB creation for a read-only app %s", app.name)
            else:
                logger.info("No migrations: creating full DB, %s", app.name)
                db.create_all()


def init_app(app):
    db.init_app(app)

    # Try to run migrations on the app or direct db creation
    init_database(app)
    dockerflow.init_check(checks.check_database_connected, db)

    @app.before_request
    def setup_request():
        flask.g.db = app.db

    return db
