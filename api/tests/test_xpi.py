from unittest import mock

import backend_common.auth
from shipit_api.common.models import XPI, XPIRelease


def _create_xpi_release(session):
    xpi = XPI(name="test-addon", revision="abc123", version="1.0.0")
    release = XPIRelease(
        build_number=1,
        revision="abc123",
        status="scheduled",
        xpi_type="privileged",
        project="xpi",
        xpi=xpi,
    )
    session.add(release)
    session.commit()
    return release


@mock.patch("shipit_api.admin.xpi._xpi_type", return_value="privileged")
def test_cancel_xpi_release(mock_xpi_type, app):
    release = _create_xpi_release(app.app.db.session)
    app.app.config["AUTH0_AUTH_SCOPES"]["project:releng:services/shipit_api/abandon_release/xpi/privileged"] = ["foobar"]
    with mock.patch(
        "shipit_api.admin.xpi.current_user",
        backend_common.auth.Auth0User("", {"email": "admin@mozilla.com", "https://sso.mozilla.com/claim/groups": ["foobar"]}),
    ):
        with app.test_client() as client:
            response = client.delete(f"/xpi/releases/{release.name}")
            assert response.status_code == 200


@mock.patch("shipit_api.admin.xpi._xpi_type", side_effect=TypeError("'NoneType' object is not subscriptable"))
def test_cancel_xpi_release_admin_fallback(mock_xpi_type, app):
    release = _create_xpi_release(app.app.db.session)
    app.app.config["AUTH0_AUTH_SCOPES"]["project:releng:services/shipit_api/abandon_release/xpi"] = ["releng"]
    with mock.patch(
        "shipit_api.admin.xpi.current_user",
        backend_common.auth.Auth0User("", {"email": "admin@mozilla.com", "https://sso.mozilla.com/claim/groups": ["releng"]}),
    ):
        with app.test_client() as client:
            response = client.delete(f"/xpi/releases/{release.name}")
            assert response.status_code == 200


@mock.patch("shipit_api.admin.xpi._xpi_type", side_effect=TypeError("'NoneType' object is not subscriptable"))
def test_cancel_xpi_release_admin_fallback_denied(mock_xpi_type, app):
    release = _create_xpi_release(app.app.db.session)
    app.app.config["AUTH0_AUTH_SCOPES"]["project:releng:services/shipit_api/abandon_release/xpi"] = ["releng"]
    with mock.patch(
        "shipit_api.admin.xpi.current_user",
        backend_common.auth.Auth0User("", {"email": "user@mozilla.com", "https://sso.mozilla.com/claim/groups": ["some_other_group"]}),
    ):
        with app.test_client() as client:
            response = client.delete(f"/xpi/releases/{release.name}")
            assert response.status_code == 401
