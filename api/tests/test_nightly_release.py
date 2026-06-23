from unittest.mock import Mock, patch

from backend_common.db import db
from shipit_api.common.models import NightlyRelease


def test_list_nightly_releases_empty(app):
    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly")
        assert response.status_code == 200
        assert response.json() == []


def test_list_nightly_releases(app):
    n1 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US", "de"])
    n2 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260523093015", locales=["en-US", "de"])
    db.session.add(n1)
    db.session.add(n2)
    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        assert sorted(r["buildid"] for r in results) == ["20260522093015", "20260523093015"]


def test_list_nightly_releases_filter_by_buildid(app):
    n1 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US", "de"])
    n2 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260523093015", locales=["en-US", "de"])
    db.session.add(n1)
    db.session.add(n2)

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&buildid=20260523093015")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["buildid"] == "20260523093015"
        assert results[0]["locales"] == ["en-US", "de"]


def test_list_nightly_releases_filter_by_version(app):
    n1 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US", "de"])
    n2 = NightlyRelease(product="firefox", channel="nightly", version="141.0a1", buildid="20260523093015", locales=["en-US", "de"])
    db.session.add(n1)
    db.session.add(n2)

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&version=141.0a1")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["version"] == "141.0a1"


def test_list_nightly_releases_no_match(app):
    n1 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US", "de"])
    db.session.add(n1)

    with app.test_client() as client:
        response = client.get("/nightly-release?product=does-not-exist&channel=nightly")
        assert response.status_code == 200
        assert response.json() == []


def test_list_nightly_releases_missing_product_returns_400(app):
    with app.test_client() as client:
        response = client.get("/nightly-release?channel=nightly")
        assert response.status_code == 400


def test_list_nightly_releases_missing_channel_returns_400(app):
    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox")
        assert response.status_code == 400


@patch("shipit_api.admin.api.current_user", new_callable=lambda: Mock())
def test_add_nightly_release(mock_user, app):
    mock_user.has_permissions.return_value = True

    with app.test_client() as client:
        response = client.post(
            "/nightly-release",
            json={
                "product": "firefox",
                "channel": "nightly",
                "version": "140.0a1",
                "buildid": "20260522093015",
                "locales": ["en-US", "de", "fr"],
            },
        )
        assert response.status_code == 201


@patch("shipit_api.admin.api.current_user", new_callable=lambda: Mock())
def test_add_nightly_release_duplicate_buildid_returns_400(mock_user, app):
    mock_user.has_permissions.return_value = True

    n1 = NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US", "de"])
    db.session.add(n1)

    with app.test_client() as client:
        response = client.post(
            "/nightly-release",
            json={
                "product": "firefox",
                "channel": "nightly",
                "version": "140.0a1",
                "buildid": "20260522093015",
                "locales": ["de"],
            },
        )
        assert response.status_code == 400


@patch("shipit_api.admin.api.current_user", new_callable=lambda: Mock())
def test_add_nightly_release_empty_locale_returns_400(mock_user, app):
    mock_user.has_permissions.return_value = True

    with app.test_client() as client:
        response = client.post(
            "/nightly-release",
            json={
                "product": "firefox",
                "channel": "nightly",
                "version": "140.0a1",
                "buildid": "20260522093015",
                "locales": ["de", ""],
            },
        )
        assert response.status_code == 400


@patch("shipit_api.admin.api.current_user", new_callable=lambda: Mock())
def test_add_nightly_release_permission_denied(mock_user, app):
    mock_user.has_permissions.return_value = False
    mock_user.get_permissions.return_value = ["some:other:permission"]

    with app.test_client() as client:
        response = client.post(
            "/nightly-release",
            json={
                "product": "firefox",
                "channel": "nightly",
                "version": "140.0a1",
                "buildid": "20260522093015",
                "locales": ["en-US"],
            },
        )
        assert response.status_code == 401
        detail = response.json()["detail"]
        assert "project:releng:services/shipit_api/add_release/firefox" in detail


def test_list_nightly_releases_default_order_desc(app):
    db.session.add(NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US"]))
    db.session.add(NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260523093015", locales=["en-US"]))
    db.session.add(NightlyRelease(product="firefox", channel="nightly", version="141.0a1", buildid="20260524093015", locales=["en-US"]))

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly")
        assert response.status_code == 200
        results = response.json()
        assert [r["buildid"] for r in results] == ["20260524093015", "20260523093015", "20260522093015"]


def test_list_nightly_releases_order_asc(app):
    db.session.add(NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260522093015", locales=["en-US"]))
    db.session.add(NightlyRelease(product="firefox", channel="nightly", version="140.0a1", buildid="20260523093015", locales=["en-US"]))
    db.session.add(NightlyRelease(product="firefox", channel="nightly", version="141.0a1", buildid="20260524093015", locales=["en-US"]))

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&order=asc")
        assert response.status_code == 200
        results = response.json()
        assert [r["buildid"] for r in results] == ["20260522093015", "20260523093015", "20260524093015"]


def test_list_nightly_releases_filter_by_after_buildid(app):
    for i in range(5):
        db.session.add(
            NightlyRelease(
                product="firefox",
                channel="nightly",
                version="140.0a1",
                buildid=f"2026052{i}093015",
                locales=["en-US"],
            )
        )

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&after_buildid=20260522093015")
        assert response.status_code == 200
        results = response.json()
        assert [r["buildid"] for r in results] == ["20260524093015", "20260523093015"]


def test_list_nightly_releases_filter_by_before_buildid(app):
    for i in range(5):
        db.session.add(
            NightlyRelease(
                product="firefox",
                channel="nightly",
                version="140.0a1",
                buildid=f"2026052{i}093015",
                locales=["en-US"],
            )
        )

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&before_buildid=20260522093015")
        assert response.status_code == 200
        results = response.json()
        assert [r["buildid"] for r in results] == ["20260521093015", "20260520093015"]


def test_list_nightly_releases_paging_before_buildid(app):
    for i in range(5):
        db.session.add(
            NightlyRelease(
                product="firefox",
                channel="nightly",
                version="140.0a1",
                buildid=f"2026052{i}093015",
                locales=["en-US"],
            )
        )

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&limit=2")
        assert response.status_code == 200
        page1 = response.json()
        buildids = [r["buildid"] for r in page1]
        assert buildids == ["20260524093015", "20260523093015"]

        next_max = buildids[-1]
        response = client.get(f"/nightly-release?product=firefox&channel=nightly&limit=2&before_buildid={next_max}")
        assert response.status_code == 200
        page2 = response.json()
        buildids = [r["buildid"] for r in page2]
        assert buildids == ["20260522093015", "20260521093015"]

        next_max = buildids[-1]
        response = client.get(f"/nightly-release?product=firefox&channel=nightly&limit=2&before_buildid={next_max}")
        assert response.status_code == 200
        page3 = response.json()
        buildids = [r["buildid"] for r in page3]
        assert buildids == ["20260520093015"]

        next_max = buildids[-1]
        response = client.get(f"/nightly-release?product=firefox&channel=nightly&limit=2&before_buildid={next_max}")
        assert response.status_code == 200
        assert response.json() == []


def test_list_nightly_releases_paging_after_buildid(app):
    for i in range(5):
        db.session.add(
            NightlyRelease(
                product="firefox",
                channel="nightly",
                version="140.0a1",
                buildid=f"2026052{i}093015",
                locales=["en-US"],
            )
        )

    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&limit=2&order=asc")
        assert response.status_code == 200
        page1 = response.json()
        buildids = [r["buildid"] for r in page1]
        assert buildids == ["20260520093015", "20260521093015"]

        next_max = buildids[-1]
        response = client.get(f"/nightly-release?product=firefox&channel=nightly&limit=2&order=asc&after_buildid={next_max}")
        assert response.status_code == 200
        page2 = response.json()
        buildids = [r["buildid"] for r in page2]
        assert buildids == ["20260522093015", "20260523093015"]

        next_max = buildids[-1]
        response = client.get(f"/nightly-release?product=firefox&channel=nightly&limit=2&order=asc&after_buildid={next_max}")
        assert response.status_code == 200
        page3 = response.json()
        buildids = [r["buildid"] for r in page3]
        assert buildids == ["20260524093015"]

        next_max = buildids[-1]
        response = client.get(f"/nightly-release?product=firefox&channel=nightly&limit=2&order=asc&after_buildid={next_max}")
        assert response.status_code == 200
        assert response.json() == []


def test_list_nightly_releases_limit_above_max_rejected(app):
    with app.test_client() as client:
        response = client.get("/nightly-release?product=firefox&channel=nightly&limit=501")
        assert response.status_code == 400
