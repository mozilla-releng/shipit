from contextlib import nullcontext as does_not_raise
from copy import deepcopy

import pytest

from shipit_api.admin import tasks


@pytest.mark.parametrize(
    "avail_flavors, product, version, partial_updates, product_key, expectation, result",
    (
        (
            ["promote_firefox", "promote_firefox_rc", "push_firefox", "ship_firefox", "ship_firefox_rc"],
            "firefox",
            "100.0",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox_rc", "in_previous_graph_ids": True},
                {"name": "ship_firefox_rc", "in_previous_graph_ids": False},
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
        (["some-flavor"], "non-existing-product", "1.0", None, None, pytest.raises(ValueError), None),
        (
            ["promote_firefox", "push_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            pytest.raises(tasks.UnsupportedFlavor),
            None,
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
    ),
)
def test_extract_our_flavors(avail_flavors, product, version, partial_updates, product_key, expectation, result):
    with expectation:
        assert tasks.extract_our_flavors(avail_flavors, product, version, partial_updates, product_key) == result


def test_extract_our_flavors_unsupported_flavor():
    # This error is only raised when someone adds a new product in
    # release._VERSION_CLASS_PER_PRODUCT but forgets to add that
    # new product in config.SUPPORTED_FLAVORS.
    supported_flavors = deepcopy(tasks.SUPPORTED_FLAVORS)

    del tasks.SUPPORTED_FLAVORS["firefox"]
    with pytest.raises(tasks.UnsupportedFlavor):
        tasks.extract_our_flavors([], "firefox", "100.0.1", None)

    tasks.SUPPORTED_FLAVORS = supported_flavors
