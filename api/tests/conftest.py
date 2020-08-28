# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

import backend_common


@pytest.fixture(scope="session")
def app():
    """Load shipit_api in test mode"""
    import shipit_api

    config = backend_common.testing.get_app_config(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "AUTH_CLIENT_ID": "dummy_id",
            "AUTH_CLIENT_SECRET": "dummy_secret",
            "OIDC_USER_INFO_ENABLED": True,
            "OIDC_CLIENT_SECRETS": os.path.join(os.path.dirname(__file__), "client_secrets.json"),
            "TASKCLUSTER_ROOT_URL": "https://something",
            "TASKCLUSTER_CLIENT_ID": "something",
            "TASKCLUSTER_ACCESS_TOKEN": "something",
        }
    )
    app = shipit_api.create_app(config)

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app
