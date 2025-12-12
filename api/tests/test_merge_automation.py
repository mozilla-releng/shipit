from unittest.mock import Mock, patch

import pytest

from backend_common.db import db
from shipit_api.admin.merge_automation import (
    get_task_group_status,
    get_task_status,
    trigger_merge_automation_action,
)
from shipit_api.common.models import MergeAutomation, TaskStatus


def create_merge_automation_with_defaults(**kwargs):
    defaults = {
        "repo": "https://hg.mozilla.org/try",
        "pretty_name": "Main -> beta",
        "project": "try",
    }
    defaults.update(kwargs)
    return MergeAutomation(**defaults)


@pytest.mark.parametrize(
    "product,expected_error",
    (
        pytest.param("firefox", False),
        pytest.param("thunderbird", True),
    ),
)
def test_list_behaviors(app, product, expected_error):
    with app.test_client() as client:
        response = client.get(f"/merge-automation/behaviors/{product}")
        if expected_error:
            assert response.status_code == 404
            return

        assert response.status_code == 200

        def assert_key_is(key, ty, obj):
            assert key in obj and isinstance(obj[key], ty)

        for name, behavior in response.json().items():
            assert_key_is("repo", str, behavior)
            assert_key_is("pretty_name", str, behavior)
            assert_key_is("always-target-tip", bool, behavior)


def test_list_merge_automation_no_data(app):
    with app.test_client() as client:
        response = client.get("/merge-automation?product=firefox")
        assert response.status_code == 200
        assert response.json() == []

    with app.test_client() as client:
        response = client.get("/merge-automation?product=thunderbird")
        assert response.status_code == 404
        assert response.json()["detail"] == "No merge behavior found for product: thunderbird"


def test_list_merge_automation_with_data(app):
    automation1 = create_merge_automation_with_defaults(
        product="firefox", behavior="main-to-beta", revision="abc123", version="130.0", status=TaskStatus.Pending, dry_run=True
    )
    automation2 = create_merge_automation_with_defaults(
        product="firefox", behavior="main-to-beta", revision="ghi789", version="128.0", status=TaskStatus.Completed, dry_run=False
    )
    automation3 = create_merge_automation_with_defaults(
        product="firefox",
        behavior="beta-to-release",
        revision="def456",
        version="129.0",
        status=TaskStatus.Running,
        dry_run=False,
        repo="https://hg.mozilla.org/releases/mozilla-beta",
        pretty_name="Beta -> release",
        project="mozilla-beta",
    )

    db.session.add(automation1)
    db.session.add(automation2)
    db.session.add(automation3)
    db.session.commit()

    with app.test_client() as client:
        response = client.get("/merge-automation?product=firefox")
        assert response.status_code == 200

        expected = [
            {
                "id": automation3.id,
                "product": "firefox",
                "behavior": "beta-to-release",
                "pretty_name": "Beta -> release",
                "revision": "def456",
                "version": "129.0",
                "repo": "https://hg.mozilla.org/releases/mozilla-beta",
                "status": "running",
                "created": automation3.created.isoformat(),
                "completed": None,
                "task_id": None,
                "dry_run": False,
                "commit_message": None,
                "commit_author": None,
            },
            {
                "id": automation1.id,
                "product": "firefox",
                "behavior": "main-to-beta",
                "pretty_name": "Main -> beta",
                "revision": "abc123",
                "version": "130.0",
                "repo": "https://hg.mozilla.org/try",
                "status": "pending",
                "created": automation1.created.isoformat(),
                "completed": None,
                "task_id": None,
                "dry_run": True,
                "commit_message": None,
                "commit_author": None,
            },
            {
                "id": automation2.id,
                "product": "firefox",
                "behavior": "main-to-beta",
                "pretty_name": "Main -> beta",
                "revision": "ghi789",
                "version": "128.0",
                "repo": "https://hg.mozilla.org/try",
                "status": "completed",
                "created": automation2.created.isoformat(),
                "completed": None,
                "task_id": None,
                "dry_run": False,
                "commit_message": None,
                "commit_author": None,
            },
        ]

        assert response.json() == expected


@patch("shipit_api.admin.merge_automation.current_user")
def test_submit_merge_automation_success(mock_user, app):
    mock_user.has_permissions.return_value = True

    with app.test_client() as client:
        payload = {
            "product": "firefox",
            "behavior": "main-to-beta",
            "revision": "abc123",
            "dryRun": True,
            "version": "130.0",
            "commitMessage": "Test commit message",
            "commitAuthor": "test@example.com",
        }

        response = client.post("/merge-automation", json=payload)
        assert response.status_code == 201
        assert response.json() == {"message": "Merge automation created successfully"}

        mock_user.has_permissions.assert_called_once_with("project:releng:services/shipit_api/add_merge_automation/firefox")


@pytest.mark.parametrize(
    "product,behavior,expected_error_message",
    [
        ("thunderbird", "main-to-beta", None),
        ("firefox", "invalid-behavior", "Behavior invalid-behavior not found for product: firefox"),
    ],
)
@patch("shipit_api.admin.merge_automation.current_user")
def test_submit_merge_automation_invalid_inputs(mock_user, app, product, behavior, expected_error_message):
    mock_user.has_permissions.return_value = True

    with app.test_client() as client:
        payload = {
            "product": product,
            "behavior": behavior,
            "revision": "abc123",
            "dryRun": True,
            "version": "130.0",
            "commitMessage": "Test commit",
            "commitAuthor": "test@example.com",
        }

        response = client.post("/merge-automation", json=payload)
        assert response.status_code == 404

        if expected_error_message:
            assert response.json()["detail"] == expected_error_message


@patch("shipit_api.admin.merge_automation.current_user")
@patch("shipit_api.admin.merge_automation.cancel_action_task_group")
def test_cancel_merge_automation_success(mock_cancel, mock_user, app):
    mock_user.has_permissions.return_value = True
    automation = create_merge_automation_with_defaults(
        product="firefox", behavior="main-to-beta", revision="abc123", version="130.0", status=TaskStatus.Pending, dry_run=True
    )
    db.session.add(automation)
    db.session.commit()
    automation_id = automation.id

    with app.test_client() as client:
        response = client.delete(f"/merge-automation/{automation_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "canceled"

        canceled_automation = db.session.get(MergeAutomation, automation_id)
        assert canceled_automation is not None
        assert canceled_automation.status == TaskStatus.Canceled


@patch("shipit_api.admin.merge_automation.current_user")
@patch("shipit_api.admin.merge_automation.cancel_action_task_group")
def test_cancel_merge_automation_with_taskcluster_task(mock_cancel, mock_user, app):
    mock_user.has_permissions.return_value = True
    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Running,
        task_id="fakeTaskId",
        dry_run=False,
    )
    db.session.add(automation)
    db.session.commit()
    automation_id = automation.id

    with app.test_client() as client:
        response = client.delete(f"/merge-automation/{automation_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "canceled"

        canceled_automation = db.session.get(MergeAutomation, automation_id)
        assert canceled_automation is not None
        assert canceled_automation.status == TaskStatus.Canceled

        mock_cancel.assert_called_once_with("fakeTaskId")


def test_cancel_merge_automation_not_found(app):
    with app.test_client() as client:
        response = client.delete("/merge-automation/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Merge automation with id 999 not found"


@patch("shipit_api.admin.merge_automation.current_user")
@patch("shipit_api.admin.merge_automation.cancel_action_task_group")
def test_cancel_merge_automation_failed_status(mock_cancel, mock_user, app):
    mock_user.has_permissions.return_value = True
    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Failed,
        task_id="fakeTaskId",
        dry_run=False,
    )
    db.session.add(automation)
    db.session.commit()
    automation_id = automation.id

    with app.test_client() as client:
        response = client.delete(f"/merge-automation/{automation_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "canceled"

        canceled_automation = db.session.get(MergeAutomation, automation_id)
        assert canceled_automation is not None
        assert canceled_automation.status == TaskStatus.Canceled


@patch("shipit_api.admin.merge_automation.current_user")
@patch("shipit_api.admin.merge_automation.trigger_merge_automation_action")
def test_start_merge_automation_success(mock_trigger, mock_user, app):
    mock_user.has_permissions.return_value = True
    mock_trigger.return_value = "fakeTaskId"

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        dry_run=True,
        commit_message="Test commit",
        commit_author="test@example.com",
    )
    db.session.add(automation)
    db.session.commit()

    with app.test_client() as client:
        response = client.post(f"/merge-automation/{automation.id}/start")
        assert response.status_code == 200
        assert response.json() == {"message": "Merge automation started successfully", "task_id": "fakeTaskId"}

        updated_automation = db.session.get(MergeAutomation, automation.id)
        assert updated_automation.status == TaskStatus.Running
        assert updated_automation.task_id == "fakeTaskId"

        mock_trigger.assert_called_once_with(automation)


@pytest.mark.parametrize(
    "automation_id,automation_status,expected_status_code,expected_error",
    [
        (999, None, 404, "Merge automation with id 999 not found"),
        (None, TaskStatus.Running, 400, "Cannot start automation in Running status"),
    ],
)
@patch("shipit_api.admin.merge_automation.current_user")
def test_start_merge_automation_error_cases(mock_user, app, automation_id, automation_status, expected_status_code, expected_error):
    mock_user.has_permissions.return_value = True

    if automation_status is not None:
        automation = create_merge_automation_with_defaults(
            product="firefox",
            behavior="main-to-beta",
            revision="abc123",
            version="130.0",
            status=automation_status,
            dry_run=True,
            commit_message="Test commit",
            commit_author="test@example.com",
        )
        db.session.add(automation)
        db.session.commit()
        automation_id = automation.id

    with app.test_client() as client:
        response = client.post(f"/merge-automation/{automation_id}/start")
        assert response.status_code == expected_status_code
        assert response.json()["detail"] == expected_error


@patch("shipit_api.admin.merge_automation.current_user")
@patch("shipit_api.admin.merge_automation.trigger_merge_automation_action")
def test_start_merge_automation_taskcluster_failure(mock_trigger, mock_user, app):
    mock_user.has_permissions.return_value = True
    mock_trigger.side_effect = Exception("taskcluster error")

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        dry_run=True,
        commit_message="Test commit",
        commit_author="test@example.com",
    )
    db.session.add(automation)
    db.session.commit()

    with app.test_client() as client:
        response = client.post(f"/merge-automation/{automation.id}/start")
        assert response.status_code == 500
        assert "Failed to start merge automation: taskcluster error" in response.json()["detail"]

        updated_automation = db.session.get(MergeAutomation, automation.id)
        assert updated_automation.status == TaskStatus.Pending
        assert updated_automation.task_id is None


@patch("shipit_api.admin.merge_automation.get_service")
@patch("shipit_api.admin.merge_automation.find_decision_task_id")
@patch("shipit_api.admin.merge_automation.get_actions")
@patch("shipit_api.admin.merge_automation.get_parameters")
@patch("shipit_api.admin.merge_automation.render_action_hook")
def test_trigger_merge_automation_action_hook_payload(mock_render_hook, mock_get_parameters, mock_get_actions, mock_find_decision, mock_get_service, app):
    mock_decision_task_id = "fakeTaskId"
    mock_find_decision.return_value = mock_decision_task_id

    mock_actions = {
        "actions": [
            {"name": "wrongaction", "hookGroupId": "test-group", "hookId": "test-hook", "hookPayload": {"some": "payload"}},
            {"name": "merge-automation", "hookGroupId": "test-group", "hookId": "test-hook", "hookPayload": {"some": "payload"}},
        ]
    }
    mock_get_actions.return_value = mock_actions

    mock_parameters = {"parameter1": "value1"}
    mock_get_parameters.return_value = mock_parameters

    mock_rendered_payload = {"rendered": "payload"}
    mock_render_hook.return_value = mock_rendered_payload

    mock_hooks_service = Mock()
    mock_hooks_service.options = {"credentials": {"clientId": b"test-client"}}
    mock_hooks_service.triggerHook.return_value = {"status": {"taskId": "fakeResultTaskId"}}
    mock_get_service.return_value = mock_hooks_service

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        dry_run=True,
    )

    result = trigger_merge_automation_action(automation)
    mock_find_decision.assert_called_once_with("https://hg.mozilla.org/try", "try", "abc123", "firefox")

    mock_get_actions.assert_called_once_with(mock_decision_task_id)
    mock_get_parameters.assert_called_once_with(mock_decision_task_id)

    expected_context = {
        "parameters": mock_parameters,
        "taskGroupId": mock_decision_task_id,
        "taskId": None,
        "task": None,
        "input": {
            "behavior": "main-to-beta",
            "force-dry-run": True,
        },
        "clientId": "test-client",
    }
    mock_render_hook.assert_called_once_with(payload={"some": "payload"}, context=expected_context)

    mock_hooks_service.triggerHook.assert_called_once_with("test-group", "test-hook", mock_rendered_payload)

    assert result == "fakeResultTaskId"


@patch("shipit_api.admin.merge_automation.get_service")
@patch("shipit_api.admin.merge_automation.find_decision_task_id")
@patch("shipit_api.admin.merge_automation.get_actions")
def test_trigger_merge_automation_action_missing_action(mock_get_actions, mock_find_decision, mock_get_service, app):
    mock_find_decision.return_value = "decision-task-123"
    mock_get_actions.return_value = {"actions": [{"name": "other-action"}]}

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        dry_run=True,
    )

    with pytest.raises(ValueError, match="merge-automation action not found in decision task"):
        trigger_merge_automation_action(automation)


@pytest.mark.parametrize(
    "initial_status,task_states,expected_final_status,expected_completed_set",
    [
        (TaskStatus.Running, ["completed", "completed"], TaskStatus.Completed, True),
        (TaskStatus.Running, ["completed", "failed"], TaskStatus.Failed, False),
        (TaskStatus.Completed, ["completed", "completed"], TaskStatus.Completed, False),
        (TaskStatus.Running, ["running", "completed"], TaskStatus.Running, False),
    ],
)
@patch("shipit_api.admin.merge_automation.get_service")
def test_get_merge_automation_task_status_scenarios(mock_get_service, app, initial_status, task_states, expected_final_status, expected_completed_set):
    mock_queue = Mock()
    mock_queue.status.return_value = {
        "status": {
            "taskId": "fakeTaskId",
            "state": "completed",
        }
    }
    mock_queue.listTaskGroup.return_value = {"tasks": [{"status": {"state": state}} for state in task_states]}
    mock_get_service.return_value = mock_queue

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=initial_status,
        task_id="fakeTaskId",
        dry_run=True,
    )
    db.session.add(automation)
    db.session.commit()
    original_completed = automation.completed

    with app.test_client() as client:
        response = client.get(f"/merge-automation/{automation.id}/task-status")
        assert response.status_code == 200

        data = response.json()
        assert data["automation"]["id"] == automation.id
        assert data["automation"]["status"] == expected_final_status.name.lower()
        assert data["decisionTask"]["taskId"] == "fakeTaskId"
        assert data["taskGroup"]["overallStatus"] == expected_final_status.name.lower()

        updated_automation = db.session.get(MergeAutomation, automation.id)
        assert updated_automation.status == expected_final_status

        if expected_completed_set:
            assert updated_automation.completed is not None
            assert updated_automation.completed != original_completed
        else:
            assert updated_automation.completed == original_completed


def test_get_merge_automation_task_status_not_found(app):
    with app.test_client() as client:
        response = client.get("/merge-automation/999/task-status")
        assert response.status_code == 404
        assert response.json()["detail"] == "Automation not found or no task ID"


def test_get_merge_automation_task_status_no_task_id(app):
    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        task_id=None,
        dry_run=True,
    )
    db.session.add(automation)
    db.session.commit()

    with app.test_client() as client:
        response = client.get(f"/merge-automation/{automation.id}/task-status")
        assert response.status_code == 404
        assert response.json()["detail"] == "Automation not found or no task ID"


@pytest.mark.parametrize(
    "task_id,task_state",
    [
        ("task123", "completed"),
        ("task456", "running"),
    ],
)
@patch("shipit_api.admin.merge_automation.get_service")
def test_get_task_status(mock_get_service, app, task_id, task_state):
    mock_queue = Mock()
    mock_queue.status.return_value = {
        "status": {
            "taskId": task_id,
            "state": task_state,
        }
    }
    mock_get_service.return_value = mock_queue

    result = get_task_status(task_id)

    mock_get_service.assert_called_once_with("queue")
    mock_queue.status.assert_called_once_with(task_id)

    assert result == {
        "taskId": task_id,
        "state": task_state,
    }


@pytest.mark.parametrize(
    "task_group_id,tasks,expected_status",
    [
        (
            "group123",
            [
                {"status": {"state": "completed"}},
                {"status": {"state": "completed"}},
            ],
            TaskStatus.Completed,
        ),
        (
            "group456",
            [
                {"status": {"state": "completed"}},
                {"status": {"state": "failed"}},
                {"status": {"state": "running"}},
            ],
            TaskStatus.Failed,
        ),
        (
            "group789",
            [
                {"status": {"state": "completed"}},
                {"status": {"state": "running"}},
                {"status": {"state": "completed"}},
            ],
            TaskStatus.Running,
        ),
    ],
)
@patch("shipit_api.admin.merge_automation.get_service")
def test_get_task_group_status(mock_get_service, app, task_group_id, tasks, expected_status):
    mock_queue = Mock()
    mock_queue.listTaskGroup.return_value = {"tasks": tasks}
    mock_get_service.return_value = mock_queue

    result = get_task_group_status(task_group_id)

    mock_get_service.assert_called_once_with("queue")
    mock_queue.listTaskGroup.assert_called_once_with(task_group_id)

    assert result == expected_status


# Permission tests
@patch("shipit_api.admin.merge_automation.current_user", new_callable=lambda: Mock())
def test_submit_merge_automation_permission_denied(mock_user, app):
    mock_user.has_permissions = Mock(return_value=False)
    mock_user.get_permissions = Mock(return_value=["some:other:permission"])

    with app.test_client() as client:
        payload = {
            "product": "firefox",
            "behavior": "main-to-beta",
            "revision": "abc123",
            "dryRun": True,
            "version": "130.0",
            "commitMessage": "Test commit",
            "commitAuthor": "test@example.com",
        }

        response = client.post("/merge-automation", json=payload)
        assert response.status_code == 401
        assert "required permission: project:releng:services/shipit_api/add_merge_automation/firefox" in response.json()["detail"]
        assert "user permissions: some:other:permission" in response.json()["detail"]


@patch("shipit_api.admin.merge_automation.current_user", new_callable=lambda: Mock())
def test_start_merge_automation_permission_denied(mock_user, app):
    mock_user.has_permissions = Mock(return_value=False)
    mock_user.get_permissions = Mock(return_value=["some:other:permission"])

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        dry_run=True,
    )
    db.session.add(automation)
    db.session.commit()

    with app.test_client() as client:
        response = client.post(f"/merge-automation/{automation.id}/start")
        assert response.status_code == 401
        assert "required permission: project:releng:services/shipit_api/add_merge_automation/firefox" in response.json()["detail"]
        assert "user permissions: some:other:permission" in response.json()["detail"]


@patch("shipit_api.admin.merge_automation.current_user", new_callable=lambda: Mock())
def test_cancel_merge_automation_permission_denied(mock_user, app):
    mock_user.has_permissions = Mock(return_value=False)
    mock_user.get_permissions = Mock(return_value=["some:other:permission"])

    automation = create_merge_automation_with_defaults(
        product="firefox",
        behavior="main-to-beta",
        revision="abc123",
        version="130.0",
        status=TaskStatus.Pending,
        dry_run=True,
    )
    db.session.add(automation)
    db.session.commit()

    with app.test_client() as client:
        response = client.delete(f"/merge-automation/{automation.id}")
        assert response.status_code == 401
        assert "required permission: project:releng:services/shipit_api/cancel_merge_automation/firefox" in response.json()["detail"]
        assert "user permissions: some:other:permission" in response.json()["detail"]
