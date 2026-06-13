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
from shipit_api.common.models import NightlyRelease, Release, Version


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
    subprocess.check_call(["git", "checkout", "-b", branch, "26140d3435c386f36a94bd23ded5d08f8a41f080"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)
    subprocess.check_call(["git", "config", "user.email", "release-services+robot@mozilla.com"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)
    subprocess.check_call(["git", "config", "user.name", "Release Services Robot"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)
    subprocess.check_call(["git", "config", "commit.gpgsign", "false"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR)


def mock_git_push(branch, secrets):
    return


# A representative set of Firefox/Thunderbird locales. The exact contents don't
# matter, but there must be more than the sanity check's minimum (20) so that
# sanity_check_firefox_builds passes, and "ach" must be present (asserted below).
L10N_CHANGESETS = {
    locale: {"revision": "abcdef123456", "platforms": ["linux", "linux64", "macosx64", "win32", "win64"], "pin": False}
    for locale in (
        "ach",
        "af",
        "an",
        "ar",
        "ast",
        "az",
        "be",
        "bg",
        "bn",
        "br",
        "bs",
        "ca",
        "cak",
        "cs",
        "cy",
        "da",
        "de",
        "dsb",
        "el",
        "en-CA",
        "en-GB",
        "eo",
        "es-AR",
        "es-CL",
        "es-ES",
        "es-MX",
        "et",
        "eu",
        "fa",
        "ff",
    )
}


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
    # Two firefox nightly builds. "ach" is in both, so its first appearance is
    # the earlier buildid; "zz" only appears in the newer one.
    nightly_build_1 = NightlyRelease(
        product="firefox", channel="nightly", version="134.0a1", buildid="20241101093000", locales=list(L10N_CHANGESETS.keys()) + ["en-US"]
    )
    nightly_build_2 = NightlyRelease(
        product="firefox", channel="nightly", version="135.0a1", buildid="20241225093000", locales=list(L10N_CHANGESETS.keys()) + ["en-US", "zz"]
    )
    app.app.db.session.add(fxnightly)
    app.app.db.session.add(tbnightly)
    app.app.db.session.add(deved)
    app.app.db.session.add(beta)
    app.app.db.session.add(release)
    app.app.db.session.add(nightly_build_1)
    app.app.db.session.add(nightly_build_2)
    app.app.db.session.commit()
    with (
        mock.patch("shipit_api.common.config.PRODUCT_DETAILS_DIR", tmp_path / "product-details"),
        mock.patch("shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR", tmp_path / "product-details-new"),
        mock.patch("shipit_api.common.config.PRODUCT_DETAILS_CACHE_DIR", tmp_path / "product-details-cache"),
        aioresponses() as m,
    ):
        hg_l10n_urls = [
            # devedition 134.0b9
            "https://hg.mozilla.org/releases/mozilla-beta/raw-file/615791f9752c70ef1757abf68544c8275f219ce3/browser/locales/l10n-changesets.json",
            # firefox beta 134.0b8
            "https://hg.mozilla.org/releases/mozilla-beta/raw-file/9fb87e89c26069198ce2a59a0a790a264d225169/browser/locales/l10n-changesets.json",
            # firefox release 133.0
            "https://hg.mozilla.org/releases/mozilla-release/raw-file/8141aab3ba856d7cbae6c851dd71f2e0cb69649c/browser/locales/l10n-changesets.json",
            # firefox nightly 135.0a1
            "https://hg.mozilla.org/mozilla-central/raw-file/default/browser/locales/l10n-changesets.json",
            # thunderbird nightly 135.0a1
            "https://hg.mozilla.org/comm-central/raw-file/default/mail/locales/l10n-changesets.json",
        ]
        for url in hg_l10n_urls:
            m.get(url, repeat=True, payload=L10N_CHANGESETS)
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

    # we do some basic checking of this file; it is too large to do extensive checks of
    # note that most of its contents come from the `testing` branch of the product-details repo
    with (parent / "firefox_history_locales.json").open() as f:
        locales = json.load(f)
    assert locales["ach"]["first_release"] == {
        "nightly": {"version": "134.0a1", "buildid": "20241101093000"},
        "beta": {"version": "19.0b1", "build_number": 1},
        "aurora": {"version": "54.0b11", "build_number": 1},
        "release": {"version": "18.0", "build_number": 1},
        "esr": {"version": "17.0.2esr", "build_number": 1},
    }
    assert locales["de"]["first_release"]["esr"] == {"version": "10.0.12esr", "build_number": 1}
    # "zz" only appears in the newer nightly build, and in no release channel
    assert locales["zz"]["first_release"] == {"nightly": {"version": "135.0a1", "buildid": "20241225093000"}}


def build_old_product_details(l10n_files):
    return {f"1.0/l10n/{name}.json": {"locales": {locale: {"changeset": "default"} for locale in locales}} for name, locales in l10n_files.items()}


def build_firefox_releases(entries):
    return {
        "releases": {
            f"firefox-{version}": {
                "category": category,
                "product": "firefox",
                "build_number": build_number,
                "version": version.replace("esr", ""),
            }
            for version, category, build_number in entries
        }
    }


def test_get_firefox_locales():
    nightly_releases = [
        NightlyRelease(product="firefox", channel="nightly", version="56.0a1", buildid="20170200000000", locales=["af", "de", "en-US", "fr"]),
        NightlyRelease(product="firefox", channel="nightly", version="55.0a1", buildid="20170100000000", locales=["af", "de", "en-US"]),
        NightlyRelease(product="firefox", channel="nightly", version="40.0a1", buildid="20150100000000", locales=["de", "en-US"]),
        NightlyRelease(product="firefox", channel="nightly", version="6.0a1", buildid="20110100000000", locales=["af", "de", "en-US"]),
    ]
    firefox_releases = build_firefox_releases(
        [
            ("110.0b1", "dev", 1),
            ("134.0b8", "dev", 1),
            ("134.0b9", "dev", 2),
            ("133.0", "major", 2),
            ("140.0esr", "major", 1),
            ("140.2.0esr", "stability", 1),
            ("128.0esr", "stability", 1),
            ("52.9.0esr", "esr", 2),
        ]
    )
    old_product_details = build_old_product_details(
        {
            "Firefox-110.0b1-build1": ["de"],
            "Firefox-134.0b8-build1": ["af", "de"],
            "Firefox-134.0b9-build2": ["af", "de", "fr"],
            "Firefox-133.0-build2": ["af", "de", "fr"],
            "Firefox-140.0esr-build1": ["de", "fr"],
            "Firefox-140.2.0esr-build1": ["de", "fr"],
            "Firefox-128.0esr-build1": ["de", "fr", "as"],
            "Firefox-52.9.0esr-build2": ["de", "as"],
        }
    )

    result = shipit_api.admin.product_details.get_firefox_locales(firefox_releases, old_product_details, nightly_releases)

    # dropped after esr128
    assert "as" not in result
    # en-US should not be included in this file, even though it's part of nightly release metadata
    assert "en-US" not in result
    assert result["af"]["first_release"] == {
        # "af" had a gap (present in 6.0a1, absent in 40.0a1, back from 55.0a1), so
        # its first_release is the start of the most recent gap-free run, not 6.0a1.
        "nightly": {"version": "55.0a1", "buildid": "20170100000000"},
        "beta": {"version": "134.0b8", "build_number": 1},
        "release": {"version": "133.0", "build_number": 2},
        "aurora": {"version": "134.0b8", "build_number": 1},
    }
    assert result["de"]["first_release"] == {
        # "de" was never dropped, so its run starts at the oldest build
        "nightly": {"version": "6.0a1", "buildid": "20110100000000"},
        "beta": {"version": "110.0b1", "build_number": 1},
        "release": {"version": "133.0", "build_number": 2},
        "aurora": {"version": "110.0b1", "build_number": 1},
        "esr": {"version": "52.9.0esr", "build_number": 2},
    }
    assert result["fr"]["first_release"] == {
        # "fr" only appears in the newest build
        "nightly": {"version": "56.0a1", "buildid": "20170200000000"},
        "beta": {"version": "134.0b9", "build_number": 2},
        "release": {"version": "133.0", "build_number": 2},
        "aurora": {"version": "134.0b9", "build_number": 2},
        "esr": {"version": "128.0esr", "build_number": 1},
    }


def test_get_firefox_nightly_locales_stops_early():
    # newest-first; "af" (the only locale of interest) is continuous in the two
    # newest builds, then disappears in 58.0a1. At that point the result is fully
    # determined and any older build is irrelevant, so it must never be fetched.
    consumed = []

    def build_stream():
        builds = [
            ("60.0a1", "20180300000000", ["af", "en-US"]),
            ("59.0a1", "20180200000000", ["af", "en-US"]),
            ("58.0a1", "20180100000000", ["en-US"]),
            # older than the point where the result is determined; consuming this
            # would mean we failed to stop early
            ("57.0a1", "20170100000000", ["af", "en-US"]),
        ]
        for version, buildid, locales in builds:
            consumed.append(buildid)
            yield NightlyRelease(product="firefox", channel="nightly", version=version, buildid=buildid, locales=locales)

    result = shipit_api.admin.product_details.get_firefox_nightly_locales(build_stream())

    assert result["af"]["first_release"] == {"nightly": {"version": "59.0a1", "buildid": "20180200000000"}}
    assert consumed == ["20180300000000", "20180200000000", "20180100000000"]
