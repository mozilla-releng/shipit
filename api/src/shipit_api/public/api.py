# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
from collections import defaultdict

from flask import abort, current_app
from mozilla_version.fenix import FenixVersion
from mozilla_version.gecko import DeveditionVersion, FirefoxVersion, ThunderbirdVersion
from mozilla_version.mobile import MobileVersion
from werkzeug.exceptions import BadRequest

from shipit_api.common.models import DisabledProduct, Phase, Release, XPIRelease
from shipit_api.common.product import Product

logger = logging.getLogger(__name__)

VERSION_CLASSES = {
    Product.DEVEDITION.value: DeveditionVersion,
    # XXX revisit when we know how pinebuild will be versioned
    Product.PINEBUILD.value: FirefoxVersion,
    Product.FENIX.value: FenixVersion,
    Product.FIREFOX.value: FirefoxVersion,
    Product.FIREFOX_ANDROID.value: MobileVersion,
    Product.THUNDERBIRD.value: ThunderbirdVersion,
}


def good_version(release):
    """Can the version be parsed by mozilla_version

    Some ancient versions cannot be parsed by the mozilla_version module. This
    function helps to skip the versions that are not supported.
    Example versions that cannot be parsed:
    1.1, 1.1b1, 2.0.0.1
    """
    product = release["product"]
    if product not in VERSION_CLASSES:
        raise ValueError(f"Product {product} versions are not supported")
    try:
        VERSION_CLASSES[product].parse(release["version"])
        return True
    except ValueError:
        return False


def list_releases(product=None, branch=None, version=None, build_number=None, status=["scheduled"]):
    session = current_app.db.session
    releases = session.query(Release)
    if product:
        releases = releases.filter(Release.product == product)
    if branch:
        releases = releases.filter(Release.branch == branch)
    if version:
        releases = releases.filter(Release.version == version)
        if build_number:
            releases = releases.filter(Release.build_number == build_number)
    elif build_number:
        raise BadRequest(description="Filtering by build_number without version is not supported.")
    releases = releases.filter(Release.status.in_(status))
    releases = [r.json for r in releases.all()]
    # filter out not parsable releases, like 1.1, 1.1b1, etc
    releases = filter(good_version, releases)
    return _sort_releases_by_product_then_version(releases)


def _sort_releases_by_product_then_version(releases):
    # mozilla-version doesn't allow 2 version of 2 different products to be compared one another.
    # This function ensures mozilla-version is given only versions of the same product
    releases_by_product = {}
    for release in releases:
        releases_for_product = releases_by_product.setdefault(release["product"], [])
        releases_for_product.append(release)

    for product, releases in releases_by_product.items():
        releases_by_product[product] = sorted(releases, key=lambda r: VERSION_CLASSES[product].parse(r["version"]))

    return [release for product in sorted(releases_by_product.keys()) for release in releases_by_product[product]]


def get_release(name):
    session = current_app.db.session
    releases = list(filter(None, [session.query(product_model).filter(product_model.name == name).first() for product_model in (Release, XPIRelease)]))

    if not releases:
        abort(404, f"Release {name} not found")

    release = releases[0]
    return release.json


def get_phase(name, phase):
    session = current_app.db.session
    phase = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).first_or_404()
    return phase.json


def get_phase_signoff(name, phase):
    session = current_app.db.session
    phase = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).first_or_404()
    signoffs = [s.json for s in phase.signoffs]
    return dict(signoffs=signoffs)


def get_disabled_products():
    session = current_app.db.session
    ret = defaultdict(list)
    for row in session.query(DisabledProduct).all():
        ret[row.product].append(row.branch)
    return ret
