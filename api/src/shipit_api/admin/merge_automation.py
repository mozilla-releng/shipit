import datetime
import logging

from flask import abort, request
from flask_login import current_user
from taskcluster.exceptions import TaskclusterRestFailure

from backend_common.db import db
from backend_common.taskcluster import get_service
from shipit_api.admin.tasks import (
    cancel_action_task_group,
    fetch_group_tasks,
    find_action,
    find_decision_task_id,
    get_actions,
    get_parameters,
    render_action_hook,
)
from shipit_api.common.config import MERGE_BEHAVIORS_PER_PRODUCT, SCOPE_PREFIX
from shipit_api.common.models import MergeAutomation, TaskStatus

logger = logging.getLogger(__name__)


def list_products():
    return list(MERGE_BEHAVIORS_PER_PRODUCT.keys())


def get_behavior_for_product(product, behavior_name):
    if product not in MERGE_BEHAVIORS_PER_PRODUCT:
        abort(404, f"No merge behavior found for product: {product}")

    behavior = next((b for b in MERGE_BEHAVIORS_PER_PRODUCT[product] if b["behavior"] == behavior_name), None)
    if not behavior:
        abort(404, f"Behavior {behavior_name} not found for product: {product}")

    return behavior


def list_behaviors(product):
    if product not in MERGE_BEHAVIORS_PER_PRODUCT:
        abort(404, f"No merge behavior found for product: {product}")

    return MERGE_BEHAVIORS_PER_PRODUCT[product]


def submit_merge_automation():
    body = request.get_json()
    product = body["product"]

    required_permission = f"{SCOPE_PREFIX}/add_merge_automation/{product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    behavior_name = body["behavior"]
    revision = body["revision"]
    dry_run = body.get("dryRun", True)
    version = body["version"]
    commit_message = body["commitMessage"]
    commit_author = body["commitAuthor"]

    behavior = get_behavior_for_product(product, behavior_name)

    automation = MergeAutomation(
        product=product,
        behavior=behavior_name,
        revision=revision,
        version=version,
        dry_run=dry_run,
        commit_message=commit_message,
        commit_author=commit_author,
        repo=behavior["repo"],
        pretty_name=behavior["pretty_name"],
        project=behavior["project"],
    )

    db.session.add(automation)
    db.session.commit()

    return {"message": "Merge automation created successfully"}, 201


def list_merge_automation(product):
    merge_automations = (
        MergeAutomation.query.filter_by(product=product)
        .filter(MergeAutomation.status != TaskStatus.Canceled)
        .order_by(db.case((MergeAutomation.status == TaskStatus.Completed, 1), else_=0), MergeAutomation.created.desc())
        .limit(20)
        .all()
    )

    return [automation.json for automation in merge_automations]


def cancel_merge_automation(automation_id):
    automation = db.session.get(MergeAutomation, automation_id)
    if not automation:
        return abort(404, f"Merge automation with id {automation_id} not found")

    required_permission = f"{SCOPE_PREFIX}/cancel_merge_automation/{automation.product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    logger.info(f"Cancelling merge automation with id {automation_id}")
    if automation.task_id:
        try:
            cancel_action_task_group(automation.task_id)
        except TaskclusterRestFailure as e:
            abort(500, str(e))

    automation.status = TaskStatus.Canceled
    db.session.commit()

    return automation.json


def mark_merge_automation_completed(automation_id):
    automation = db.session.get(MergeAutomation, automation_id, with_for_update=True)
    if not automation:
        return abort(404, f"Merge automation with id {automation_id} not found")

    required_permission = f"{SCOPE_PREFIX}/mark_merge_automation_completed/{automation.product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    if automation.status in (TaskStatus.Completed, TaskStatus.Canceled):
        return abort(409, f"Cannot update automation in {automation.status.name} status")

    automation.status = TaskStatus.Completed
    automation.completed = datetime.datetime.now(datetime.UTC)

    db.session.commit()
    logger.info(f"Merge automation {automation_id} marked as completed")

    return automation.json


def start_merge_automation(automation_id):
    automation = db.session.get(MergeAutomation, automation_id, with_for_update=True)
    if not automation:
        return abort(404, f"Merge automation with id {automation_id} not found")

    # Check permissions
    required_permission = f"{SCOPE_PREFIX}/add_merge_automation/{automation.product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    if automation.status != TaskStatus.Pending:
        return abort(409, f"Cannot start automation in {automation.status.name} status")

    try:
        task_id = trigger_merge_automation_action(automation)
        automation.task_id = task_id
        automation.status = TaskStatus.Running
        db.session.commit()

        logger.info(f"Started merge automation {automation.id} with task {task_id}")
        return {"message": "Merge automation started successfully", "task_id": task_id}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to start merge automation {automation.id}: {e}")
        return abort(500, f"Failed to start merge automation: {str(e)}")


def trigger_merge_automation_action(automation):
    decision_task_id = find_decision_task_id(automation.repo, automation.project, automation.revision, automation.product)
    actions = get_actions(decision_task_id)

    merge_action = find_action("merge-automation", actions)
    if not merge_action:
        raise ValueError("merge-automation action not found in decision task")

    action_input = {
        "behavior": automation.behavior,
        "force-dry-run": automation.dry_run,
        "merge-automation-id": automation.id,
    }

    hooks = get_service("hooks")
    client_id = hooks.options["credentials"]["clientId"].decode("utf-8")

    parameters = get_parameters(decision_task_id)

    context = {
        "parameters": parameters,
        "taskGroupId": decision_task_id,
        "taskId": None,
        "task": None,
        "input": action_input,
        "clientId": client_id,
    }

    hook_payload_rendered = render_action_hook(payload=merge_action["hookPayload"], context=context)

    try:
        result = hooks.triggerHook(
            merge_action["hookGroupId"],
            merge_action["hookId"],
            hook_payload_rendered,
        )
    except TaskclusterRestFailure as e:
        abort(500, str(e))

    task_id = result["status"]["taskId"]
    logger.info(f"Triggered merge automation action, task ID: {task_id}")
    return task_id


def get_task_status(task_id):
    queue = get_service("queue")
    task_status = queue.status(task_id)
    return {
        "taskId": task_id,
        "state": task_status["status"]["state"],
    }


def get_task_group_status(task_group_id):
    try:
        tasks = fetch_group_tasks(task_group_id)
    except TaskclusterRestFailure as e:
        if e.status_code == 404:
            return TaskStatus.Pending
        raise

    group_status = TaskStatus.Completed
    for task in tasks:
        state = task["status"]["state"]

        if state in ("failed", "exception"):
            group_status = TaskStatus.Failed
            break

        if state in ("running", "pending", "unscheduled"):
            group_status = TaskStatus.Running

    return group_status


def get_merge_automation_task_status(automation_id):
    automation = db.session.get(MergeAutomation, automation_id)
    if not automation or not automation.task_id:
        return abort(404, "Automation not found or no task ID")

    if automation.status in (TaskStatus.Completed, TaskStatus.Canceled):
        return {
            "automation": automation.json,
            "decisionTask": {"taskId": automation.task_id, "state": automation.status.name.lower()},
            "taskGroup": {"overallStatus": automation.status.name.lower()},
        }

    decision_task_status = get_task_status(automation.task_id)

    if decision_task_status["state"] == "completed":
        overall_status = get_task_group_status(automation.task_id)
    else:
        overall_status = TaskStatus.Pending

    return {
        "automation": automation.json,
        "decisionTask": decision_task_status,
        "taskGroup": {"overallStatus": overall_status.name.lower()},
    }
