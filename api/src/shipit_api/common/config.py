# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pathlib
import re
import tempfile
from functools import cache, lru_cache

from decouple import config

from backend_common import get_products_config

PROJECT_NAME = "shipit/api"
APP_NAME = "shipit_api"
SCOPE_PREFIX = f"project:releng:services/{APP_NAME}"

# A route key that triggers rebuild of product details.
# Worker will listen to this route key to trigger the rebuild.
PULSE_ROUTE_REBUILD_PRODUCT_DETAILS = "rebuild_product_details"

# A folder where we will keep a checkout of product details
PRODUCT_DETAILS_DIR = pathlib.Path(tempfile.gettempdir(), "product-details")
PRODUCT_DETAILS_NEW_DIR = pathlib.Path(tempfile.gettempdir(), "product-details-new")
PRODUCT_DETAILS_CACHE_DIR = pathlib.Path(tempfile.gettempdir(), "product-details-cache")

# Use CURRENT_ESR-1. Releases with major version equal or less than the
# breakpoint version will be served using static files. No related
# product-details data will be generated if we decide to ship a dot release
# with major version <= BREAKPOINT_VERSION. This includes Firefox (release,
# esr, beta, devedition), and Thunderbird.
BREAKPOINT_VERSION = 114

# When there is only one ESR release ESR_NEXT is set to '' and ESR_CURRENT is
# set to current ESR major version.  When we have 2 ESR releases, ESR_CURRENT
# should be using the major version of the older release, while ESR_NEXT should
# be using the major version of the release with greater version.
CURRENT_ESR = "140"
ESR_NEXT = ""
# Pre Firefox version
LATEST_FIREFOX_OLDER_VERSION = "3.6.28"
# TODO: move the branch configs to secrets
RELEASE_BRANCH = "releases/mozilla-release"
BETA_BRANCH = "releases/mozilla-beta"
ESR_BRANCH_PREFIX = "releases/mozilla-esr"

# Aurora has been replaced by Dev Edition, but some 3rd party applications may
# still rely on this value.
FIREFOX_AURORA = ""

# IOS versions
IOS_BETA_VERSION = ""
IOS_VERSION = ""

# Thunderbird configs
LATEST_THUNDERBIRD_ALPHA_VERSION = "54.0a2"

THUNDERBIRD_RELEASE_BRANCH = "releases/comm-release"
THUNDERBIRD_BETA_BRANCH = "releases/comm-beta"
THUNDERBIRD_ESR_BRANCH_PREFIX = "releases/comm-esr"

# Mixed
HG_PREFIX = "https://hg.mozilla.org"

MOBILE_DETAILS_TEMPLATE = r"""
{
  "builds": [
        {
            "locale": {
                "code": "ar",
                "english": "Arabic",
                "native": "\u0639\u0631\u0628\u064a"
            }
        },
        {
            "locale": {
                "code": "be",
                "english": "Belarusian",
                "native": "\u0411\u0435\u043b\u0430\u0440\u0443\u0441\u043a\u0430\u044f"
            }
        },
        {
            "locale": {
                "code": "ca",
                "english": "Catalan",
                "native": "Catal\u00e0"
            }
        },
        {
            "locale": {
                "code": "cs",
                "english": "Czech",
                "native": "\u010ce\u0161tina"
            }
        },
        {
            "locale": {
                "code": "de",
                "english": "German",
                "native": "Deutsch"
            }
        },
        {
            "locale": {
                "code": "en-US",
                "english": "English (US)",
                "native": "English (US)"
            }
        },
        {
            "locale": {
                "code": "es-AR",
                "english": "Spanish (Argentina)",
                "native": "Espa\u00f1ol (de Argentina)"
            }
        },
        {
            "locale": {
                "code": "es-ES",
                "english": "Spanish (Spain)",
                "native": "Espa\u00f1ol (de Espa\u00f1a)"
            }
        },
        {
            "locale": {
                "code": "eu",
                "english": "Basque",
                "native": "Euskara"
            }
        },
        {
            "locale": {
                "code": "fa",
                "english": "Persian",
                "native": "\u0641\u0627\u0631\u0633\u06cc"
            }
        },
        {
            "locale": {
                "code": "fi",
                "english": "Finnish",
                "native": "suomi"
            }
        },
        {
            "locale": {
                "code": "fr",
                "english": "French",
                "native": "Fran\u00e7ais"
            }
        },
        {
            "locale": {
                "code": "fy-NL",
                "english": "Frisian",
                "native": "Frysk"
            }
        },
        {
            "locale": {
                "code": "ga-IE",
                "english": "Irish",
                "native": "Gaeilge"
            }
        },
        {
            "locale": {
                "code": "gl",
                "english": "Galician",
                "native": "Galego"
            }
        },
        {
            "locale": {
                "code": "hu",
                "english": "Hungarian",
                "native": "magyar"
            }
        },
        {
            "locale": {
                "code": "it",
                "english": "Italian",
                "native": "Italiano"
            }
        },
        {
            "locale": {
                "code": "ja",
                "english": "Japanese",
                "native": "\u65e5\u672c\u8a9e"
            }
        },
        {
            "locale": {
                "code": "lt",
                "english": "Lithuanian",
                "native": "lietuvi\u0173 kalba"
            }
        },
        {
            "locale": {
                "code": "nl",
                "english": "Dutch",
                "native": "Nederlands"
            }
        },
        {
            "locale": {
                "code": "pa-IN",
                "english": "Punjabi (India)",
                "native": "\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40 (\u0a2d\u0a3e\u0a30\u0a24)"
            }
        },
        {
            "locale": {
                "code": "pl",
                "english": "Polish",
                "native": "Polski"
            }
        },
        {
            "locale": {
                "code": "pt-BR",
                "english": "Portuguese (Brazilian)",
                "native": "Portugu\u00eas (do\u00a0Brasil)"
            }
        },
        {
            "locale": {
                "code": "pt-PT",
                "english": "Portuguese (Portugal)",
                "native": "Portugu\u00eas (Europeu)"
            }
        },
        {
            "locale": {
                "code": "ro",
                "english": "Romanian",
                "native": "Rom\u00e2n\u0103"
            }
        },
        {
            "locale": {
                "code": "ru",
                "english": "Russian",
                "native": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439"
            }
        },
        {
            "locale": {
                "code": "sk",
                "english": "Slovak",
                "native": "sloven\u010dina"
            }
        },
        {
            "locale": {
                "code": "tr",
                "english": "Turkish",
                "native": "T\u00fcrk\u00e7e"
            }
        },
        {
            "locale": {
                "code": "uk",
                "english": "Ukrainian",
                "native": "\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430"
            }
        },
        {
            "locale": {
                "code": "zh-CN",
                "english": "Chinese (Simplified)",
                "native": "\u4e2d\u6587 (\u7b80\u4f53)"
            }
        },
        {
            "locale": {
                "code": "zh-TW",
                "english": "Chinese (Traditional)",
                "native": "\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)"
            }
        }
    ],
    "beta_builds": [
        {
            "locale": {
                "code": "cs",
                "english": "Czech",
                "native": "\u010ce\u0161tina"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "de",
                "english": "German",
                "native": "Deutsch"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "en-US",
                "english": "English (US)",
                "native": "English (US)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "es-ES",
                "english": "Spanish (Spain)",
                "native": "Espa\u00f1ol (de Espa\u00f1a)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "fi",
                "english": "Finnish",
                "native": "suomi"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "fr",
                "english": "French",
                "native": "Fran\u00e7ais"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "it",
                "english": "Italian",
                "native": "Italiano"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "ja",
                "english": "Japanese",
                "native": "\u65e5\u672c\u8a9e"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "nl",
                "english": "Dutch",
                "native": "Nederlands"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "pl",
                "english": "Polish",
                "native": "Polski"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "pt-PT",
                "english": "Portuguese (Portugal)",
                "native": "Portugu\u00eas (Europeu)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "ru",
                "english": "Russian",
                "native": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        }
    ],
    "alpha_builds": [
        {
            "locale": {
                "code": "en-US",
                "english": "English (US)",
                "native": "English (US)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox"
            }
        }
    ]
}
"""


@cache
def _get_supported_flavors():
    products_config = get_products_config()

    supported_flavors_per_product = {}
    for product_name, product_config in products_config.items():
        phase_definitions = _get_phases_definitions(product_config["phases"])
        supported_flavors_per_product[product_name] = phase_definitions

    # We RCs are not a real product per se. That's why we special-case it here.
    supported_flavors_per_product["firefox_rc"] = [
        {"name": "promote_firefox_rc", "in_previous_graph_ids": True},
        {"name": "ship_firefox_rc", "in_previous_graph_ids": False},
        {"name": "push_firefox", "in_previous_graph_ids": True},
        {"name": "ship_firefox", "in_previous_graph_ids": True},
    ]

    return supported_flavors_per_product


def _get_phases_definitions(phases):
    return [
        {
            "name": phase,
            "in_previous_graph_ids": True,
        }
        for phase in phases
    ]


SUPPORTED_FLAVORS = _get_supported_flavors()

SYSTEM_ADDONS = (
    "data-leak-blocker",
    "newtab",
    "webcompat",
)

XPI_LAX_SIGN_OFF = config("XPI_LAX_SIGN_OFF", default=False, cast=bool)
SIGNOFFS = {
    "mozilla-vpn-client": {
        "ship-client": [
            {"name": "MozillaVPN Team", "description": "Ship mozilla-vpn-client", "permissions": "vpn-signoff"},
            {"name": "Release Engineering", "description": "Ship mozilla-vpn-client", "permissions": "admin"},
        ]
    },
    "mozilla-vpn-addons": {
        "ship-addons": [
            {"name": "MozillaVPN Team", "description": "Ship mozilla-vpn-client", "permissions": "vpn-signoff"},
            {"name": "Release Engineering", "description": "Ship mozilla-vpn-client", "permissions": "admin"},
        ]
    },
    "xpi": {
        "privileged": {
            "promote": [
                {"name": "Add-on Review Team", "description": "Promote XPI", "permissions": "xpi_privileged_admin_signoff"},
                {"name": "Privileged webextension admin", "description": "Promote XPI", "permissions": "xpi_privileged_signoff"},
            ],
            "ship": [
                {"name": "Privileged webextension admin", "description": "Ship XPI", "permissions": "xpi_privileged_signoff"},
            ],
        },
        "mozillaonline-privileged": {
            "promote": [
                {"name": "MozillaOnline privileged webextension team", "description": "Promote XPI", "permissions": "xpi_mozillaonline-privileged_signoff"},
                {
                    "name": "MozillaOnline privileged webextension admin",
                    "description": "Promote XPI",
                    "permissions": "xpi_mozillaonline-privileged_admin_signoff",
                },
            ],
            "ship": [
                {"name": "MozillaOnline privileged webextension team", "description": "Ship XPI", "permissions": "xpi_mozillaonline-privileged_signoff"},
                {
                    "name": "MozillaOnline privileged webextension admin",
                    "description": "Ship XPI",
                    "permissions": "xpi_mozillaonline-privileged_admin_signoff",
                },
            ],
        },
        "normandy-privileged": {
            "promote": [
                {"name": "Normandy privileged admin", "description": "Promote XPI", "permissions": "xpi_normandy-privileged_signoff"},
            ],
            "ship": [
                {"name": "Normandy privileged admin", "description": "Ship XPI", "permissions": "xpi_normandy-privileged_signoff"},
            ],
        },
    },
}

# System Addon signoffs
for addon in SYSTEM_ADDONS:
    SIGNOFFS["xpi"][f"system_{addon}"] = {
        "ship": [
            {"name": f"{addon.capitalize()} developer (#1)", "description": f"Ship {addon}", "permissions": f"system_addon_{addon}"},
            {"name": f"{addon.capitalize()} developer (#2)", "description": f"Ship {addon}", "permissions": f"system_addon_{addon}"},
        ],
    }


ALLOW_PHASE_SKIPPING = {
    "devedition": {
        "try": True,
        "beta": True,
    },
    "firefox": {
        "try": True,
        "beta": True,
    },
    "firefox-android": {
        "try": True,
        "beta": True,
    },
    "app-services": {
        "default": True,
    },
}


@lru_cache(maxsize=10)
def get_allowed_github_files(owner: str, repo: str) -> set[re.Pattern]:
    """Retrieve a set of compiled regexes that match allowed file paths."""
    allowed_paths = {
        r"taskcluster/config.yml",
        r"version.txt",
    }

    match (owner, repo):
        case ("mozilla-firefox", "firefox") | ("mozilla-releng", "staging-firefox"):
            allowed_paths.add(r"browser/extensions/[^/]+(?:/extension)?/manifest.json")
        case ("mozilla-extensions", _):
            allowed_paths.add(r"package.json")
        case ("mozilla-releng", "staging-xpi-public"):
            allowed_paths.add(r"one/package.json")

    return {re.compile(s) for s in allowed_paths}


# NOTE: This duplicates some configuration between the backend and the frontend (mainly the repo names).
# However, the frontend should never have half of the config it has in the first place and it should get moved at some point.
# See bug 1879910
_MERGE_BEHAVIORS_PER_PRODUCT = {
    "firefox": {
        "main-to-beta": {
            "pretty_name": "Main -> beta",
            "by-env": {
                "local": {
                    "always-target-tip": False,
                    "repo": "https://hg.mozilla.org/try",
                    "project": "try",
                    "version_path": "browser/config/version_display.txt",
                },
                "staging": {
                    "always-target-tip": False,
                    "repo": "https://hg.mozilla.org/try",
                    "project": "try",
                    "version_path": "browser/config/version_display.txt",
                },
                "production": {
                    "always-target-tip": True,
                    "repo": "https://hg.mozilla.org/mozilla-central",
                    "project": "mozilla-central",
                    "version_path": "browser/config/version_display.txt",
                },
            },
        },
        "beta-to-release": {
            "pretty_name": "Beta -> release",
            "by-env": {
                "local": {
                    "always-target-tip": True,
                    "repo": "https://hg.mozilla.org/releases/mozilla-beta",
                    "project": "mozilla-beta",
                    "version_path": "browser/config/version_display.txt",
                },
                "staging": {
                    "always-target-tip": False,
                    "repo": "https://hg.mozilla.org/try",
                    "project": "try",
                    "version_path": "browser/config/version_display.txt",
                },
                "production": {
                    "always-target-tip": True,
                    "repo": "https://hg.mozilla.org/releases/mozilla-beta",
                    "project": "mozilla-beta",
                    "version_path": "browser/config/version_display.txt",
                },
            },
        },
    }
}


def resolve_config_by_environment(config, environment):
    def _resolve(obj):
        if isinstance(obj, dict) and "by-env" in obj:
            env_mapping = obj["by-env"]
            env_value = env_mapping[environment]

            result = {k: _resolve(v) for k, v in obj.items() if k != "by-env"}
            if isinstance(env_value, dict):
                result.update(_resolve(env_value))
            else:
                return _resolve(env_value)
            return result

        if isinstance(obj, dict):
            return {k: _resolve(v) for k, v in obj.items()}
        return obj

    return _resolve(config)


MERGE_BEHAVIORS_PER_PRODUCT = resolve_config_by_environment(_MERGE_BEHAVIORS_PER_PRODUCT, os.environ.get("APP_CHANNEL", "local"))
