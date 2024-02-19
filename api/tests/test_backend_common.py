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
