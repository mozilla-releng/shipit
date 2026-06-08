# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import os
from unittest.mock import Mock

import aiohttp
import pytest
import responses as rsps

import backend_common.testing
from shipit_api.common.models import XPI, XPIRelease

# Cribbed from https://github.com/j7an/dep-rank/pull/123
# aiohttp 3.14 added a required keyword-only ``stream_writer`` argument to
# ``ClientResponse.__init__``. aioresponses (<=0.7.8) builds mocked responses
# without it, so every mocked request raises ``TypeError: ... missing 1
# required keyword-only argument: 'stream_writer'``. aiohttp only reads
# ``stream_writer.output_size``, so a ``Mock(output_size=0)`` suffices.
#
# This mirrors the upstream fix (aioresponses#288, tracking aioresponses#289).
# The signature guard makes it a no-op on aiohttp < 3.14 and once aioresponses
# ships a release that supplies the argument itself; remove this shim then.
_response_init = aiohttp.ClientResponse.__init__
if "stream_writer" in inspect.signature(_response_init).parameters:

    def _patched_response_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        _response_init(self, *args, **kwargs)

    aiohttp.ClientResponse.__init__ = _patched_response_init


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
        phase_obj = release.phase_class(name=phase, task_id="", task={}, context={}, scheduled_by=None)
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
