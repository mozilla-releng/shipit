# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import os

from backend_common.auth import create_auth0_secrets_file
from cli_common.taskcluster import get_secrets
from shipit_api.common.config import PROJECT_NAME, SCOPE_PREFIX, SUPPORTED_FLAVORS

# -- LOAD SECRETS -------------------------------------------------------------

required = [
    "APP_CHANNEL",
    "AUTH_DOMAIN",
    "AUTH_CLIENT_ID",
    "AUTH_CLIENT_SECRET",
    "DATABASE_URL",
    "SECRET_KEY_BASE64",
]
optional = ["DISABLE_NOTIFY", "GITHUB_TOKEN", "XPI_MANIFEST_OWNER", "XPI_MANIFEST_REPO", "GITHUB_SKIP_PRIVATE_REPOS"]

# In local development, these come directly from the environment.
if os.environ.get("APP_CHANNEL") == "development":
    secrets = {k: os.environ[k] for k in required}
    secrets.update({k: os.environ[k] for k in optional if k in os.environ})
# For deployed environments, they come from Taskcluster.
else:
    secrets = get_secrets(
        os.environ.get("TASKCLUSTER_SECRET"),
        PROJECT_NAME,
        required=required,
        existing={x: os.environ.get(x) for x in required if x in os.environ},
        taskcluster_client_id=os.environ.get("TASKCLUSTER_CLIENT_ID"),
        taskcluster_access_token=os.environ.get("TASKCLUSTER_ACCESS_TOKEN"),
    )

locals().update(secrets)

SECRET_KEY = base64.b64decode(secrets["SECRET_KEY_BASE64"])

# -- PULSE -----------------------------------------------------------------

if "PULSE_PASSWORD" in os.environ:
    PULSE_PASSWORD = os.environ["PULSE_PASSWORD"]

if "PULSE_USER" in os.environ:
    PULSE_USER = os.environ["PULSE_USER"]

# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_TRACK_MODIFICATIONS = False
# Use pessimistic disconnect handling as described at
# https://docs.sqlalchemy.org/en/13/core/pooling.html#disconnect-handling-pessimistic
# In some edge cases, when GCP performs maintenance on the database, the
# connection goes away, but sqlalchemy doesn't detect it.
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
SQLALCHEMY_DATABASE_URI = secrets["DATABASE_URL"]

# -- AUTH --------------------------------------------------------------------

OIDC_USER_INFO_ENABLED = True
OIDC_CLIENT_SECRETS = create_auth0_secrets_file(secrets["AUTH_CLIENT_ID"], secrets["AUTH_CLIENT_SECRET"], secrets["AUTH_DOMAIN"])

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
    "xpi_privileged_signoff": ["rdalal@mozilla.com"],
    "xpi_system_signoff": ["rdalal@mozilla.com"],
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
AUTH0_AUTH = True
TASKCLUSTER_AUTH = True
