import datetime
import logging
from functools import lru_cache

import requests
from flask import abort, request
from flask_login import current_user
from taskcluster.exceptions import TaskclusterRestFailure

from backend_common.db import db
from backend_common.taskcluster import get_service
from shipit_api.admin.tasks import cancel_action_task_group, find_action, find_decision_task_id, get_actions, get_parameters, render_action_hook
from shipit_api.common.config import MERGE_BEHAVIORS_PER_PRODUCT, SCOPE_PREFIX
from shipit_api.common.models import MergeAutomation, TaskStatus

logger = logging.getLogger(__name__)


def get_behavior_for_product(product, behavior_name):
    if product not in MERGE_BEHAVIORS_PER_PRODUCT:
        abort(404, f"No merge behavior found for product: {product}")

    behavior = MERGE_BEHAVIORS_PER_PRODUCT[product].get(behavior_name)
    if not behavior:
        abort(404, f"Behavior {behavior_name} not found for product: {product}")

    return behavior


def list_behaviors(product):
    if product not in MERGE_BEHAVIORS_PER_PRODUCT:
        abort(404, f"No merge behavior found for product: {product}")

    return MERGE_BEHAVIORS_PER_PRODUCT[product]


def revisions_for_behavior(product, behavior_name):
    behavior = get_behavior_for_product(product, behavior_name)

    pushes = get_hg_pushes(behavior["repo"])

    if not behavior.get("always-target-tip", False):
        return pushes

    push = next(iter(pushes.items()))
    return {push[0]: push[1]}


def info_for_behavior_revision(product, behavior_name, revision):
    behavior = get_behavior_for_product(product, behavior_name)

    current_version = get_version_from_hg(behavior["repo"], revision, behavior["version_path"])
    commit_info = get_commit_info_from_hg(behavior["repo"], revision)

    commit_message = commit_info.get("desc", "").split("\n")[0]
    commit_author = commit_info.get("author", "")

    return {
        "version": current_version,
        "commit_message": commit_message,
        "commit_author": commit_author,
    }


def get_hg_pushes(repo):
    url = f"{repo}/json-pushes?version=2&full=1&tipsonly=1&branch=default"

    logger.debug(f"Getting hg pushes from {url}")
    response = requests.get(url)
    response.raise_for_status()
    results = response.json()

    commits = {}
    for push in results["pushes"].values():
        for changeset in push["changesets"]:
            commits[changeset["node"]] = {"date": push["date"], "desc": changeset["desc"], "author": changeset["author"]}

    return commits


@lru_cache(maxsize=20)
def get_commit_info_from_hg(repo_url, revision):
    url = f"{repo_url}/json-log?rev={revision}"

    logger.debug(f"Getting hg pushes commit info from {url}")
    response = requests.get(url)
    response.raise_for_status()
    log_data = response.json()

    commit_data = log_data["entries"][0]
    return {"desc": commit_data["desc"], "author": commit_data["user"], "node": commit_data["node"], "date": commit_data["date"][0]}


@lru_cache(maxsize=20)
def get_version_from_hg(repo_url, revision, version_path):
    url = f"{repo_url}/raw-file/{revision}/{version_path}"
    logger.debug(f"Getting version info from {url}")
    response = requests.get(url)
    response.raise_for_status()
    version = response.text.strip()

    return version


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

    behavior = get_behavior_for_product(product, behavior_name)

    version = get_version_from_hg(behavior["repo"], revision, behavior["version_path"])
    commit_info = get_commit_info_from_hg(behavior["repo"], revision)
    commit_message = commit_info.get("desc", "").split("\n")[0]
    commit_author = commit_info.get("author", "")

    automation = MergeAutomation(
        product=product,
        behavior=behavior_name,
        revision=revision,
        version=version,
        status=TaskStatus.Pending,
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
    if product not in MERGE_BEHAVIORS_PER_PRODUCT:
        return abort(404, f"No merge behavior found for product: {product}")

    merge_automations = (
        MergeAutomation.query.filter_by(product=product)
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
            abort(400, str(e))

    db.session.delete(automation)
    db.session.commit()

    return {"message": "Merge automation deleted successfully"}


def start_merge_automation(automation_id):
    automation = db.session.get(MergeAutomation, automation_id)
    if not automation:
        return abort(404, f"Merge automation with id {automation_id} not found")

    # Check permissions
    required_permission = f"{SCOPE_PREFIX}/add_merge_automation/{automation.product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    if automation.status != TaskStatus.Pending:
        return abort(400, f"Cannot start automation in {automation.status.name} status")

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

        task_id = result["status"]["taskId"]
        logger.info(f"Triggered merge automation action, task ID: {task_id}")
        return task_id
    except TaskclusterRestFailure as e:
        abort(400, str(e))


def get_task_status(task_id):
    queue = get_service("queue")
    task_status = queue.status(task_id)
    return {
        "taskId": task_id,
        "state": task_status["status"]["state"],
    }


def get_task_group_status(task_group_id):
    queue = get_service("queue")

    try:
        task_group = queue.listTaskGroup(task_group_id)
    except TaskclusterRestFailure as e:
        if e.status_code == 404:
            return TaskStatus.Pending
        raise

    group_status = TaskStatus.Completed
    for task in task_group["tasks"]:
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

    decision_task_status = get_task_status(automation.task_id)
    overall_status = get_task_group_status(automation.task_id)

    # Update automation status based on task group status
    status_changed = False
    if overall_status == TaskStatus.Completed and automation.status != TaskStatus.Completed:
        automation.status = TaskStatus.Completed
        automation.completed = datetime.datetime.now(datetime.UTC)
        status_changed = True
    elif overall_status == TaskStatus.Failed and automation.status != TaskStatus.Failed:
        automation.status = TaskStatus.Failed
        status_changed = True

    if status_changed:
        db.session.commit()

    return {
        "automation": automation.json,
        "decisionTask": decision_task_status,
        "taskGroup": {"overallStatus": overall_status.name.lower()},
    }
