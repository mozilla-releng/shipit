from deepmerge import merge_or_raise

from backend_common import get_products_config
from shipit_api.common.config import SUPPORTED_FLAVORS


def assign_ldap_groups_to_scopes():
    ldap_groups_per_scope = {}
    for product_name, product_config in get_products_config().items():
        if product_config["legacy"]:
            continue

        scopes = _get_auth0_scopes(product_name, product_config)
        new_ldap_groups_per_scope = {s: product_config["authorized-ldap-groups"] for s in scopes}
        ldap_groups_per_scope = merge_or_raise.merge(ldap_groups_per_scope, new_ldap_groups_per_scope)

    return ldap_groups_per_scope


def _get_auth0_scopes(product_name, product_config):
    scopes = [
        f"add_release/{product_name}",
        f"abandon_release/{product_name}",
        f"add_merge_automation/{product_name}",
        f"cancel_merge_automation/{product_name}",
    ]
    phases = [f["name"] for f in SUPPORTED_FLAVORS.get(product_name, [])]
    if product_name == "firefox":
        phases.extend([f["name"] for f in SUPPORTED_FLAVORS["firefox_rc"]])
    for phase in phases:
        scopes.extend([f"schedule_phase/{product_name}/{phase}", f"phase_signoff/{product_name}/{phase}"])

    if product_config["can-be-disabled"]:
        scopes.extend(
            [
                f"disable_product/{product_name}",
                f"enable_product/{product_name}",
            ]
        )

    if "github.com" in product_config["repo-url"]:
        scopes.extend(["github"])

    return scopes
