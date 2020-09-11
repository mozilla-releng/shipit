# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

import requests

from shipit_api.common.config import SUPPORTED_FLAVORS
from shipit_api.common.product import Product

# If version has two parts with no trailing specifiers like "rc", we
# consider it a 'final' release for which we only create a _RELEASE tag.
FINAL_RELEASE_REGEX = r"^\d+\.\d+$"


# TODO: Reland https://github.com/mozilla/release-services/pull/2262. It was backed out because of
# https://github.com/mozilla/release-services/pull/2265#issue-317003960
VERSION_REGEX = re.compile(
    r"^"
    r"(?P<major_minor>[0-9]+\.[0-9]+)"  # Major and minor version
    r"(?:"  # Patch or beta version is optional
    r"(?P<point>[.ba])"  # Separator from patch or beta version
    r"(?P<patch>[0-9]+)"  # Patch or beta version
    r")?"
    r"(?P<esr>(?:esr)?)"  # ESR indicator
    r"(-beta\.(?P<semver_beta>[0-9]+))?"  # Semver beta number (used in Fenix)
    r"$"
)


def parse_version(version):
    match = VERSION_REGEX.match(version)
    if not match:
        raise Exception("Unknown version format.")
    return match.groupdict()


def is_final_release(version):
    return bool(re.match(FINAL_RELEASE_REGEX, version))


def is_beta(version):
    return parse_version(version)["point"] == "b"


def is_esr(version):
    return parse_version(version)["esr"] == "esr"


def is_rc(product, version, partial_updates):
    if not is_beta(version) and not is_esr(version):
        if is_final_release(version):
            # version supports rc flavor
            # now validate that the product itself supports rc flavor
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
            for version in partial_updates:
                if is_beta(version):
                    return True
    return False


def bump_version(version):
    """Bump last digit"""
    parts = parse_version(version)
    if parts["patch"]:
        parts["patch"] = int(parts["patch"]) + 1
    else:
        parts["patch"] = 1
    if not parts["point"]:
        parts["point"] = "."
    return f'{parts["major_minor"]}{parts["point"]}{parts["patch"]}{parts["esr"]}'


def get_beta_num(version):
    if is_beta(version):
        parts = version.split("b")
        return int(parts[-1])


def is_partner_enabled(product, version, min_version=60):
    major_version = int(version.split(".")[0])
    if product == "firefox" and major_version >= min_version:
        if is_beta(version):
            if get_beta_num(version) >= 5:
                return True
        elif is_esr(version):
            return True
        else:
            return True
    return False


def is_eme_free_enabled(product, version):
    if product == "firefox":
        if is_beta(version):
            if get_beta_num(version) >= 8:
                return True
        elif not is_esr(version):
            return True
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
