from contextlib import nullcontext as does_not_raise

import pytest

import backend_common


def test_set_products_config_default_values():
    products_config = {
        "all-default-values": {},
        "no-default-values": {
            "authorized-ldap-groups": ["admin_group", "product_group"],
            "can-be-disabled": True,
            "legacy": True,
            "phases": ["phase_1", "phase_2"],
            "repo-url": "https://github.com/some-org/some-repo",
        },
    }

    backend_common._set_products_config_default_values(products_config)
    assert products_config == {
        "all-default-values": {
            "authorized-ldap-groups": [],
            "can-be-disabled": False,
            "legacy": False,
            "phases": [],
            "repo-url": "",
        },
        "no-default-values": {
            "authorized-ldap-groups": ["admin_group", "product_group"],
            "can-be-disabled": True,
            "legacy": True,
            "phases": ["phase_1", "phase_2"],
            "repo-url": "https://github.com/some-org/some-repo",
        },
    }


@pytest.mark.parametrize(
    "products_config, expectation",
    (
        (
            {"mandatory-keys-provided": {"version-class": "some.version.Class"}},
            does_not_raise(),
        ),
        (
            {
                "missing-version-class": {},
            },
            pytest.raises(KeyError),
        ),
    ),
)
def test_check_mandatory_keys_are_provided(products_config, expectation):
    with expectation:
        backend_common._check_mandatory_keys_are_provided(products_config)
