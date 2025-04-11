import os


def flatten(lst):
    return [item for sublist in lst for item in sublist]


def test_scopes(monkeypatch):
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
        LDAP_GROUPS,
        XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_LDAP_GROUP,
        XPI_MOZILLAONLINE_PRIVILEGED_LDAP_GROUP,
        XPI_PRIVILEGED_ADMIN_LDAP_GROUP,
        XPI_PRIVILEGED_BUILD_LDAP_GROUP,
    )
    from shipit_api.common.config import SYSTEM_ADDONS

    # make sure the admin ldap group has all scopes
    assert all([set(LDAP_GROUPS["admin"]).issubset(entry) for entry in AUTH0_AUTH_SCOPES.values()])

    # github API, for XPI and Fenix ldap groups only
    github_ldap_groups = flatten(
        [ldap_groups for ldap_group, ldap_groups in LDAP_GROUPS.items() if ldap_group.startswith("xpi_") or ldap_group.startswith("fenix_")]
    )
    assert set(github_ldap_groups).issubset(set(AUTH0_AUTH_SCOPES["project:releng:services/shipit_api/github"]))

    # firefox-signoff has no access to TB and XPI
    firefox_ldap_groups = LDAP_GROUPS["firefox-signoff"]
    tb_ldap_groups = flatten([ldap_groups for scope, ldap_groups in AUTH0_AUTH_SCOPES.items() if "thunderbird" in scope])
    assert set(firefox_ldap_groups).isdisjoint(set(tb_ldap_groups))
    xpi_ldap_groups = flatten([ldap_groups for scope, ldap_groups in AUTH0_AUTH_SCOPES.items() if "xpi_" in scope])
    assert set(firefox_ldap_groups).isdisjoint(set(xpi_ldap_groups))

    # thunderbird-signoff has no access to Firefox and XPI
    tb_ldap_groups = LDAP_GROUPS["thunderbird-signoff"]
    firefox_ldap_groups = flatten(
        [
            ldap_groups
            for scope, ldap_groups in AUTH0_AUTH_SCOPES.items()
            if "firefox" in scope or "fenix" in scope or "fennec" in scope or "devedition" in scope
        ]
    )
    assert set(firefox_ldap_groups).isdisjoint(set(tb_ldap_groups))

    xpi_ldap_groups = (
        XPI_PRIVILEGED_BUILD_LDAP_GROUP
        + XPI_PRIVILEGED_ADMIN_LDAP_GROUP
        + XPI_MOZILLAONLINE_PRIVILEGED_LDAP_GROUP
        + XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_LDAP_GROUP
        + [f"shipit_system_addon_{addon}" for addon in SYSTEM_ADDONS]
    )

    # XPI ldap_groups have no access to Firefox and Thunderbird
    firefox_ldap_groups = flatten(
        [
            ldap_groups
            for scope, ldap_groups in AUTH0_AUTH_SCOPES.items()
            if "firefox" in scope or "fenix" in scope or "fennec" in scope or "devedition" in scope
        ]
    )
    assert set(firefox_ldap_groups).isdisjoint(set(xpi_ldap_groups))
    tb_ldap_groups = flatten([ldap_groups for scope, ldap_groups in AUTH0_AUTH_SCOPES.items() if "thunderbird" in scope])
    assert set(xpi_ldap_groups).isdisjoint(set(tb_ldap_groups))

    # xpi_privileged_build has a limited set of scopes
    scopes = set([scope for scope, ldap_groups in AUTH0_AUTH_SCOPES.items() if set(XPI_PRIVILEGED_BUILD_LDAP_GROUP).issubset(set(ldap_groups))])
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
