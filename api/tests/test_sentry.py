from unittest.mock import Mock

import pytest
import sentry_sdk
from flask import abort
from starlette.testclient import TestClient

from backend_common.log import configure_sentry


@pytest.fixture
def sentry_events():
    events = []

    def capture_event(event, hint=None):
        events.append(event)

    # Initialize Sentry with a real client (not NonRecordingClient) using a fake DSN
    # and a mock transport so we can capture events
    configure_sentry("test", "https://fake@fake.ingest.sentry.io/123456")
    new_client = sentry_sdk.get_client()

    def mock_transport(envelope):
        for item in envelope.items:
            capture_event(item.payload.json)

    new_client.transport = Mock()
    new_client.transport.capture_envelope = mock_transport

    yield events, capture_event


@pytest.mark.parametrize(
    "status_code,expected_captured",
    [
        (400, False),
        (401, False),
        (403, False),
        (404, False),
        (409, False),
        (500, True),
    ],
)
def test_sentry_captures_only_5xx_errors(app, sentry_events, status_code, expected_captured):
    events, capture_event = sentry_events

    # Reset first request flag. This is a hacky way to be able to register routes after the app has already started
    app.app._got_first_request = False

    def make_test_route(code):
        def test_route():
            if code >= 500:
                raise RuntimeError("500 error")
            abort(code, f"Test {code} error")

        return test_route

    app.app.add_url_rule(
        f"/test_status_{status_code}",
        f"test_route_{status_code}",
        make_test_route(status_code),
    )

    client = TestClient(app)

    response = client.get(f"/test_status_{status_code}")
    assert response.status_code == status_code
    sentry_sdk.flush(timeout=1)

    exception_events = [e for e in events if e.get("exception")]

    if expected_captured:
        assert len(exception_events) > 0, f"Expected {status_code} errors to be captured by sentry"
    else:
        assert len(exception_events) == 0, f"Unexpected {status_code} error captured by sentry"
