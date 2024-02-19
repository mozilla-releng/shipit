from contextlib import nullcontext as does_not_raise

import pytest

import backend_common


def test_build_api_specification(monkeypatch):
    def mock_get_specifications_from_openapi_yaml_files(_):
        return {
            "components": {
                "schemas": {
                    "ProductInput": {},
                    "ProductOutput": {},
                },
            },
        }

    monkeypatch.setattr(backend_common, "_get_specifications_from_openapi_yaml_files", mock_get_specifications_from_openapi_yaml_files)

    def mock_get_product_names(include_legacy=False):
        return ["legacy-product", "current-product"] if include_legacy else ["current-product"]

    monkeypatch.setattr(backend_common, "get_product_names", mock_get_product_names)

    assert backend_common.build_api_specification("dummy_root_path") == {
        "components": {
            "schemas": {
                "ProductInput": {
                    "enum": ["current-product"],
                },
                "ProductOutput": {
                    "enum": ["legacy-product", "current-product"],
                },
            },
        },
    }


@pytest.mark.parametrize("include_legacy, expected", ((True, ["legacy-product", "current-product"]), (False, ["current-product"])))
def test_get_product_names(monkeypatch, include_legacy, expected):
    def mock_get_products_config():
        return {
            "legacy-product": {"legacy": True},
            "current-product": {"legacy": False},
        }

    monkeypatch.setattr(backend_common, "get_products_config", mock_get_products_config)

    assert backend_common.get_product_names(include_legacy) == expected


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
