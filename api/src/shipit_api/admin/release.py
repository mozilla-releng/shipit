# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

import requests
from mozilla_version.gecko import FirefoxVersion

from shipit_api.common.product import Product
from shipit_api.common.version import parse_version

logger = logging.getLogger(__name__)


def bump_version(product, version):
    """Bump most sensible digit based on the current version type"""
    mozilla_version = parse_version(product, version)
    number_to_bump = "patch_number"

    for version_type in ("beta", "release_candidate"):
        try:
            if getattr(mozilla_version, f"is_{version_type}"):
                number_to_bump = f"{version_type}_number"
                break
        except AttributeError:
            # some versions (like MavenVersion) can never be betas and don't expose this attribute
            pass

    logging.debug(f'Bumping {number_to_bump} for version "{version}"')
    bumped_version = str(mozilla_version.bump(number_to_bump))
    logging.info(f'Version "{version}" is being bumped to "{bumped_version}"')

    return bumped_version


def is_partner_repacks_enabled(product, version, min_version=60):
    if product != "firefox":
        return False

    firefox_version = FirefoxVersion.parse(version)
    return firefox_version.major_number >= min_version and any(
        (firefox_version.is_beta and firefox_version.beta_number >= 5, firefox_version.is_release, firefox_version.is_esr)
    )


def is_partner_attribution_enabled(product, version, min_version=60):
    if product != "firefox":
        return False

    firefox_version = FirefoxVersion.parse(version)
    return is_partner_repacks_enabled(product, version, min_version) and not firefox_version.is_esr


def is_eme_free_enabled(product, version):
    if product == "firefox":
        firefox_version = FirefoxVersion.parse(version)
        return any((firefox_version.is_beta and firefox_version.beta_number >= 8, firefox_version.is_release))

    return False


def product_to_appname(product):
    """Convert product name to appName"""
    if product in [Product.FIREFOX.value, Product.DEVEDITION.value]:
        return "browser"


def get_locales(repo, revision, appname):
    """Fetches list of locales from mercurial"""
    url = f"{repo}/raw-file/{revision}/{appname}/locales/l10n-changesets.json"
    req = requests.get(url, timeout=10)
    req.raise_for_status()
    return list(req.json().keys())
