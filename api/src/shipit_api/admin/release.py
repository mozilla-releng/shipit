# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

import requests
from mozilla_version.fenix import FenixVersion  # TODO replace with MobileVersion
from mozilla_version.gecko import DeveditionVersion, FennecVersion, FirefoxVersion, ThunderbirdVersion
from mozilla_version.mobile import MobileVersion

from shipit_api.common.config import SUPPORTED_FLAVORS
from shipit_api.common.product import Product, get_key

logger = logging.getLogger(__name__)

_VERSION_CLASS_PER_PRODUCT = {
    Product.DEVEDITION: DeveditionVersion,
    Product.PINEBUILD: FirefoxVersion,
    Product.FENIX: FenixVersion,
    Product.FENNEC: FennecVersion,
    Product.FIREFOX: FirefoxVersion,
    Product.FIREFOX_ANDROID: MobileVersion,
    Product.FOCUS_ANDROID: MobileVersion,
    Product.THUNDERBIRD: ThunderbirdVersion,
}


def parse_version(product, version):
    if isinstance(product, Product):
        product_enum = product
    else:
        try:
            product_enum = Product[get_key(product)]
        except KeyError:
            raise ValueError(f"Product {product} versions are not supported")

    VersionClass = _VERSION_CLASS_PER_PRODUCT[product_enum]
    return VersionClass.parse(version)


def is_rc(product, version, partial_updates):
    gecko_version = parse_version(product, version)

    # Release candidates are only expected when the version number matches
    # the release pattern

    try:
        if not gecko_version.is_release or gecko_version.patch_number is not None:
            return False
    except AttributeError:
        # some versions (like MavenVersion) don't expose this attribute
        return False

    if SUPPORTED_FLAVORS.get(f"{product}_rc"):
        # could hard code "Thunderbird" condition here but
        # suspect it's better to use SUPPORTED_FLAVORS for a
        # configuration driven decision.
        return True

    # RC release types will enable beta-channel testing &
    # shipping. We need this for all "final" releases
    # and also any releases that include a beta as a partial.
    # The assumption that "shipping to beta channel" always
    # implies other RC behaviour is bound to break at some
    # point, but this works for now.
    if partial_updates:
        for partial_version in partial_updates:
            partial_gecko_version = parse_version(product, partial_version)
            if partial_gecko_version.is_beta:
                return True

    return False


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


def is_partner_enabled(product, version, min_version=60):
    if product == "firefox":
        firefox_version = FirefoxVersion.parse(version)
        return firefox_version.major_number >= min_version and any(
            (firefox_version.is_beta and firefox_version.beta_number >= 5, firefox_version.is_release, firefox_version.is_esr)
        )

    return False


def is_eme_free_enabled(product, version):
    if product == "firefox":
        firefox_version = FirefoxVersion.parse(version)
        return any((firefox_version.is_beta and firefox_version.beta_number >= 8, firefox_version.is_release))

    return False


def product_to_appname(product):
    """Convert product name to appName"""
    if product in [Product.FIREFOX.value, Product.DEVEDITION.value, Product.PINEBUILD.value]:
        return "browser"


def get_locales(repo, revision, appname):
    """Fetches list of locales from mercurial"""
    url = f"{repo}/raw-file/{revision}/{appname}/locales/l10n-changesets.json"
    req = requests.get(url, timeout=10)
    req.raise_for_status()
    return list(req.json().keys())
