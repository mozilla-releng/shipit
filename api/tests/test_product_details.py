# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pathlib
import re

import aiohttp
import pytest
from aioresponses import aioresponses

import shipit_api.admin.product_details
from shipit_api.admin.product_details import fetch_l10n_data
from shipit_api.common.models import Release


def create_html(folder, items):
    return shipit_api.admin.product_details.create_index_listing_html(pathlib.Path(folder), [pathlib.Path(item) for item in items])


@pytest.mark.parametrize(
    "product_details, product_details_final",
    (
        (
            {"1.0/all.json": {}, "1.0/l10n/en.json": {}},
            {
                "1.0/all.json": {},
                "1.0/l10n/en.json": {},
                "index.html": create_html("", ["1.0"]),
                "1.0/index.html": create_html("1.0", ["1.0/all.json", "1.0/l10n"]),
                "1.0/l10n/index.html": create_html("1.0/l10n", ["1.0/l10n/en.json"]),
            },
        ),
    ),
)
def test_create_index_listing(product_details, product_details_final):
    assert shipit_api.admin.product_details.create_index_listing(product_details) == product_details_final


@pytest.mark.asyncio
async def test_fetch_l10n_data():
    release = Release(
        product="firefox",
        branch="releases/mozilla-beta",
        version="62.0b16",
        revision="812b11ed03e02e7d5ec9f23c6abcbc46d7859740",
        build_number=1,
        release_eta=None,
        status="shipped",
        partial_updates=None,
    )
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1))
    url = re.compile(r"^https://hg\.mozilla\.org/")
    with aioresponses() as m:
        m.get(url, status=200, payload=dict(a="a"))
        (_, changesets) = await fetch_l10n_data(session, release, raise_on_failure=True, use_cache=False)
        assert changesets == {"a": "a"}

        # simulate HTTP errors.
        # Fail first time
        m.get(url, status=500)
        # Return proper result second time
        m.get(url, status=200, payload=dict(a="a"))
        (_, changesets) = await fetch_l10n_data(session, release, raise_on_failure=True, use_cache=False)
        assert changesets == {"a": "a"}

        # simulate timeout
        # Fail first time
        m.get(url, timeout=True)
        # Return proper result second time
        m.get(url, status=200, payload=dict(a="a"))
        (_, changesets) = await fetch_l10n_data(session, release, raise_on_failure=True, use_cache=False)
        assert changesets == {"a": "a"}
