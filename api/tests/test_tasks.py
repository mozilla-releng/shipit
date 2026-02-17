from contextlib import nullcontext as does_not_raise
from unittest import mock

import pytest
import taskcluster

from shipit_api.admin import tasks


@pytest.mark.parametrize(
    "avail_flavors, product, version, partial_updates, product_key, expectation, result",
    (
        (
            ["promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0.1",
            None,
            "firefox",
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (["some-flavor"], "non-existing-product", "1.0", None, None, pytest.raises(tasks.UnsupportedFlavor), None),
        (
            ["promote_firefox", "push_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["extra_flavor", "promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["promote_thunderbird", "push_thunderbird", "ship_thunderbird"],
            "thunderbird",
            "129.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_thunderbird", "in_previous_graph_ids": True},
                {"name": "push_thunderbird", "in_previous_graph_ids": True},
                {"name": "ship_thunderbird", "in_previous_graph_ids": True},
            ],
        ),
    ),
)
def test_extract_our_flavors(avail_flavors, product, version, partial_updates, product_key, expectation, result):
    with expectation:
        assert tasks.extract_our_flavors(avail_flavors, product, version, partial_updates, product_key) == result


def test_extract_our_flavors_unsupported_flavor():
    # This error is only raised when someone adds a new product in
    # release._VERSION_CLASS_PER_PRODUCT but forgets to add that
    # new product in config.SUPPORTED_FLAVORS.
    flavors_without_firefox = {k: v for k, v in tasks.SUPPORTED_FLAVORS.items() if k != "firefox"}
    with mock.patch.dict(tasks.SUPPORTED_FLAVORS, flavors_without_firefox, clear=True):
        with pytest.raises(tasks.UnsupportedFlavor):
            tasks.extract_our_flavors([], "firefox", "100.0.1", None)


@pytest.mark.parametrize(
    "avail_flavors, expected_records, expected_text",
    (
        (["promote_firefox", "push_firefox", "ship_firefox"], 0, None),
        (["promote_firefox", "push_firefox"], 1, "Some hardcoded flavors are not in actions.json: {'ship_firefox'}. Product: firefox. Version: 100.0.1"),
        (
            ["extra_flavor", "promote_firefox", "push_firefox", "ship_firefox"],
            1,
            "Some flavors in actions.json are not hardcoded in shipit: {'extra_flavor'}. Product: firefox. Version: 100.0.1",
        ),
    ),
)
def test_extract_our_flavors_warnings(caplog, avail_flavors, expected_records, expected_text):
    tasks.extract_our_flavors(avail_flavors, "firefox", "100.0.1", None)

    assert len(caplog.records) == expected_records
    if expected_records > 0:
        assert caplog.records[0].levelname == "WARNING"
        assert expected_text in caplog.text


@pytest.mark.parametrize(
    "repo_url, product, expectation, trust_domain",
    (
        ("https://hg.mozilla.org/try", "firefox-android", does_not_raise(), "gecko"),
        ("https://hg.mozilla.org/try", "firefox", does_not_raise(), "gecko"),
        ("https://hg.mozilla.org/releases/mozilla-beta", "firefox-android", does_not_raise(), "gecko"),
        ("https://hg.mozilla.org/mozilla-central", "firefox-android", does_not_raise(), "gecko"),
        ("https://hg.mozilla.org/try-comm-central", "firefox-android", does_not_raise(), "comm"),
        ("https://hg.mozilla.org/try-comm-central", "thunderbird", does_not_raise(), "comm"),
        ("", "xpi", does_not_raise(), "xpi"),
        ("https://github.com/mozilla-mobile/firefox-android", "firefox", does_not_raise(), "mobile"),
        ("https://github.com/mozilla-mobile/firefox-android", "firefox-android", does_not_raise(), "mobile"),
        ("https://github.com/mozilla-releng/staging-firefox-android", "firefox-android", does_not_raise(), "mobile"),
        ("https://github.com/mozilla-mobile/mozilla-vpn-client", "firefox-android", does_not_raise(), "mozillavpn"),
    ),
)
def test_get_trust_domain(repo_url, product, expectation, trust_domain):
    with expectation:
        assert tasks.get_trust_domain(repo_url, product) == trust_domain


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            {
                "actions": {"actions": [{"name": "cancel-all", "hookGroupId": "hg", "hookId": "hi", "hookPayload": {"decision": {"parameters": {}}}}]},
                "parameters": {"test": "params"},
                "raise_artifact_error": False,
                "expect_cancel": True,
                "expect_trigger": True,
                "expect_seal": True,
            },
            id="happy-path",
        ),
        pytest.param(
            {
                "actions": None,
                "parameters": None,
                "raise_artifact_error": True,
                "expect_cancel": True,
                "expect_trigger": False,
                "expect_seal": False,
            },
            id="artifact-not-found",
        ),
        pytest.param(
            {
                "actions": {"actions": [{"name": "other-action", "hookGroupId": "hg", "hookId": "hi", "hookPayload": {}}]},
                "parameters": {"test": "params"},
                "raise_artifact_error": False,
                "expect_cancel": True,
                "expect_trigger": False,
                "expect_seal": False,
            },
            id="no-cancel-all-action",
        ),
    ],
)
def test_cancel_action_task_group(app, test_case):
    tc_options = {"rootUrl": "https://taskcluster.example.com", "credentials": {"clientId": "client-id", "accessToken": "access-token"}}
    real_queue = taskcluster.Queue(tc_options)
    real_hooks = taskcluster.Hooks(tc_options)

    mocked_queue = mock.Mock(wraps=real_queue)
    mocked_queue.cancelTask = mock.Mock()
    mocked_queue.sealTaskGroup = mock.Mock()

    mocked_hooks = mock.Mock(wraps=real_hooks)
    mocked_hooks.options = real_hooks.options
    mocked_hooks.triggerHook.return_value = {"status": {"taskId": "triggered-task-id"}}

    def mocked_get_service(name, **kwargs):
        if name == "queue":
            return mocked_queue
        elif name == "hooks":
            return mocked_hooks
        assert False, "cancel_action tried to access an unexpected tc service"

    if test_case["raise_artifact_error"]:
        mock_get_actions = mock.Mock(side_effect=tasks.ArtifactNotFound)
    else:
        mock_get_actions = mock.Mock(return_value=test_case["actions"])

    with (
        mock.patch("shipit_api.admin.tasks.get_service", mocked_get_service),
        mock.patch("shipit_api.admin.tasks.get_actions", mock_get_actions),
        mock.patch("shipit_api.admin.tasks.get_parameters", return_value=test_case["parameters"]),
    ):

        tasks.cancel_action_task_group("abc")

        if test_case["expect_cancel"]:
            mocked_queue.cancelTask.assert_called_once_with("abc")
        else:
            mocked_queue.cancelTask.assert_not_called()

        if test_case["expect_trigger"]:
            mocked_hooks.triggerHook.assert_called_once()
        else:
            mocked_hooks.triggerHook.assert_not_called()

        if test_case["expect_seal"]:
            mocked_queue.sealTaskGroup.assert_called_once_with("abc")
        else:
            mocked_queue.sealTaskGroup.assert_not_called()
