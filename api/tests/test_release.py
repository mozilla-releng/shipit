# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import nullcontext as does_not_raise

import pytest
from mozilla_version.fenix import FenixVersion
from mozilla_version.gecko import DeveditionVersion, FennecVersion, FirefoxVersion, ThunderbirdVersion
from mozilla_version.mobile import MobileVersion

from shipit_api.admin.api import get_signoff_emails
from shipit_api.admin.release import bump_version, is_eme_free_enabled, is_partner_enabled, is_rc, parse_version
from shipit_api.common.models import XPISignoff
from shipit_api.common.product import Product


@pytest.mark.parametrize(
    "product, version, expectation, result",
    (
        ("devedition", "56.0b1", does_not_raise(), DeveditionVersion(56, 0, beta_number=1)),
        (Product.DEVEDITION, "56.0b1", does_not_raise(), DeveditionVersion(56, 0, beta_number=1)),
        ("pinebuild", "56.0b1", does_not_raise(), FirefoxVersion(56, 0, beta_number=1)),
        (Product.PINEBUILD, "56.0b1", does_not_raise(), FirefoxVersion(56, 0, beta_number=1)),
        ("fenix", "84.0.0-beta.2", does_not_raise(), FenixVersion(84, 0, 0, beta_number=2)),
        (Product.FENIX, "84.0.0", does_not_raise(), FenixVersion(84, 0, 0)),
        ("fennec", "68.2b3", does_not_raise(), FennecVersion(68, 2, beta_number=3)),
        (Product.FENNEC, "68.2b3", does_not_raise(), FennecVersion(68, 2, beta_number=3)),
        ("firefox", "45.0", does_not_raise(), FirefoxVersion(45, 0)),
        (Product.FIREFOX, "45.0", does_not_raise(), FirefoxVersion(45, 0)),
        ("thunderbird", "60.8.0", does_not_raise(), ThunderbirdVersion(60, 8, 0)),
        (Product.THUNDERBIRD, "60.8.0", does_not_raise(), ThunderbirdVersion(60, 8, 0)),
        ("non-existing-product", "68.0", pytest.raises(ValueError), None),
        # fennec_release used to be a valid value when we moved Fennec to ESR68
        # https://github.com/mozilla/release-services/pull/2265
        # Let's be explicitly failing about it.
        ("fennec_release", "68.1.1", pytest.raises(ValueError), None),
        (Product.FOCUS_ANDROID, "95.0.1", does_not_raise(), MobileVersion(95, 0, 1)),
    ),
)
def test_parse_version(product, version, expectation, result):
    with expectation:
        assert parse_version(product, version) == result


@pytest.mark.parametrize(
    "product, version, partial_updates, result",
    (
        ("firefox", "64.0", None, True),
        ("thunderbird", "64.0", None, False),
        ("fennec", "64.0", None, False),  # "fennec_rc" does not exist anymore
        ("firefox", "64.0.1", None, False),
        ("thunderbird", "64.0.1", None, False),
        ("fennec", "64.0.1", None, False),
        ("firefox", "56.0b3", None, False),
        ("fennec", "56.0b3", None, False),
        ("firefox", "45.0esr", None, False),
        ("firefox", "57.0", {"56.0b1": [], "55.0": []}, True),
        ("firefox", "57.0", {"56.0": [], "55.0": []}, True),
        ("firefox", "57.0.1", {"57.0": [], "56.0.1": [], "56.0": []}, False),
        ("thunderbird", "57.0", {"56.0": [], "55.0": []}, False),
        ("thunderbird", "57.0", {"56.0": [], "56.0b4": [], "55.0": []}, True),
        ("firefox", "70.0b4", {"69.0b15": [], "69.0b16": [], "70.0b3": []}, False),
        ("devedition", "70.0b4", {"70.0b3": [], "70.0b1": [], "70.0b2": []}, False),
        ("pinebuild", "70.0b4", {"70.0b3": [], "70.0b1": [], "70.0b2": []}, False),
    ),
)
def test_is_rc(product, version, partial_updates, result):
    assert is_rc(product, version, partial_updates) == result


@pytest.mark.parametrize(
    "product, version, result",
    (
        ("firefox", "45.0", "45.0.1"),
        ("firefox", "45.0.1", "45.0.2"),
        ("firefox", "45.0b3", "45.0b4"),
        ("firefox", "45.0esr", "45.0.1esr"),
        ("firefox", "45.0.1esr", "45.0.2esr"),
        ("firefox", "45.2.1esr", "45.2.2esr"),
        ("fennec", "68.1b2", "68.1b3"),
        ("fenix", "84.0.0-beta.2", "84.0.0-beta.3"),
        ("fenix", "84.0.0-rc.1", "84.0.0-rc.2"),
        ("fenix", "84.0.0", "84.0.1"),
        ("android-components", "84.0.0", "84.0.1"),
        ("focus-android", "95.0.0", "95.0.1"),
    ),
)
def test_bump_version(product, version, result):
    assert bump_version(product, version) == result


@pytest.mark.parametrize(
    "product, version, result",
    (
        ("firefox", "59.0", False),
        ("firefox", "65.0b3", False),
        ("firefox", "65.0b8", True),
        ("firefox", "65.0", True),
        ("firefox", "65.0.1", True),
        ("firefox", "60.5.0esr", True),
        ("fennec", "65.0b8", False),
        ("fennec", "65.0", False),
    ),
)
def test_is_partner_enabled(product, version, result):
    assert is_partner_enabled(product, version) == result


@pytest.mark.parametrize(
    "product, version, result",
    (
        ("firefox", "65.0b3", False),
        ("firefox", "65.0b8", True),
        ("firefox", "65.0", True),
        ("firefox", "65.0.1", True),
        ("firefox", "60.5.0esr", False),
        ("fennec", "65.0b8", False),
        ("fennec", "65.0", False),
    ),
)
def test_is_eme_free_enabled(product, version, result):
    assert is_eme_free_enabled(product, version) == result


def test_additional_emails(test_xpi_release):
    # new release
    additional_shipit_emails = get_signoff_emails(test_xpi_release.phases)
    assert len(additional_shipit_emails) == 0

    # build phase completion
    _phase = filter(lambda _phase: _phase.name == "build", test_xpi_release.phases)
    phase = list(_phase)[0]
    phase.completed_by = "releng@mozilla.com"
    additional_shipit_emails = get_signoff_emails(test_xpi_release.phases)
    assert len(additional_shipit_emails) == 1

    # build phase signoffs
    XPISignoff(completed="2021-07-15T23:03:10.179036Z", completed_by="addon-team@mozilla.com", signed=True, phase=phase)
    additional_shipit_emails = get_signoff_emails(test_xpi_release.phases)
    assert len(additional_shipit_emails) == 2

    # promote phase completion and signoffs
    _phase = filter(lambda _phase: _phase.name == "promote", test_xpi_release.phases)
    phase = list(_phase)[0]
    phase.completed_by = "special-admin@mozilla.com"
    XPISignoff(completed="2021-07-15T23:03:10.179036Z", completed_by="addon-team@mozilla.com", signed=True, phase=phase)
    XPISignoff(completed="2021-07-15T23:03:10.179036Z", completed_by="another-team@mozilla.com", signed=True, phase=phase)
    additional_shipit_emails = get_signoff_emails(test_xpi_release.phases)
    assert len(additional_shipit_emails) == 4
