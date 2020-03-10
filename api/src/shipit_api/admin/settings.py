# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64

from decouple import config

from backend_common.auth import create_auth0_secrets_file
from shipit_api.common.config import SCOPE_PREFIX, SUPPORTED_FLAVORS

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
IRC_NOTIFICATIONS_OWNERS_PER_PRODUCT = config("IRC_NOTIFICATIONS_OWNERS_PER_PRODUCT", default=None)
IRC_NOTIFICATIONS_CHANNELS_PER_PRODUCT = config("IRC_NOTIFICATIONS_CHANNELS_PER_PRODUCT", default=None)
PRODUCT_DETAILS_GIT_REPO_URL = config("PRODUCT_DETAILS_GIT_REPO_URL", default=None)

if APP_CHANNEL not in supported_channels:
    raise ValueError(f"APP_CHANNEL should be one of {supported_channels}, `{APP_CHANNEL}` given")

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
GROUPS = {
    "admin": [
        "asasaki@mozilla.com",
        "bhearsum@mozilla.com",
        "catlee@mozilla.com",
        "jlorenzo@mozilla.com",
        "jlund@mozilla.com",
        "jwood@mozilla.com",
        "mtabara@mozilla.com",
        "nthomas@mozilla.com",
        "raliiev@mozilla.com",
        "sfraser@mozilla.com",
        "tprince@mozilla.com",
    ],
    "firefox-signoff": ["rkothari@mozilla.com", "ehenry@mozilla.com", "jcristau@mozilla.com", "pchevrel@mozilla.com", "rvandermeulen@mozilla.com"],
    "fenix-signoff": ["rkothari@mozilla.com", "ehenry@mozilla.com", "jcristau@mozilla.com", "pchevrel@mozilla.com", "rvandermeulen@mozilla.com"],
    "thunderbird-signoff": ["vseerror@lehigh.edu", "mozilla@jorgk.com", "thunderbird@calypsoblue.org"],
    # We use 2 separate groups for privileged and system addon type
    "xpi_privileged_signoff": ["rdalal@mozilla.com", "mcooper@mozilla.com"],
    "xpi_system_signoff": ["rdalal@mozilla.com", "mcooper@mozilla.com"],
}

AUTH0_AUTH_SCOPES = dict()

# releng signoff scopes
for product in ["firefox", "fenix", "fennec", "devedition"]:
    scopes = {f"add_release/{product}": GROUPS["firefox-signoff"], f"abandon_release/{product}": GROUPS["firefox-signoff"]}
    phases = []
    for flavor in [product, f"{product}_rc", f"{product}_release", f"{product}_release_rc", f"{product}_beta"]:
        phases += [i["name"] for i in SUPPORTED_FLAVORS.get(flavor, [])]
    for phase in set(phases):
        scopes.update({f"schedule_phase/{product}/{phase}": GROUPS["firefox-signoff"], f"phase_signoff/{product}/{phase}": GROUPS["firefox-signoff"]})
    AUTH0_AUTH_SCOPES.update(scopes)

# Add scopes for enabling/disabling products
AUTH0_AUTH_SCOPES.update(
    {
        "disable_product/firefox": GROUPS["firefox-signoff"],
        "disable_product/fennec": GROUPS["firefox-signoff"],
        "disable_product/devedition": GROUPS["firefox-signoff"],
        "enable_product/firefox": GROUPS["firefox-signoff"],
        "enable_product/fennec": GROUPS["firefox-signoff"],
        "enable_product/devedition": GROUPS["firefox-signoff"],
    }
)

# thunderbird signoff scopes
scopes = {"add_release/thunderbird": GROUPS["thunderbird-signoff"], "abandon_release/thunderbird": GROUPS["thunderbird-signoff"]}
phases = []
for flavor in ["thunderbird", "thunderbird_rc"]:
    phases += [i["name"] for i in SUPPORTED_FLAVORS.get(flavor, [])]
for phase in set(phases):
    scopes.update({f"schedule_phase/thunderbird/{phase}": GROUPS["thunderbird-signoff"], f"phase_signoff/thunderbird/{phase}": GROUPS["thunderbird-signoff"]})
AUTH0_AUTH_SCOPES.update(scopes)

# other scopes
AUTH0_AUTH_SCOPES.update({"rebuild_product_details": [], "update_release_status": []})

# Github scopes
# The following scope gives permission to all github queries, inlcuding private repos
AUTH0_AUTH_SCOPES.update({"github": GROUPS["fenix-signoff"] + GROUPS["xpi_privileged_signoff"] + GROUPS["xpi_system_signoff"]})

# XPI scopes
for xpi_type in ["privileged", "system"]:
    AUTH0_AUTH_SCOPES.update(
        {f"add_release/xpi/{xpi_type}": GROUPS[f"xpi_{xpi_type}_signoff"], f"abandon_release/xpi/{xpi_type}": GROUPS[f"xpi_{xpi_type}_signoff"]}
    )
    for phase in ["build", "promote"]:
        AUTH0_AUTH_SCOPES.update(
            {
                f"schedule_phase/xpi/{xpi_type}/{phase}": GROUPS[f"xpi_{xpi_type}_signoff"],
                f"phase_signoff/xpi/{xpi_type}/{phase}": GROUPS[f"xpi_{xpi_type}_signoff"],
            }
        )

# append scopes with scope prefix and add admin group of users
AUTH0_AUTH_SCOPES = {f"{SCOPE_PREFIX}/{scope}": list(set(users + GROUPS["admin"])) for scope, users in AUTH0_AUTH_SCOPES.items()}
