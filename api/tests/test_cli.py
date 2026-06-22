import importlib
import json
import sys
from datetime import datetime
from types import ModuleType
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from click.testing import CliRunner
from sqlalchemy import event

from shipit_api.common.models import NightlyRelease, Release, Version

API_FROM = "https://shipit-api.mozilla-releng.net"


def _coerce_release_datetimes(_, __, target):
    # Production runs against Postgres, which accepts the ISO strings the import
    # assigns to Release.created/completed. SQLite (used in tests) requires real
    # datetime objects, so bridge the difference here.
    for field in ("created", "completed"):
        value = getattr(target, field)
        if isinstance(value, str):
            setattr(target, field, datetime.fromisoformat(value))


@pytest.fixture
def cli(app):
    # Importing shipit_api.admin.cli builds a real flask app from settings.py at
    # import time. Stub the module so the command runs against the test app.
    fake_flask = ModuleType("shipit_api.admin.flask")
    fake_flask.app = app
    fake_flask.flask_app = app.app
    event.listen(Release, "before_insert", _coerce_release_datetimes)
    try:
        with patch.dict(sys.modules, {"shipit_api.admin.flask": fake_flask}):
            import shipit_api.admin.cli as cli_module

            importlib.reload(cli_module)
            yield cli_module
    finally:
        event.remove(Release, "before_insert", _coerce_release_datetimes)


def run_import(cli, *args):
    result = CliRunner().invoke(cli.shipit_import, list(args), catch_exceptions=False)
    assert result.exit_code == 0, result.output
    return result


def make_release(product, version, build_number, created, status="shipped", completed=None):
    return {
        "name": f"{product.capitalize()}-{version}-build{build_number}",
        "product": product,
        "version": version,
        "branch": "releases/mozilla-release",
        "revision": "abcdef",
        "build_number": build_number,
        "release_eta": None,
        "partials": None,
        "status": status,
        "created": created,
        "completed": completed or created,
    }


def make_nightly(product, channel, version, buildid, locales=None):
    return {
        "product": product,
        "channel": channel,
        "version": version,
        "buildid": buildid,
        "locales": locales or ["en-US"],
    }


def make_nightly_model(product, channel, version, buildid, locales=None):
    return NightlyRelease(product=product, channel=channel, version=version, buildid=buildid, locales=locales or ["en-US"])


def register_releases(responses, releases):
    responses.add(responses.GET, f"{API_FROM}/releases", json=releases)


def register_versions(responses, firefox="140.0a1", thunderbird="140.0a1"):
    responses.add(responses.GET, f"{API_FROM}/versions/firefox/nightly", json=firefox)
    responses.add(responses.GET, f"{API_FROM}/versions/thunderbird/nightly", json=thunderbird)


def register_nightlies(responses, datasets):
    def _callback(request):
        qs = parse_qs(urlparse(request.url).query)
        product = qs["product"][0]
        channel = qs["channel"][0]
        limit = int(qs.get("limit", ["500"])[0])
        before_buildid = qs.get("before_buildid", [None])[0]

        items = sorted(datasets.get((product, channel), []), key=lambda n: n["buildid"], reverse=True)
        if before_buildid is not None:
            items = [n for n in items if n["buildid"] < before_buildid]
        return (200, {"Content-Type": "application/json"}, json.dumps(items[:limit]))

    responses.add_callback(responses.GET, f"{API_FROM}/nightly-release", callback=_callback)


def test_shipit_import_imports_releases_nightlies_and_versions(cli, responses):
    register_releases(
        responses,
        [
            make_release("firefox", "128.0", 1, "2026-06-01T00:00:00"),
            make_release("firefox", "129.0", 1, "2026-06-02T00:00:00"),
        ],
    )
    register_nightlies(
        responses,
        {
            ("firefox", "nightly"): [
                make_nightly("firefox", "nightly", "140.0a1", "20260601000000", ["en-US", "de"]),
                make_nightly("firefox", "nightly", "140.0a1", "20260602000000"),
            ],
            ("thunderbird", "nightly"): [
                make_nightly("thunderbird", "nightly", "140.0a1", "20260603000000"),
            ],
        },
    )
    register_versions(responses)

    run_import(cli)

    assert Release.query.count() == 2
    assert NightlyRelease.query.count() == 3

    firefox = NightlyRelease.query.filter_by(product="firefox", buildid="20260601000000").one()
    assert firefox.locales == ["en-US", "de"]

    versions = {(v.product_name, v.product_channel): v.current_version for v in Version.query.all()}
    assert versions == {("firefox", "nightly"): "140.0a1", ("thunderbird", "nightly"): "140.0a1"}


def test_shipit_import_skips_releases_and_nightlies_when_limit_zero(cli, responses):
    register_versions(responses)

    run_import(cli, "--limit-releases", "0")

    assert Release.query.count() == 0
    assert NightlyRelease.query.count() == 0
    assert Version.query.count() == 2


def test_shipit_import_limits_to_most_recent_releases_and_nightlies(cli, responses):
    register_releases(
        responses,
        [
            make_release("firefox", "128.0", 1, "2026-06-01T00:00:00"),
            make_release("firefox", "129.0", 1, "2026-06-02T00:00:00"),
            make_release("firefox", "130.0", 1, "2026-06-03T00:00:00"),
        ],
    )
    register_nightlies(
        responses,
        {
            ("firefox", "nightly"): [make_nightly("firefox", "nightly", "140.0a1", f"2026060{i}000000") for i in range(1, 6)],
            ("thunderbird", "nightly"): [make_nightly("thunderbird", "nightly", "140.0a1", "20260601000000")],
        },
    )
    register_versions(responses)

    run_import(cli, "--limit-releases", "2")

    imported_releases = {r.version for r in Release.query.all()}
    assert imported_releases == {"129.0", "130.0"}

    firefox_buildids = sorted(n.buildid for n in NightlyRelease.query.filter_by(product="firefox").all())
    assert firefox_buildids == ["20260604000000", "20260605000000"]
    assert NightlyRelease.query.filter_by(product="thunderbird").count() == 1


def test_shipit_import_pages_through_all_nightlies(cli, responses):
    register_releases(responses, [])
    firefox_nightlies = [make_nightly("firefox", "nightly", "140.0a1", str(20260000000000 + i)) for i in range(600)]
    register_nightlies(responses, {("firefox", "nightly"): firefox_nightlies})
    register_versions(responses)

    run_import(cli, "--limit-releases", "-1")

    assert NightlyRelease.query.filter_by(product="firefox").count() == 600


def test_shipit_import_skips_existing_entries(cli, responses):
    from backend_common.db import db

    existing_release = make_release("firefox", "128.0", 1, "2026-06-01T00:00:00")
    db.session.add(
        Release(
            product="firefox",
            version="128.0",
            branch="releases/mozilla-release",
            revision="abcdef",
            build_number=1,
            release_eta=None,
            partial_updates=None,
            status="shipped",
        )
    )
    db.session.add(make_nightly_model("firefox", "nightly", "140.0a1", "20260601000000"))
    db.session.commit()

    register_releases(
        responses,
        [
            existing_release,
            make_release("firefox", "129.0", 1, "2026-06-02T00:00:00"),
        ],
    )
    register_nightlies(
        responses,
        {
            ("firefox", "nightly"): [
                make_nightly("firefox", "nightly", "140.0a1", "20260601000000"),
                make_nightly("firefox", "nightly", "140.0a1", "20260602000000"),
            ],
        },
    )
    register_versions(responses)

    run_import(cli, "--limit-releases", "-1")

    assert Release.query.count() == 2
    assert NightlyRelease.query.filter_by(product="firefox").count() == 2
