import os

import pytest

from shipit_api import admin


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
        XPI_SYSTEM_ADMIN_LDAP_GROUP,
    )

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
        + XPI_SYSTEM_ADMIN_LDAP_GROUP
        + XPI_MOZILLAONLINE_PRIVILEGED_LDAP_GROUP
        + XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_LDAP_GROUP
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


@pytest.mark.parametrize(
    "product_name, product_config, expected",
    (
        (
            "can-be-disabled-product",
            {"can-be-disabled": True, "repo-url": ""},
            [
                "add_release/can-be-disabled-product",
                "abandon_release/can-be-disabled-product",
                "disable_product/can-be-disabled-product",
                "enable_product/can-be-disabled-product",
            ],
        ),
        (
            "product-on-github",
            {"can-be-disabled": False, "repo-url": "https://github.com/some-org/product-on-github"},
            [
                "add_release/product-on-github",
                "abandon_release/product-on-github",
                "github",
            ],
        ),
        (
            "firefox",  # Must include rc phases
            {
                "can-be-disabled": True,
                "authorized-ldap-groups": [
                    "shipit_firefox",
                    "shipit_relman",
                ],
                "phases": [
                    "promote_firefox",
                    "push_firefox",
                    "ship_firefox",
                ],
                "firefox-ci-trust-domain": "gecko",
                "repo-url": "",
                "version-class": "mozilla_version.gecko.GeckoVersion",
            },
            [
                "add_release/firefox",
                "abandon_release/firefox",
                "schedule_phase/firefox/promote_firefox",
                "phase_signoff/firefox/promote_firefox",
                "schedule_phase/firefox/push_firefox",
                "phase_signoff/firefox/push_firefox",
                "schedule_phase/firefox/ship_firefox",
                "phase_signoff/firefox/ship_firefox",
                "schedule_phase/firefox/promote_firefox_rc",
                "phase_signoff/firefox/promote_firefox_rc",
                "schedule_phase/firefox/ship_firefox_rc",
                "phase_signoff/firefox/ship_firefox_rc",
                "schedule_phase/firefox/push_firefox",
                "phase_signoff/firefox/push_firefox",
                "schedule_phase/firefox/ship_firefox",
                "phase_signoff/firefox/ship_firefox",
                "disable_product/firefox",
                "enable_product/firefox",
            ],
        ),
    ),
)
def test_get_auth0_scopes(product_name, product_config, expected):
    assert admin.settings._get_auth0_scopes(product_name, product_config) == expected
