# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest
import responses as rsps

import backend_common.testing
from shipit_api.common.models import XPI, XPIRelease


@pytest.fixture
def responses():
    with rsps.RequestsMock() as req_mock:
        yield req_mock


@pytest.fixture(scope="session")
def global_app():
    """Load shipit_api in test mode"""
    import shipit_api.admin

    config = backend_common.testing.get_app_config(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "AUTH_CLIENT_ID": "dummy_id",
            "AUTH_CLIENT_SECRET": "dummy_secret",
            "OIDC_USER_INFO_ENABLED": True,
            "OIDC_CLIENT_SECRETS": os.path.join(os.path.dirname(__file__), "mock_client_secrets.json"),
            "TASKCLUSTER_ROOT_URL": "https://something",
            "TASKCLUSTER_CLIENT_ID": "something",
            "TASKCLUSTER_ACCESS_TOKEN": "something",
            "AUTH0_AUTH_SCOPES": {
                "project:releng:services/shipit_api/add_release/firefox": "releng",
                "project:releng:services/shipit_api/add_release/firefox-ios": "releng",
                "project:releng:services/shipit_api/schedule_phase/firefox/promote": "releng",
                "project:releng:services/shipit_api/schedule_phase/firefox/ship": "releng",
            },
        }
    )
    app = shipit_api.admin.create_app(config)

    with app.app.app_context():
        backend_common.testing.configure_app(app.app)
        yield app


@pytest.fixture(scope="function")
def app(global_app):
    global_app.app.db.create_all()
    try:
        yield global_app
    finally:
        global_app.app.db.drop_all()
        global_app.app.db.session.close()


def mock_generate_phases(release):
    phases = []
    for phase in ["build", "promote", "ship"]:
        phase_obj = release.phase_class(name=phase, task_id="", task={}, context={}, completed_by=None)
        phase_obj.signoffs = release.phase_signoffs(phase)
        phases.append(phase_obj)
    return phases


@pytest.fixture
def test_xpi_release():
    xpi = XPI(name="staging-public", revision="2c91fa1f75a1e0ff8b16055b944fe1d2fe10175", version="1.0.0")
    release = XPIRelease(
        build_number=5, revision="be8a48ca7a82c79cefc8ac10dee182005cdbd3c7", status="scheduled", xpi_type="addon-type", project="staging-xpi-manifest", xpi=xpi
    )
    release.phases = mock_generate_phases(release)
    return release
