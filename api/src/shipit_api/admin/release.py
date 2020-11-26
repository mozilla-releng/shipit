# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
from mozilla_version.fenix import FenixVersion  # TODO Move FenixVersion into mozilla.gecko
from mozilla_version.gecko import DeveditionVersion, FennecVersion, FirefoxVersion, ThunderbirdVersion

from shipit_api.common.config import SUPPORTED_FLAVORS
from shipit_api.common.product import Product

_VERSION_CLASS_PER_PRODUCT = {
    Product.DEVEDITION: DeveditionVersion,
    Product.FENIX: FenixVersion,
    Product.FENNEC: FennecVersion,
    Product.FIREFOX: FirefoxVersion,
    Product.THUNDERBIRD: ThunderbirdVersion,
}


def parse_version(product, version):
    if isinstance(product, Product):
        product_enum = product
    else:
        try:
            product_enum = Product[product.upper()]
        except KeyError:
            raise ValueError(f"Product {product} versions are not supported")

    VersionClass = _VERSION_CLASS_PER_PRODUCT[product_enum]
    return VersionClass.parse(version)


def is_rc(product, version, partial_updates):
    gecko_version = parse_version(product, version)

    # Release candidates are only expected when the version number matches
    # the release pattern

    if not gecko_version.is_release or gecko_version.patch_number is not None:
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
    """Bump last digit"""
    gecko_version = parse_version(product, version)
    number_to_bump = "beta_number" if gecko_version.is_beta else "patch_number"
    bumped_version = gecko_version.bump(number_to_bump)
    return str(bumped_version)


def is_partner_enabled(product, version, min_version=60):
    if product == "firefox":
        firefox_version = FirefoxVersion.parse(version)
        return firefox_version.major_number >= min_version and any(
            (
                firefox_version.is_beta and firefox_version.beta_number >= 8,
                firefox_version.is_release,
                firefox_version.is_esr,
            )
        )

    return False


def is_eme_free_enabled(product, version):
    if product == "firefox":
        firefox_version = FirefoxVersion.parse(version)
        return any(
            (
                firefox_version.is_beta and firefox_version.beta_number >= 8,
                firefox_version.is_release,
            )
        )

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
