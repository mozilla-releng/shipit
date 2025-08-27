import pytest

from shipit_api.common.models import Version


@pytest.mark.parametrize(
    "product,channel,expected_version",
    (
        pytest.param("firefox", "nightly", "42.0.1"),
        pytest.param("foo", "bar", "77.7.7"),
        pytest.param("bar", "foo", None),
        pytest.param("firefox", "beta", None),
    ),
)
def test_versions(app, product, channel, expected_version):
    session = app.app.db.session
    version1 = Version(
        product_name="firefox",
        product_channel="nightly",
        current_version="42.0.1",
    )
    version2 = Version(
        product_name="foo",
        product_channel="bar",
        current_version="77.7.7",
    )
    session.add_all([version1, version2])
    session.commit()

    with app.test_client() as client:
        response = client.get(f"/versions/{product}/{channel}")
        assert response.headers["content-type"] == "application/json"
        if expected_version is not None:
            assert response.status_code == 200
            assert response.json() == expected_version
        else:
            assert response.status_code == 404
            assert response.json()["error"] == f"No version found for {product} {channel}."
