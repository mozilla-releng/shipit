# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import pathlib
import re
import subprocess
from unittest import mock

import aiohttp
import pytest
from aioresponses import aioresponses
from sqlalchemy import engine, event

import shipit_api.admin.product_details
from shipit_api.admin.product_details import fetch_l10n_data, rebuild
from shipit_api.common.models import Release, Version


# product_details uses a postgresql-specific "split_part" sql function
@event.listens_for(engine.Engine, "connect")
def setup_split_part(dbapi_connection, conn_rec):
    def split_part(string, delimiter, position):
        return string.split(delimiter, position)[position - 1]

    dbapi_connection.create_function(
        "split_part",
        3,
        split_part,
    )


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
        _, changesets = await fetch_l10n_data(session, release, raise_on_failure=True, use_cache=False)
        assert changesets == {"a": "a"}

        # simulate HTTP errors.
        # Fail first time
        m.get(url, status=500)
        # Return proper result second time
        m.get(url, status=200, payload=dict(a="a"))
        _, changesets = await fetch_l10n_data(session, release, raise_on_failure=True, use_cache=False)
        assert changesets == {"a": "a"}

        # simulate timeout
        # Fail first time
        m.get(url, timeout=True)
        # Return proper result second time
        m.get(url, status=200, payload=dict(a="a"))
        _, changesets = await fetch_l10n_data(session, release, raise_on_failure=True, use_cache=False)
        assert changesets == {"a": "a"}


def mock_setup_working_copy(branch, url, secrets):
    subprocess.check_call(["git", "clone", "-n", url, str(shipit_api.common.config.PRODUCT_DETAILS_DIR)])
    subprocess.check_call(["git", "checkout", "-b", branch, "906b7cd284728a2acec695ddcba9193b44d38982"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)
    subprocess.check_call(["git", "config", "user.email", "release-services+robot@mozilla.com"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)
    subprocess.check_call(["git", "config", "user.name", "Release Services Robot"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)
    subprocess.check_call(["git", "config", "commit.gpgsign", "false"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)


def mock_git_push(branch, secrets):
    return


@pytest.mark.asyncio
@mock.patch("shipit_api.admin.product_details.setup_working_copy", mock_setup_working_copy)
@mock.patch("shipit_api.admin.product_details.git_push", mock_git_push)
async def test_rebuild(app, tmp_path):
    fxnightly = Version(product_name="firefox", current_version="135.0a1", product_channel="nightly")
    tbnightly = Version(product_name="thunderbird", current_version="135.0a1", product_channel="nightly")
    deved = Release(
        product="devedition",
        branch="releases/mozilla-beta",
        version="134.0b9",
        revision="615791f9752c70ef1757abf68544c8275f219ce3",
        build_number=1,
        release_eta=None,
        status="shipped",
        partial_updates=None,
    )
    beta = Release(
        product="firefox",
        branch="releases/mozilla-beta",
        version="134.0b8",
        revision="9fb87e89c26069198ce2a59a0a790a264d225169",
        build_number=1,
        release_eta=None,
        status="shipped",
        partial_updates=None,
    )
    release = Release(
        product="firefox",
        branch="releases/mozilla-release",
        version="133.0",
        revision="8141aab3ba856d7cbae6c851dd71f2e0cb69649c",
        build_number=2,
        release_eta=None,
        status="shipped",
        partial_updates=None,
    )
    app.app.db.session.add(fxnightly)
    app.app.db.session.add(tbnightly)
    app.app.db.session.add(deved)
    app.app.db.session.add(beta)
    app.app.db.session.add(release)
    app.app.db.session.commit()
    with (
        mock.patch("shipit_api.common.config.PRODUCT_DETAILS_DIR", tmp_path / "product-details"),
        mock.patch("shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR", tmp_path / "product-details-new"),
        mock.patch("shipit_api.common.config.PRODUCT_DETAILS_CACHE_DIR", tmp_path / "product-details-cache"),
        aioresponses(passthrough=["https://hg.mozilla.org"]) as m,
    ):
        m.get(
            "https://whattrainisitnow.com/api/release/schedule/?version=135",
            repeat=True,
            payload={
                "version": "135.0",
                "nightly_start": "2024-11-25 00:00:00+00:00",
                "a11y_request_deadline": "2024-11-29 00:00:00+00:00",
                "qa_request_deadline": "2024-11-29 00:00:00+00:00",
                "qa_feature_done_1": "2024-12-06 21:00:00+00:00",
                "qa_feature_done_2": "2025-01-02 08:00:00+00:00",
                "soft_code_freeze": "2025-01-02 08:00:00+00:00",
                "qa_test_plan_due": "2025-01-03 00:00:00+00:00",
                "string_freeze": "2025-01-03 00:00:00+00:00",
                "qa_pre_merge_done": "2025-01-03 14:00:00+00:00",
                "merge_day": "2025-01-06 00:00:00+00:00",
                "beta_1": "2025-01-06 00:00:00+00:00",
                "beta_2": "2025-01-08 13:00:00+00:00",
                "beta_3": "2025-01-10 13:00:00+00:00",
                "sumo_1": "2025-01-10 21:00:00+00:00",
                "beta_4": "2025-01-13 13:00:00+00:00",
                "beta_5": "2025-01-15 13:00:00+00:00",
                "beta_6": "2025-01-17 13:00:00+00:00",
                "beta_7": "2025-01-20 13:00:00+00:00",
                "sumo_2": "2025-01-20 21:00:00+00:00",
                "beta_8": "2025-01-22 13:00:00+00:00",
                "qa_pre_rc_signoff": "2025-01-22 14:00:00+00:00",
                "beta_9": "2025-01-24 13:00:00+00:00",
                "rc_gtb": "2025-01-27 21:00:00+00:00",
                "rc": "2025-01-28 00:00:00+00:00",
                "release": "2025-02-04 14:00:00+00:00",
                "mobile_dot_release": "2025-02-11 00:00:00+00:00",
                "planned_dot_release": "2025-02-18 00:00:00+00:00",
            },
        )
        m.get(
            "https://whattrainisitnow.com/api/release/schedule/?version=134",
            repeat=True,
            payload={
                "version": "134.0",
                "nightly_start": "2024-10-29 00:00:00+00:00",
                "soft_code_freeze": "2024-11-21 08:00:00+00:00",
                "string_freeze": "2024-11-22 00:00:00+00:00",
                "merge_day": "2024-11-25 00:00:00+00:00",
                "beta_1": "2024-11-26 00:00:00+00:00",
                "beta_2": "2024-11-27 00:00:00+00:00",
                "beta_3": "2024-11-29 00:00:00+00:00",
                "beta_4": "2024-12-02 00:00:00+00:00",
                "beta_5": "2024-12-04 00:00:00+00:00",
                "beta_6": "2024-12-06 00:00:00+00:00",
                "beta_7": "2024-12-09 00:00:00+00:00",
                "beta_8": "2024-12-11 00:00:00+00:00",
                "beta_9": "2024-12-13 00:00:00+00:00",
                "release": "2025-01-07 14:00:00+00:00",
            },
        )
        await rebuild(app.app.db.session, "testing", "https://github.com/mozilla-releng/product-details", "public", 130)

    parent = tmp_path / "product-details" / "public" / "1.0"
    with (parent / "firefox_versions.json").open() as f:
        versions = json.load(f)
    assert versions["FIREFOX_NIGHTLY"] == "135.0a1"
    assert versions["FIREFOX_DEVEDITION"] == "134.0b9"
    assert versions["LATEST_FIREFOX_DEVEL_VERSION"] == "134.0b8"
    assert versions["LATEST_FIREFOX_VERSION"] == "133.0"

    with (parent / "firefox_primary_builds.json").open() as f:
        primary_builds = json.load(f)
    assert set(primary_builds["ach"].keys()) == {"133.0", "134.0b8", "134.0b9", "135.0a1"}

    assert not list(parent.glob("l10n/Devedition-*"))
    assert next(parent.glob("l10n/Firefox-134.0b8-*")).name == "Firefox-134.0b8-build1.json"
