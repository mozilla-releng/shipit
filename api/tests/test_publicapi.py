# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pathlib import Path

import pytest

from backend_common import build_api_specification
from cli_common.openapi_subset import PUBLIC_API_SECTIONS, extract
from shipit_api.common.product import Product
from shipit_api.public import api


def test_public_api_subset():
    full_api = build_api_specification(Path(__file__).parent.parent / "src/shipit_api/admin")
    public_api = build_api_specification(Path(__file__).parent.parent / "src/shipit_api/public")
    generated_public_api = extract(full_api, PUBLIC_API_SECTIONS)
    # If this fails, check the diff; each file needs to match exactly, including the ordering of enum values
    assert generated_public_api == public_api


@pytest.mark.parametrize(
    "release, expected",
    (
        ({"product": "firefox", "version": "123.0"}, True),
        ({"product": Product.FIREFOX_ANDROID, "version": "123.0b4"}, True),
        ({"product": "firefox", "version": "123.4"}, False),
    ),
)
def test_good_version(release, expected):
    assert api.good_version(release) == expected
