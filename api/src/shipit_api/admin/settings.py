# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
from itertools import chain

from decouple import config

from backend_common.auth import create_auth0_secrets_file
from shipit_api.admin.auth0 import assign_ldap_groups_to_scopes
from shipit_api.common.config import SCOPE_PREFIX, SYSTEM_ADDONS, XPI_LAX_SIGN_OFF

# TODO: 1) rename "development" to "local" 2) remove "staging" when fully migrated
supported_channels = ["dev", "development", "staging", "production"]

# required
APP_CHANNEL = config("APP_CHANNEL")
TASKCLUSTER_ROOT_URL = config("TASKCLUSTER_ROOT_URL")
TASKCLUSTER_CLIENT_ID = config("TASKCLUSTER_CLIENT_ID")
TASKCLUSTER_ACCESS_TOKEN = config("TASKCLUSTER_ACCESS_TOKEN")
AUTH_DOMAIN = config("AUTH_DOMAIN")
AUTH_CLIENT_ID = config("AUTH_CLIENT_ID")
AUTH_CLIENT_SECRET = config("AUTH_CLIENT_SECRET")
SQLALCHEMY_DATABASE_URI = config("DATABASE_URL")
SECRET_KEY = config("SECRET_KEY_BASE64", cast=base64.b64decode)

# optional
GITHUB_TOKEN = config("GITHUB_TOKEN", default=None)
XPI_MANIFEST_OWNER = config("XPI_MANIFEST_OWNER", default=None)
XPI_MANIFEST_REPO = config("XPI_MANIFEST_REPO", default=None)
GITHUB_SKIP_PRIVATE_REPOS = config("GITHUB_SKIP_PRIVATE_REPOS", default=False, cast=bool)
PULSE_USER = config("PULSE_USER", default=None)
PULSE_PASSWORD = config("PULSE_PASSWORD", default=None)
PULSE_USE_SSL = config("PULSE_USE_SSL", default=True, cast=bool)
PULSE_CONNECTION_TIMEOUT = config("PULSE_CONNECTION_TIMEOUT", default=5, cast=int)
PULSE_HOST = config("PULSE_HOST", default="pulse.mozilla.org")
PULSE_PORT = config("PULSE_PORT", default=5671, cast=int)
PULSE_VIRTUAL_HOST = config("PULSE_VIRTUAL_HOST", default="/")
SENTRY_DSN = config("SENTRY_DSN", default=None)
CORS_ORIGINS = config("CORS_ORIGINS", default=None)
PRODUCT_DETAILS_GIT_REPO_URL = config("PRODUCT_DETAILS_GIT_REPO_URL", default=None)

if APP_CHANNEL not in supported_channels:
    raise ValueError(f"APP_CHANNEL should be one of {supported_channels}, `{APP_CHANNEL}` given")

if XPI_LAX_SIGN_OFF and APP_CHANNEL == "production":
    raise ValueError("XPI_LAX_SIGN_OFF cannot be enabled when the APP_CHANNEL is production!")

# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_TRACK_MODIFICATIONS = False
# Use pessimistic disconnect handling as described at
# https://docs.sqlalchemy.org/en/13/core/pooling.html#disconnect-handling-pessimistic
# In some edge cases, when GCP performs maintenance on the database, the
# connection goes away, but sqlalchemy doesn't detect it.
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

# -- AUTH --------------------------------------------------------------------

OIDC_USER_INFO_ENABLED = True
OIDC_CLIENT_SECRETS = create_auth0_secrets_file(AUTH_CLIENT_ID, AUTH_CLIENT_SECRET, AUTH_DOMAIN)

# XXX: scopes/groups are hardcoded for now
ADMIN_LDAP_GROUP = ["releng"]

# Please ping awagner before making changes to this group
XPI_PRIVILEGED_BUILD_LDAP_GROUP = ["xpi_privileged_build"]

XPI_PRIVILEGED_ADMIN_LDAP_GROUP = ["xpi_privileged_admin"]
XPI_MOZILLAONLINE_PRIVILEGED_LDAP_GROUP = ["xpi_mozillaonline_build"]
XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_LDAP_GROUP = ["xpi_mozillaonline_admin"]

LDAP_GROUPS = {
    "admin": ADMIN_LDAP_GROUP,
    "relman": ["shipit_relman"],
    "firefox-signoff": ["shipit_firefox"],
    "thunderbird-signoff": ["shipit_thunderbird"],
    "firefox-android-signoff": ["shipit_mobile"],
    "firefox-ios-signoff": ["shipit_mobile"],
    "app-services-signoff": ["shipit_app_services"],
    "vpn-signoff": ["shipit_mozillavpn"],
    # XPI signoffs. These are in flux.
    # Adding Releng as a backup to most of these, for bus factor. Releng should
    # only sign off if requested by someone in the appropriate group.
    # ADMIN_GROUP has to be added in order for multiple signoffs to work
    "xpi_privileged_build": XPI_PRIVILEGED_BUILD_LDAP_GROUP + ADMIN_LDAP_GROUP,
    "xpi_privileged_signoff": XPI_PRIVILEGED_ADMIN_LDAP_GROUP + ADMIN_LDAP_GROUP,
    "xpi_privileged_admin_signoff": XPI_PRIVILEGED_ADMIN_LDAP_GROUP,
    "xpi_mozillaonline-privileged_signoff": XPI_MOZILLAONLINE_PRIVILEGED_LDAP_GROUP + ADMIN_LDAP_GROUP,
    "xpi_mozillaonline-privileged_admin_signoff": XPI_MOZILLAONLINE_PRIVILEGED_ADMIN_LDAP_GROUP + ADMIN_LDAP_GROUP,
    "xpi_normandy-privileged_signoff": ADMIN_LDAP_GROUP,
}
for addon in SYSTEM_ADDONS:
    LDAP_GROUPS[f"system_addon_{addon}"] = [f"shipit_system_addon_{addon}"] + ADMIN_LDAP_GROUP


AUTH0_AUTH_SCOPES = assign_ldap_groups_to_scopes()

# other scopes
AUTH0_AUTH_SCOPES.update(
    {
        "rebuild_product_details": LDAP_GROUPS["firefox-signoff"],
        "update_release_status": [],
        "create_product_channel_version/firefox": [],
        "create_product_channel_version/thunderbird": [],
    }
)

# Github scopes
# The following scope gives permission to all github queries, including private repos
AUTH0_AUTH_SCOPES.setdefault("github", []).extend(
    list(
        set(
            LDAP_GROUPS["xpi_privileged_build"]
            + LDAP_GROUPS["xpi_privileged_signoff"]
            + LDAP_GROUPS["xpi_mozillaonline-privileged_signoff"]
            + LDAP_GROUPS["xpi_mozillaonline-privileged_admin_signoff"]
            + LDAP_GROUPS["xpi_normandy-privileged_signoff"]
        )
    )
    + list(chain(*[LDAP_GROUPS[f"system_addon_{addon}"] for addon in SYSTEM_ADDONS]))
)

# XPI scopes
for xpi_type in ["privileged", "mozillaonline-privileged", "normandy-privileged"]:
    # "build", "signoff", and "admin_signoff" groups can create and cancel releases
    AUTH0_AUTH_SCOPES.update(
        {
            f"add_release/xpi/{xpi_type}": LDAP_GROUPS.get(f"xpi_{xpi_type}_build", [])
            + LDAP_GROUPS[f"xpi_{xpi_type}_signoff"]
            + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
            f"abandon_release/xpi/{xpi_type}": LDAP_GROUPS.get(f"xpi_{xpi_type}_build", [])
            + LDAP_GROUPS[f"xpi_{xpi_type}_signoff"]
            + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
        }
    )
    # "build", "signoff", and "admin_signoff" groups can schedule the "build" phase
    AUTH0_AUTH_SCOPES.update(
        {
            f"schedule_phase/xpi/{xpi_type}/build": LDAP_GROUPS.get(f"xpi_{xpi_type}_build", [])
            + LDAP_GROUPS[f"xpi_{xpi_type}_signoff"]
            + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
            f"phase_signoff/xpi/{xpi_type}/build": LDAP_GROUPS.get(f"xpi_{xpi_type}_build", [])
            + LDAP_GROUPS[f"xpi_{xpi_type}_signoff"]
            + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
        }
    )
    # Only "signoff", and "admin_signoff" groups can schedule the "promote" phase
    AUTH0_AUTH_SCOPES.update(
        {
            f"schedule_phase/xpi/{xpi_type}/promote": LDAP_GROUPS[f"xpi_{xpi_type}_signoff"] + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
            f"phase_signoff/xpi/{xpi_type}/promote": LDAP_GROUPS[f"xpi_{xpi_type}_signoff"] + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
        }
    )
    # Only "signoff", and "admin_signoff" groups can schedule the "ship" phase
    AUTH0_AUTH_SCOPES.update(
        {
            f"schedule_phase/xpi/{xpi_type}/ship": LDAP_GROUPS[f"xpi_{xpi_type}_signoff"] + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
            f"phase_signoff/xpi/{xpi_type}/ship": LDAP_GROUPS[f"xpi_{xpi_type}_signoff"] + LDAP_GROUPS.get(f"xpi_{xpi_type}_admin_signoff", []),
        }
    )

# XPI System Addons
for addon in SYSTEM_ADDONS:
    # We grant the system addon specific LDAP group the ability to manage and
    # signoff on all phases of the release. This is acceptable because System
    # Addons don't ship to users until Balrog rules are set up manually.
    # Additional signoffs are setup in Balrog.
    addon_ldap_group = LDAP_GROUPS[f"system_addon_{addon}"]
    AUTH0_AUTH_SCOPES.update(
        {
            f"add_release/xpi/system_{addon}": addon_ldap_group,
            f"abandon_release/xpi/system_{addon}": addon_ldap_group,
            f"schedule_phase/xpi/system_{addon}/build": addon_ldap_group,
            f"phase_signoff/xpi/system_{addon}/build": addon_ldap_group,
            f"schedule_phase/xpi/system_{addon}/promote": addon_ldap_group,
            f"phase_signoff/xpi/system_{addon}/promote": addon_ldap_group,
            f"schedule_phase/xpi/system_{addon}/ship": addon_ldap_group,
            f"phase_signoff/xpi/system_{addon}/ship": addon_ldap_group,
        }
    )

# append scopes with scope prefix and add admin group of ldap_groups
AUTH0_AUTH_SCOPES = {f"{SCOPE_PREFIX}/{scope}": list(set(ldap_groups + LDAP_GROUPS["admin"])) for scope, ldap_groups in AUTH0_AUTH_SCOPES.items()}

# fmt: off
if APP_CHANNEL == "production":
    MATRIX_NOTIFICATIONS_OWNERS_PER_PRODUCT = {
        "thunderbird": ["rjl", "wsmwk", "dandarnell"],
        "default": ["sheriffduty", "ciduty", "releaseduty"]
    }
    MATRIX_NOTIFICATIONS_ROOMS_PER_PRODUCT = {
        "thunderbird": [
            "!xPTYfLywxFMryjbnJl:mozilla.org",  # #tbdrivers:mozilla.org
        ],
        "default": [
            "!tBWwNyfeKqGvkNpdDL:mozilla.org",  # #releaseduty:mozilla.org
        ],
    }
elif APP_CHANNEL == "dev":
    MATRIX_NOTIFICATIONS_OWNERS_PER_PRODUCT = {"default": ["here"]}
    MATRIX_NOTIFICATIONS_ROOMS_PER_PRODUCT = {
        "default": [
            "!wGgsWXnVncJLSBYmuf:mozilla.org",  # #releaseduty-dev:mozilla.org
        ],
    }

# fmt: on
