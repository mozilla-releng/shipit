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

from shipit_api.common.models import MergeAutomation, NightlyRelease, Release, TaskStatus, Version

API_FROM = "https://shipit-api.mozilla-releng.net"


def _coerce_datetimes(_, __, target):
    # Production runs against Postgres, which accepts the ISO strings the import
    # assigns to created/completed columns. SQLite (used in tests) requires real
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
    event.listen(Release, "before_insert", _coerce_datetimes)
    event.listen(MergeAutomation, "before_insert", _coerce_datetimes)
    try:
        with patch.dict(sys.modules, {"shipit_api.admin.flask": fake_flask}):
            import shipit_api.admin.cli as cli_module

            importlib.reload(cli_module)
            yield cli_module
    finally:
        event.remove(Release, "before_insert", _coerce_datetimes)
        event.remove(MergeAutomation, "before_insert", _coerce_datetimes)


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


def make_merge_automation(
    product,
    behavior,
    revision,
    version,
    task_id,
    created,
    completed=None,
    status="completed",
    dry_run=False,
    commit_message="",
    commit_author="",
    repo="",
    pretty_name="",
    project="",
):
    return {
        "id": 1,
        "product": product,
        "behavior": behavior,
        "revision": revision,
        "dry_run": dry_run,
        "created": created,
        "completed": completed,
        "status": status,
        "task_id": task_id,
        "version": version,
        "commit_message": commit_message,
        "commit_author": commit_author,
        "repo": repo,
        "pretty_name": pretty_name,
        "project": project,
    }


def register_merge_automations(responses, products=None):
    products = products or {}
    responses.add(responses.GET, f"{API_FROM}/merge-automation/products", json=list(products.keys()))
    for product, merges in products.items():
        responses.add(responses.GET, f"{API_FROM}/merge-automation?product={product}", json=merges)


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
    register_merge_automations(responses)

    run_import(cli)

    assert Release.query.count() == 2
    assert NightlyRelease.query.count() == 3

    firefox = NightlyRelease.query.filter_by(product="firefox", buildid="20260601000000").one()
    assert firefox.locales == ["en-US", "de"]

    versions = {(v.product_name, v.product_channel): v.current_version for v in Version.query.all()}
    assert versions == {("firefox", "nightly"): "140.0a1", ("thunderbird", "nightly"): "140.0a1"}


def test_shipit_import_skips_releases_and_nightlies_when_limit_zero(cli, responses):
    register_versions(responses)
    register_merge_automations(responses)

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
    register_merge_automations(responses)

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
    register_merge_automations(responses)

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
    register_merge_automations(responses)

    run_import(cli, "--limit-releases", "-1")

    assert Release.query.count() == 2
    assert NightlyRelease.query.filter_by(product="firefox").count() == 2


def test_shipit_import_imports_merge_automations(cli, responses):
    register_versions(responses)
    register_merge_automations(
        responses,
        {
            "firefox": [
                make_merge_automation(
                    "firefox",
                    "central-to-beta",
                    "abcdef",
                    "129.0",
                    "task1",
                    "2026-06-01T00:00:00",
                    completed="2026-06-01T01:00:00",
                    status="completed",
                    dry_run=False,
                    commit_message="Bump version",
                    commit_author="someone@mozilla.com",
                    repo="https://hg.mozilla.org/mozilla-central",
                    pretty_name="mozilla-central",
                    project="mozilla-central",
                ),
                make_merge_automation(
                    "firefox",
                    "beta-to-release",
                    "123456",
                    "128.0",
                    "task2",
                    "2026-06-02T00:00:00",
                    completed=None,
                    status="pending",
                    dry_run=True,
                    commit_message="Bump version to 128.0",
                    commit_author="someone-else@mozilla.com",
                    repo="https://hg.mozilla.org/releases/mozilla-beta",
                    pretty_name="mozilla-beta",
                    project="mozilla-beta",
                ),
            ],
            "firefox-ios": [
                make_merge_automation(
                    "firefox-ios",
                    "central-to-beta",
                    "fedcba",
                    "129.0",
                    "task3",
                    "2026-06-03T00:00:00",
                    completed=None,
                    status="running",
                    dry_run=False,
                    commit_message="Bump version to 129.0",
                    commit_author="someone@mozilla.com",
                    repo="https://github.com/mozilla-mobile/firefox-ios",
                    pretty_name="firefox-ios",
                    project="firefox-ios",
                ),
            ],
        },
    )

    run_import(cli, "--limit-releases", "0")

    assert MergeAutomation.query.count() == 3

    task1 = MergeAutomation.query.filter_by(task_id="task1").one()
    assert task1.product == "firefox"
    assert task1.behavior == "central-to-beta"
    assert task1.revision == "abcdef"
    assert task1.version == "129.0"
    assert task1.dry_run is False
    assert task1.created == datetime(2026, 6, 1, 0, 0, 0)
    assert task1.completed == datetime(2026, 6, 1, 1, 0, 0)
    assert task1.status == TaskStatus.Completed
    assert task1.commit_message == "Bump version"
    assert task1.commit_author == "someone@mozilla.com"
    assert task1.repo == "https://hg.mozilla.org/mozilla-central"
    assert task1.pretty_name == "mozilla-central"
    assert task1.project == "mozilla-central"

    task2 = MergeAutomation.query.filter_by(task_id="task2").one()
    assert task2.product == "firefox"
    assert task2.behavior == "beta-to-release"
    assert task2.status == TaskStatus.Pending

    task3 = MergeAutomation.query.filter_by(task_id="task3").one()
    assert task3.product == "firefox-ios"
    assert task3.behavior == "central-to-beta"
    assert task3.status == TaskStatus.Running


def test_shipit_import_raises_on_unknown_merge_automation_status(cli, responses):
    register_versions(responses)
    register_merge_automations(
        responses,
        {
            "firefox": [
                make_merge_automation(
                    "firefox",
                    "central-to-beta",
                    "abcdef",
                    "129.0",
                    "task1",
                    "2026-06-01T00:00:00",
                    completed="2026-06-01T01:00:00",
                    status="bogus",
                    dry_run=False,
                    commit_message="Bump version",
                    commit_author="someone@mozilla.com",
                    repo="https://hg.mozilla.org/mozilla-central",
                    pretty_name="mozilla-central",
                    project="mozilla-central",
                ),
            ],
        },
    )

    with pytest.raises(Exception, match="Unknown merge automation status: Bogus"):
        run_import(cli, "--limit-releases", "0")
