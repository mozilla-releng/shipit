import pytest

from shipit_api.admin import auth0


@pytest.mark.parametrize(
    "product_name, product_config, expected",
    (
        (
            "can-be-disabled-product",
            {"can-be-disabled": True, "repo-url": ""},
            [
                "add_release/can-be-disabled-product",
                "abandon_release/can-be-disabled-product",
                "add_merge_automation/can-be-disabled-product",
                "cancel_merge_automation/can-be-disabled-product",
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
                "add_merge_automation/product-on-github",
                "cancel_merge_automation/product-on-github",
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
                "add_merge_automation/firefox",
                "cancel_merge_automation/firefox",
                "schedule_phase/firefox/promote_firefox",
                "phase_signoff/firefox/promote_firefox",
                "schedule_phase/firefox/push_firefox",
                "phase_signoff/firefox/push_firefox",
                "schedule_phase/firefox/ship_firefox",
                "phase_signoff/firefox/ship_firefox",
                "schedule_phase/firefox/promote_firefox_rc",
                "phase_signoff/firefox/promote_firefox_rc",
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
    assert auth0._get_auth0_scopes(product_name, product_config) == expected
