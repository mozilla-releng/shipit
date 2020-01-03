# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import os

import backend_common.auth
import cli_common.taskcluster
import shipit_api.config

DEBUG = bool(os.environ.get("DEBUG", False))

# -- LOAD SECRETS -------------------------------------------------------------

required = [
    "APP_CHANNEL",
    # Unused, but required by flask-oidc
    "APP_URL",
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
    secrets = cli_common.taskcluster.get_secrets(
        os.environ.get("TASKCLUSTER_SECRET"),
        shipit_api.config.PROJECT_NAME,
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

if DEBUG:
    SQLALCHEMY_ECHO = True

# We require DATABASE_URL set by environment variables for branches deployed to Dockerflow.
if secrets["APP_CHANNEL"] in ("testing", "staging", "production"):
    if "DATABASE_URL" not in os.environ:
        raise RuntimeError(f"DATABASE_URL has to be set as an environment variable, when " f'APP_CHANNEL is set to {secrets["APP_CHANNEL"]}')
    else:
        SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
else:
    SQLALCHEMY_DATABASE_URI = secrets["DATABASE_URL"]

# -- AUTH --------------------------------------------------------------------

OIDC_USER_INFO_ENABLED = True
args = [secrets["AUTH_CLIENT_ID"], secrets["AUTH_CLIENT_SECRET"], secrets["APP_URL"]]
OIDC_CLIENT_SECRETS = backend_common.auth.create_auth0_secrets_file(*args)

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
    "thunderbird-signoff": ["vseerror@lehigh.edu", "mozilla@jorgk.com", "thunderbird@calypsoblue.org"],
    # We use 2 separate groups for standard and system addon type
    "xpi_standard_signoff": ["rdalal@mozilla.com"],
    "xpi_system_signoff": ["rdalal@mozilla.com"],
}

AUTH0_AUTH_SCOPES = dict()

# releng signoff scopes
for product in ["firefox", "fennec", "devedition"]:
    scopes = {f"add_release/{product}": GROUPS["firefox-signoff"], f"abandon_release/{product}": GROUPS["firefox-signoff"]}
    phases = []
    for flavor in [product, f"{product}_rc", f"{product}_release", f"{product}_release_rc", f"{product}_beta"]:
        phases += [i["name"] for i in shipit_api.config.SUPPORTED_FLAVORS.get(flavor, [])]
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
    phases += [i["name"] for i in shipit_api.config.SUPPORTED_FLAVORS.get(flavor, [])]
for phase in set(phases):
    scopes.update({f"schedule_phase/thunderbird/{phase}": GROUPS["thunderbird-signoff"], f"phase_signoff/thunderbird/{phase}": GROUPS["thunderbird-signoff"]})
AUTH0_AUTH_SCOPES.update(scopes)

# other scopes
AUTH0_AUTH_SCOPES.update({"rebuild_product_details": [], "update_release_status": []})

# XPI scopes
# The following scope gives permission to all github queries, inlcuding private repos
AUTH0_AUTH_SCOPES.update({"github": GROUPS["xpi_standard_signoff"] + GROUPS["xpi_system_signoff"]})

for xpi_type in ["standard", "system"]:
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
AUTH0_AUTH_SCOPES = {f"{shipit_api.config.SCOPE_PREFIX}/{scope}": list(set(users + GROUPS["admin"])) for scope, users in AUTH0_AUTH_SCOPES.items()}
AUTH0_AUTH = True
TASKCLUSTER_AUTH = True
