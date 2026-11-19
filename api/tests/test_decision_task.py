from unittest import mock

import pytest

from shipit_api.admin.api import check_decision_task

BODY = {
    "product": "firefox",
    "branch": "releases/mozilla-beta",
    "revision": "a3177e0ca15650169d489b4823603674d32d3d34",
    "repo_url": "https://hg.mozilla.org/releases/mozilla-beta",
}


@mock.patch("shipit_api.admin.api.get_parameters")
@mock.patch("shipit_api.admin.api.find_decision_task_id", side_effect=Exception("not found"))
def test_check_decision_task_missing(mock_find, mock_get_parameters):
    assert check_decision_task(BODY) == {"state": "missing"}
    mock_find.assert_called_once_with(BODY["repo_url"], "mozilla-beta", BODY["revision"], "firefox")
    mock_get_parameters.assert_not_called()


@pytest.mark.parametrize(
    "parameters, expected_version",
    (
        ({"version": "161.0b6", "app_version": "161.0"}, "161.0b6"),
        ({"version": "140.17.1esr"}, "140.17.1esr"),
        # Projects that don't compute a version
        ({"version": ""}, None),
        ({"version": None}, None),
        ({}, None),
        # Unquoted YAML numbers are not trusted
        ({"version": 161.1}, None),
    ),
)
@mock.patch("shipit_api.admin.api.find_decision_task_id", return_value="W6KoVlg7SoyyYl7e_JhK9g")
def test_check_decision_task_ready(mock_find, parameters, expected_version):
    with mock.patch("shipit_api.admin.api.get_parameters", return_value=parameters) as mock_get_parameters:
        result = check_decision_task(BODY)
    mock_get_parameters.assert_called_once_with("W6KoVlg7SoyyYl7e_JhK9g")
    expected = {"task_id": "W6KoVlg7SoyyYl7e_JhK9g", "state": "ready"}
    if expected_version is not None:
        expected["version"] = expected_version
    assert result == expected


@mock.patch("shipit_api.admin.api.get_parameters", side_effect=Exception("artifact not found"))
@mock.patch("shipit_api.admin.api.find_decision_task_id", return_value="W6KoVlg7SoyyYl7e_JhK9g")
def test_check_decision_task_parameters_unavailable(mock_find, mock_get_parameters):
    # Still ready: the decision task exists, we just can't tell the version
    assert check_decision_task(BODY) == {"task_id": "W6KoVlg7SoyyYl7e_JhK9g", "state": "ready"}
