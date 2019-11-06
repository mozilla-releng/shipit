# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import flask
import flask_migrate
import flask_sqlalchemy

import backend_common.dockerflow
import cli_common.log

logger = cli_common.log.get_logger(__name__)
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate(db=db)


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw, _test_hook=None):
    # Based on
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/UniqueObject
    cache = session.info.get("_unique_cache", None)
    if cache is None:
        session.info["_unique_cache"] = cache = {}

        # Setup to clear session cache on rollback
        @db.event.listens_for(session, "after_rollback", once=True)
        def _clear_session_cache(s):
            if s.info.get("_unique_cache", None):
                del s.info["_unique_cache"]

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if _test_hook:
                _test_hook()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
                session.flush()
        cache[key] = obj
        return obj


class UniqueMixin(object):
    # Based on
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/UniqueObject

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(session, cls, cls.unique_hash, cls.unique_filter, cls, arg, kw)


def init_database(app):
    """
    Run Migrations through Alembic
    """
    migrations_dir = os.path.abspath(os.path.join(app.root_path, "..", "migrations"))

    with app.app_context():

        # Needed to init potential migrations later on
        # Use a separate alembic_version table per app
        options = {f"version_table": "{app.import_name}_alembic_version"}
        migrate.init_app(app, directory=migrations_dir, **options)

        if os.path.isdir(migrations_dir):
            logger.info("Starting migrations", app=app.name)
            try:
                flask_migrate.upgrade()
                logger.info("Completed migrations", app=app.name)
            except Exception as e:
                logger.error("Migrations failure", app=app.name, error=e)

        else:
            logger.info("No migrations: creating full DB", app=app.name)
            db.create_all()


def init_app(app):
    db.init_app(app)

    # Try to run migrations on the app
    # or direct db creation
    init_database(app)

    @app.before_request
    def setup_request():
        flask.g.db = app.db

    return db


def app_heartbeat():
    try:
        db = flask.current_app.db
        db.session.execute("SELECT 1").fetchall()
    except Exception as e:
        logger.exception(e)
        raise backend_common.dockerflow.HeartbeatException("Cannot connect to the database.")
