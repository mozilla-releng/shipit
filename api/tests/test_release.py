# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from shipit_api.admin.release import bump_version, is_beta, is_eme_free_enabled, is_esr, is_final_release, is_partner_enabled, is_rc


@pytest.mark.parametrize("version, result", (("57.0", True), ("7.0", True), ("123.0", True), ("56.0b3", False), ("41.0esr", False), ("78.0.1", False)))
def test_is_final_version(version, result):
    assert is_final_release(version) == result


@pytest.mark.parametrize("version, result", (("57.0", False), ("7.0", False), ("123.0", False), ("56.0b3", True), ("41.0esr", False), ("78.0.1", False)))
def test_is_beta(version, result):
    assert is_beta(version) == result


@pytest.mark.parametrize("version, result", (("57.0", False), ("7.0", False), ("123.0", False), ("56.0b3", False), ("41.0esr", True), ("78.0.1", False)))
def test_is_esr(version, result):
    assert is_esr(version) == result


@pytest.mark.parametrize(
    "product, version, partial_updates, result",
    (
        ("firefox", "41.0esr", None, False),
        ("fennec", "56.0b3", None, False),
        ("firefox", "57.0", {"56.0b1": [], "55.0": []}, True),
        ("firefox", "57.0", {"56.0": [], "55.0": []}, True),
        ("thunderbird", "57.0", {"56.0": [], "55.0": []}, False),
        ("firefox", "64.0", None, True),
        ("thunderbird", "64.0", None, False),
        ("fennec", "64.0", None, True),
        ("firefox", "64.0.1", None, False),
        ("thunderbird", "64.0.1", None, False),
        # Fennec on the 68 branch is a special case
        ("fennec", "68.0", None, True),
        ("fennec", "68.2.0", None, True),
        ("fennec", "68.2.1", None, False),
        ("fennec", "68.3.0", None, True),
        ("fennec", "68.3.1", None, False),
    ),
)
def test_is_rc(product, version, partial_updates, result):
    assert is_rc(product, version, partial_updates) == result


@pytest.mark.parametrize(
    "version, result",
    (("45.0", "45.0.1"), ("45.0.1", "45.0.2"), ("45.0b3", "45.0b4"), ("45.0esr", "45.0.1esr"), ("45.0.1esr", "45.0.2esr"), ("45.2.1esr", "45.2.2esr")),
)
def test_bump_version(version, result):
    assert bump_version(version) == result


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
