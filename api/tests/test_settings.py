import os


def flatten(lst):
    return [item for sublist in lst for item in sublist]


def test_somethig(monkeypatch):
    FAKE_ENV = dict(
        APP_CHANNEL="development",
        TASKCLUSTER_ROOT_URL="fake",
        TASKCLUSTER_CLIENT_ID="fake",
        TASKCLUSTER_ACCESS_TOKEN="fake",
        AUTH_DOMAIN="fake",
        AUTH_CLIENT_ID="fake",
        AUTH_CLIENT_SECRET="fake",
        SECRET_KEY_BASE64="fake",
        DATABASE_URL="fake",
    )
    # mock the environment in order to import settings
    monkeypatch.setattr(os, "environ", FAKE_ENV)

    from shipit_api.admin.settings import (
        AUTH0_AUTH_SCOPES,
        GROUPS,
        XPI_PRIVILEGED_BUILD_GROUP,
        XPI_PRIVILEGED_ADMIN_GROUP,
        XPI_SYSTEM_ADMIN_GROUP,
        XPI_MOZILLAONLINE_PRIVILEGED_GROUP,
        XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_GROUP,
    )

    # make sure the admin group has all scopes
    assert all([set(GROUPS["admin"]).issubset(entry) for entry in AUTH0_AUTH_SCOPES.values()])

    # github API, for XPI and Fenix groups only
    github_users = flatten([users for group, users in GROUPS.items() if group.startswith("xpi_") or group.startswith("fenix_")])
    assert set(github_users).issubset(set(AUTH0_AUTH_SCOPES["project:releng:services/shipit_api/github"]))

    # firefox-signoff has no access to TB and XPI
    firefox_users = GROUPS["firefox-signoff"]
    tb_users = flatten([users for scope, users in AUTH0_AUTH_SCOPES.items() if "thunderbird" in scope])
    assert set(firefox_users).isdisjoint(set(tb_users))
    xpi_users = flatten([users for scope, users in AUTH0_AUTH_SCOPES.items() if "xpi_" in scope])
    assert set(firefox_users).isdisjoint(set(xpi_users))

    # thunderbird-signoff has no access to Firefox and XPI
    tb_users = GROUPS["thunderbird-signoff"]
    firefox_users = flatten(
        [users for scope, users in AUTH0_AUTH_SCOPES.items() if "firefox" in scope or "fenix" in scope or "fennec" in scope or "devedition" in scope]
    )
    assert set(firefox_users).isdisjoint(set(tb_users))

    xpi_users = (
        XPI_PRIVILEGED_BUILD_GROUP
        + XPI_PRIVILEGED_ADMIN_GROUP
        + XPI_SYSTEM_ADMIN_GROUP
        + XPI_MOZILLAONLINE_PRIVILEGED_GROUP
        + XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_GROUP
    )

    # XPI users have no access to Firefox and Thunderbird
    firefox_users = flatten(
        [users for scope, users in AUTH0_AUTH_SCOPES.items() if "firefox" in scope or "fenix" in scope or "fennec" in scope or "devedition" in scope]
    )
    assert set(firefox_users).isdisjoint(set(xpi_users))
    tb_users = flatten([users for scope, users in AUTH0_AUTH_SCOPES.items() if "thunderbird" in scope])
    assert set(xpi_users).isdisjoint(set(tb_users))

    # xpi_privileged_build has a limited set of scopes
    scopes = set([scope for scope, users in AUTH0_AUTH_SCOPES.items() if set(XPI_PRIVILEGED_BUILD_GROUP).issubset(set(users))])
    expected_scopes = set(
        [
            "project:releng:services/shipit_api/github",
            "project:releng:services/shipit_api/add_release/xpi/privileged",
            "project:releng:services/shipit_api/abandon_release/xpi/privileged",
            "project:releng:services/shipit_api/schedule_phase/xpi/privileged/build",
            "project:releng:services/shipit_api/phase_signoff/xpi/privileged/build",
        ]
    )

    assert scopes == expected_scopes
