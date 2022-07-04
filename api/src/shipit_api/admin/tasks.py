# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import json
from functools import lru_cache

import jsone
import requests
import yaml

from backend_common.taskcluster import get_service
from shipit_api.admin.github import extract_github_repo_owner_and_name, is_github_url
from shipit_api.admin.release import is_rc
from shipit_api.common.config import SUPPORTED_FLAVORS, SUPPORTED_MOBILE_REPO_NAMES


class UnsupportedFlavor(Exception):
    def __init__(self, description):
        super().__init__(description)
        self.description = description


class ArtifactNotFound(Exception):
    pass


def get_trust_domain(repo_url, project, product):
    if is_github_url(repo_url):
        repo_owner, repo_name = extract_github_repo_owner_and_name(repo_url)
        if repo_owner == "mozilla-mobile" or repo_name in SUPPORTED_MOBILE_REPO_NAMES:
            return "mobile"
        else:
            raise UnsupportedFlavor(f'Unable to know what to do with repo_owner "{repo_owner}" and repo_name "{repo_name}"')
    elif "comm" in project:
        return "comm"
    elif "xpi" in project:
        return "xpi"
    else:
        return "gecko"


@lru_cache(maxsize=2048)
def find_decision_task_id(repo_url, project, revision, product):
    trust_domain = get_trust_domain(repo_url, project, product)
    if trust_domain.endswith("mobile"):
        _, project = extract_github_repo_owner_and_name(repo_url)

    decision_task_route = f"{trust_domain}.v2.{project}.revision.{revision}.taskgraph.decision"
    index = get_service("index")
    try:
        return index.findTask(decision_task_route)["taskId"]
    except Exception as exc:
        raise Exception(f"route {decision_task_route} exception {exc}")


def fetch_group_tasks(task_id):
    queue = get_service("queue")
    try:
        return queue.listTaskGroup(task_id)["tasks"]
    except Exception as exc:
        raise Exception(f"task {task_id} exception {exc}")


def fetch_latest_artifacts(task_id):
    queue = get_service("queue")
    try:
        return queue.listLatestArtifacts(task_id)["artifacts"]
    except Exception as exc:
        raise Exception(f"task {task_id} exception {exc}")


@lru_cache(maxsize=2048)
def generate_artifact_url(task_id, artifact_path):
    queue = get_service("queue")
    try:
        return queue.buildUrl("getLatestArtifact", task_id, artifact_path)
    except Exception as exc:
        raise Exception(f"task {task_id} exception {exc}")


def generate_xpi_url(task_id):
    """
    Generates a taskcluster url pointing to a phase's .xpi artifact.
    Useful for exposing signed system add-ons after a release's promote phase is completed.

    Args:
        task_id: The task id for the action task associated with the release phase.
        xpi_name: The xpi name set on the xpi release.

    Returns:
        A taskcluster url pointing to a phase's .xpi artifact or the empty string.
    """
    try:
        tasks = fetch_group_tasks(task_id)
        for task in tasks:
            task_state = task["status"]["state"]
            task_kind = task["task"]["tags"]["kind"]
            if task_state == "completed" and task_kind == "release-signing":
                task_id = task["status"]["taskId"]
                artifacts = fetch_latest_artifacts(task_id)
                artifact_path = next(artifact["name"] for artifact in artifacts if artifact["name"].endswith(".xpi"))
                artifact_url = generate_artifact_url(task_id, artifact_path)
                return artifact_url
    except Exception:
        return ""


def fetch_artifact(task_id, artifact):
    try:
        queue = get_service("queue")
        url = queue.buildUrl("getLatestArtifact", task_id, artifact)
        q = requests.get(url)
        q.raise_for_status()
        return yaml.safe_load(q.text)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ArtifactNotFound
        raise


def find_action(name, actions):
    for action in actions["actions"]:
        if action["name"] == name:
            return copy.deepcopy(action)
    else:
        return None


def extract_our_flavors(avail_flavors, product, version, partial_updates, product_key=None):
    if not product_key:
        product_key = product

    if is_rc(product_key, version, partial_updates):
        product_key = f"{product_key}_rc"

    if product_key not in SUPPORTED_FLAVORS:
        raise UnsupportedFlavor(description=f"`{product_key}` is not supported")

    # sanity check
    all_flavors = set([fl["name"] for fl in SUPPORTED_FLAVORS[product_key]])
    if not set(avail_flavors).issuperset(all_flavors):
        description = f"Some flavors are not in actions.json: {all_flavors.difference(set(avail_flavors))}."
        raise UnsupportedFlavor(description=description)
    return SUPPORTED_FLAVORS[product_key]


def generate_action_hook(task_group_id, action_name, actions, parameters, input_):
    target_action = find_action(action_name, actions)
    context = copy.deepcopy({"parameters": parameters})
    context.update({"taskGroupId": task_group_id, "taskId": None, "task": None, "input": input_})
    return dict(hook_group_id=target_action["hookGroupId"], hook_id=target_action["hookId"], hook_payload=target_action["hookPayload"], context=context)


def render_action_hook(payload, context, delete_params=[]):
    rendered_payload = jsone.render(payload, context)
    # some parameters contain a lot of entries, so we hit the payload
    # size limit. We don't use this parameter in any case, safe to
    # remove
    if "parameters" in rendered_payload["decision"]:
        for param in delete_params:
            del rendered_payload["decision"]["parameters"][param]
    return rendered_payload


def rendered_hook_payload(phase, extra_context={}, additional_shipit_emails=[]):
    context = phase.context_json
    previous_graph_ids = context["input"]["previous_graph_ids"]
    # The first ID is always the decision task ID. We need to update the
    # remaining tasks' IDs using their names.
    decision_task_id, remaining = previous_graph_ids[0], previous_graph_ids[1:]
    resolved_previous_graph_ids = [decision_task_id]
    other_phases = {p.name: p.task_id for p in phase.release.phases}
    for phase_name in remaining:
        resolved_previous_graph_ids.append(other_phases[phase_name])
    # in case we skip a phase, the task ID is not defined, we want to
    # filter it out
    resolved_previous_graph_ids = filter(None, resolved_previous_graph_ids)
    context["input"]["previous_graph_ids"] = list(resolved_previous_graph_ids)

    if len(additional_shipit_emails):
        context["input"]["additional_shipit_emails"] = additional_shipit_emails

    if extra_context:
        context.update(extra_context)
    return render_action_hook(phase.task_json["hook_payload"], context)


def generate_phases(release, common_input, verify_supported_flavors):
    phases = []
    decision_task_id = find_decision_task_id(release.repo_url, release.project, release.revision, release.product)
    previous_graph_ids = [decision_task_id]
    actions = get_actions(decision_task_id)
    parameters = get_parameters(decision_task_id)
    for phase in release_promotion_flavors(release, actions, verify_supported_flavors):
        input_ = copy.deepcopy(common_input)
        input_["release_promotion_flavor"] = phase["name"]
        input_["previous_graph_ids"] = list(previous_graph_ids)

        hook = generate_action_hook(task_group_id=decision_task_id, action_name="release-promotion", actions=actions, parameters=parameters, input_=input_)
        hook_no_context = {k: v for k, v in hook.items() if k != "context"}
        phase_obj = release.phase_class(name=phase["name"], task_id="", task=json.dumps(hook_no_context), context=json.dumps(hook["context"]))
        # we need to update input_['previous_graph_ids'] later, because
        # the task IDs cannot be set for hooks in advance
        if phase["in_previous_graph_ids"]:
            previous_graph_ids.append(phase["name"])

        phase_obj.signoffs = release.phase_signoffs(phase["name"])
        phases.append(phase_obj)
    return phases


@lru_cache(maxsize=2048)
def get_actions(decision_task_id):
    return fetch_artifact(decision_task_id, "public/actions.json")


@lru_cache(maxsize=2048)
def get_parameters(decision_task_id):
    return fetch_artifact(decision_task_id, "public/parameters.yml")


def release_promotion_flavors(release, actions, verify_supported_flavors=True):
    relpro = find_action("release-promotion", actions)
    avail_flavors = relpro["schema"]["properties"]["release_promotion_flavor"]["enum"]
    if verify_supported_flavors:
        return extract_our_flavors(avail_flavors, release.product, release.version, release.partial_updates, release.product_key)
    return [{"name": name, "in_previous_graph_ids": True} for name in avail_flavors]
