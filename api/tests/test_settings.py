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


def _sort(dict_):
    return {key: sorted(value) for key, value in dict_.items()}


# Temporary (and dumb) test to ensure AUTH0_AUTH_SCOPES don't get altered in the refactor made in bug 1879094
def test_scopes_are_all_defined():
    from shipit_api.admin.settings import AUTH0_AUTH_SCOPES

    assert _sort(AUTH0_AUTH_SCOPES) == _sort(
        {
            "project:releng:services/shipit_api/abandon_release/app-services": [
                "shipit_app_services",
                "releng",
                "shipit_relman",
            ],
            "project:releng:services/shipit_api/abandon_release/devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/firefox-android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/mozilla-vpn-addons": [
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/mozilla-vpn-client": [
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/xpi/mozillaonline-privileged": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/xpi/normandy-privileged": [
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/xpi/privileged": [
                "xpi_privileged_build",
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/abandon_release/xpi/system": [
                "xpi_system_build",
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/app-services": [
                "shipit_app_services",
                "releng",
                "shipit_relman",
            ],
            "project:releng:services/shipit_api/add_release/devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/firefox-android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/mozilla-vpn-addons": [
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/mozilla-vpn-client": [
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/xpi/mozillaonline-privileged": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/xpi/normandy-privileged": [
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/xpi/privileged": [
                "xpi_privileged_build",
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/add_release/xpi/system": [
                "xpi_system_build",
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/disable_product/devedition": [
                "shipit_firefox",
                "shipit_relman",
                "releng",
            ],
            "project:releng:services/shipit_api/disable_product/firefox": [
                "shipit_firefox",
                "shipit_relman",
                "releng",
            ],
            "project:releng:services/shipit_api/disable_product/firefox-android": [
                "shipit_firefox",
                "shipit_relman",
                "releng",
            ],
            "project:releng:services/shipit_api/enable_product/devedition": [
                "shipit_firefox",
                "shipit_relman",
                "releng",
            ],
            "project:releng:services/shipit_api/enable_product/firefox": [
                "shipit_firefox",
                "shipit_relman",
                "releng",
            ],
            "project:releng:services/shipit_api/enable_product/firefox-android": [
                "shipit_firefox",
                "shipit_relman",
                "releng",
            ],
            "project:releng:services/shipit_api/github": [
                "xpi_system_build",
                "xpi_mozillaonline_build",
                "xpi_system_admin",
                "xpi_mozillaonline_admin",
                "releng",
                "shipit_app_services",
                "xpi_privileged_admin",
                "shipit_firefox",
                "shipit_relman",
                "xpi_privileged_build",
            ],
            "project:releng:services/shipit_api/phase_signoff/app-services/promote": [
                "shipit_app_services",
                "releng",
                "shipit_relman",
            ],
            "project:releng:services/shipit_api/phase_signoff/app-services/ship": [
                "shipit_app_services",
                "releng",
                "shipit_relman",
            ],
            "project:releng:services/shipit_api/phase_signoff/devedition/promote_devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/devedition/push_devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/devedition/ship_devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox-android/promote": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox-android/promote_android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox-android/push": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox-android/push_android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox-android/ship": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox-android/ship_android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox/promote_firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox/promote_firefox_rc": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox/push_firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox/ship_firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/firefox/ship_firefox_rc": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/mozilla-vpn-addons/promote-addons": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/mozilla-vpn-addons/ship-addons": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/mozilla-vpn-client/promote-client": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/mozilla-vpn-client/ship-client": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/thunderbird/promote_thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/thunderbird/push_thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/thunderbird/ship_thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/mozillaonline-privileged/build": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/mozillaonline-privileged/promote": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/mozillaonline-privileged/ship": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/normandy-privileged/build": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/normandy-privileged/promote": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/normandy-privileged/ship": [
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/privileged/build": [
                "xpi_privileged_build",
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/privileged/promote": [
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/privileged/ship": [
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/system/build": [
                "xpi_system_build",
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/system/promote": [
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/phase_signoff/xpi/system/ship": [
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/rebuild_product_details": [
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/app-services/promote": [
                "shipit_app_services",
                "releng",
                "shipit_relman",
            ],
            "project:releng:services/shipit_api/schedule_phase/app-services/ship": [
                "shipit_app_services",
                "releng",
                "shipit_relman",
            ],
            "project:releng:services/shipit_api/schedule_phase/devedition/promote_devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/devedition/push_devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/devedition/ship_devedition": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox-android/promote": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox-android/promote_android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox-android/push": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox-android/push_android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox-android/ship": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox-android/ship_android": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox/promote_firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox/promote_firefox_rc": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox/push_firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox/ship_firefox": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/firefox/ship_firefox_rc": [
                "shipit_relman",
                "shipit_firefox",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/mozilla-vpn-addons/promote-addons": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/mozilla-vpn-addons/ship-addons": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/mozilla-vpn-client/promote-client": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/mozilla-vpn-client/ship-client": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/thunderbird/promote_thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/thunderbird/push_thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/thunderbird/ship_thunderbird": [
                "shipit_thunderbird",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/mozillaonline-privileged/build": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/mozillaonline-privileged/promote": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/mozillaonline-privileged/ship": [
                "xpi_mozillaonline_build",
                "xpi_mozillaonline_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/normandy-privileged/build": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/normandy-privileged/promote": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/normandy-privileged/ship": [
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/privileged/build": [
                "xpi_privileged_build",
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/privileged/promote": [
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/privileged/ship": [
                "xpi_privileged_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/system/build": [
                "xpi_system_admin",
                "releng",
                "xpi_system_build",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/system/promote": [
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/schedule_phase/xpi/system/ship": [
                "xpi_system_admin",
                "releng",
            ],
            "project:releng:services/shipit_api/update_release_status": [
                "releng",
            ],
        }
    )
