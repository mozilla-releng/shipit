# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import logging

import taskcluster_urls
from flask import abort, current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from taskcluster.exceptions import TaskclusterRestFailure
from werkzeug.exceptions import BadRequest

from backend_common.auth import AuthType, auth
from backend_common.taskcluster import get_root_url, get_service
from shipit_api.admin.release import Product, bump_version, get_locales, is_eme_free_enabled, is_partner_enabled, product_to_appname
from shipit_api.admin.tasks import (
    ArtifactNotFound,
    UnsupportedFlavor,
    find_action,
    generate_action_hook,
    generate_phases,
    get_actions,
    get_parameters,
    render_action_hook,
    rendered_hook_payload,
)
from shipit_api.common.config import HG_PREFIX, PROJECT_NAME, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS, SCOPE_PREFIX
from shipit_api.common.models import DisabledProduct, Phase, Release, Signoff, XPIRelease
from shipit_api.public.api import get_disabled_products, list_releases

logger = logging.getLogger(__name__)


def notify_via_matrix(product, message):
    owners_section = current_app.config.get("MATRIX_NOTIFICATIONS_OWNERS_PER_PRODUCT", {})
    rooms_section = current_app.config.get("MATRIX_NOTIFICATIONS_ROOMS_PER_PRODUCT", {})
    owners = owners_section.get(product, owners_section.get("default"))
    rooms = rooms_section.get(product, rooms_section.get("default"))

    if not owners or not rooms:
        logger.info("Matrix notifications are not configured")
        return

    owners = ": ".join(owners)
    notify = get_service("notify")
    for room_id in rooms:
        try:
            notify.matrix({"roomId": room_id, "body": f"{owners}: {message}"})
        except TaskclusterRestFailure:
            logger.exception("Failed to send Matrix notification")


def add_release(body):
    # we must require scope which depends on product
    required_permission = f'{SCOPE_PREFIX}/add_release/{body["product"]}'
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    product = body["product"]
    branch = body["branch"]

    product_disabled = branch in get_disabled_products().get(product, [])
    if current_user.type == AuthType.TASKCLUSTER and product_disabled:
        abort(401, "Taskcluster based submissions are disabled")

    session = current_app.db.session
    partial_updates = body.get("partial_updates")
    if partial_updates == "auto":
        if product not in [Product.FIREFOX.value, Product.DEVEDITION.value, Product.PINEBUILD.value] or branch not in [
            "try",
            "releases/mozilla-beta",
            "projects/maple",
        ]:
            abort(400, "Partial suggestion works for automated betas only")

        partial_updates = _suggest_partials(product=product, branch=branch)
    release = Release(
        branch=branch,
        build_number=body["build_number"],
        partial_updates=partial_updates,
        product_key=body.get("product_key"),
        product=product,
        release_eta=body.get("release_eta"),
        repo_url=body.get("repo_url", ""),
        revision=body["revision"],
        status="scheduled",
        version=body["version"],
    )
    try:
        next_version = bump_version(release.product, release.version)
        common_input = {
            "build_number": release.build_number,
            "next_version": next_version,
            # specify version rather than relying on in-tree version,
            # so if a version bump happens between the build and an action task
            # revision, we still use the correct version.
            "version": release.version,
            "release_eta": release.release_eta,
            "release_enable_emefree": is_eme_free_enabled(release.product, release.version),
        }
        partners_enabled = is_partner_enabled(release.product, release.version)
        if int(release.version.split(".")[0]) >= 81:
            common_input["release_enable_partner_repack"] = partners_enabled
            common_input["release_enable_partner_attribution"] = partners_enabled
        else:
            common_input["release_enable_partners"] = partners_enabled
        if release.partial_updates:
            common_input["partial_updates"] = release.partial_updates

        release.phases = generate_phases(release, common_input, verify_supported_flavors=True)
        session.add(release)
        session.commit()
    except UnsupportedFlavor as e:
        raise BadRequest(description=e.description)
    except (IntegrityError, TaskclusterRestFailure) as e:
        # Report back Taskcluster and SQL failures for better visibility of the
        # actual issue. Usually it happens when we cannot find the indexed
        # task or a duplicate release request accordingly.
        abort(400, str(e))

    logger.info("New release of %s", release.name)
    notify_via_matrix(product, f"New release of {release.name}")

    return release.json, 201


def do_schedule_phase(session, phase, additional_shipit_emails=[]):
    if phase.submitted:
        abort(409, "Already submitted!")

    for signoff in phase.signoffs:
        if not signoff.signed:
            abort(400, "Pending signoffs")

    hook = phase.task_json
    hooks = get_service("hooks")
    client_id = hooks.options["credentials"]["clientId"].decode("utf-8")
    extra_context = {"clientId": client_id}

    try:
        result = hooks.triggerHook(
            hook["hook_group_id"], hook["hook_id"], rendered_hook_payload(phase, extra_context=extra_context, additional_shipit_emails=additional_shipit_emails)
        )
        phase.task_id = result["status"]["taskId"]
    except TaskclusterRestFailure as e:
        abort(400, str(e))

    phase.submitted = True
    completed = datetime.datetime.utcnow()
    phase.completed_by = current_user.get_id()
    phase.completed = completed
    # If the previous phases are not submitted, mark them as submitted and they
    # will be calculated as skipped because they don't have taskId associated
    for ph in phase.release.phases:
        if ph.name == phase.name:
            break
        if not ph.submitted:
            ph.submitted = True
            ph.completed_by = current_user.get_id()
            ph.completed = completed

    session.commit()
    return phase


def schedule_phase(name, phase):
    session = current_app.db.session
    phase = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).first_or_404()

    # we must require scope which depends on product
    required_permission = f"{SCOPE_PREFIX}/schedule_phase/{phase.release.product}/{phase.name}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    phase = do_schedule_phase(session, phase)
    url = taskcluster_urls.ui(get_root_url(), f"/tasks/groups/{phase.task_id}")
    logger.info("Phase %s of %s started by %s. - %s", phase.name, phase.release.name, phase.completed_by, url)
    notify_via_matrix(phase.release.product, f"Phase {phase.name} was just scheduled for {phase.release.name} - {url}")

    return phase.json


def abandon_release(name):
    session = current_app.db.session
    release = session.query(Release).filter(Release.name == name).first_or_404()

    # we must require scope which depends on product
    required_permission = f"{SCOPE_PREFIX}/abandon_release/{release.product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    # Cancel all submitted task groups first
    for phase in filter(lambda x: x.submitted and not x.skipped, release.phases):
        try:
            actions = get_actions(phase.task_id)
            parameters = get_parameters(phase.task_id)
            cancel_action = find_action("cancel-all", actions)
            if not cancel_action:
                logger.info("%s %s does not have `cancel-all` action, skipping...", release.name, phase.name)
                continue
        except ArtifactNotFound:
            logger.info("Ignoring not completed action task %s", phase.task_id)
            continue

        hook = generate_action_hook(task_group_id=phase.task_id, action_name="cancel-all", actions=actions, parameters=parameters, input_={})
        hooks = get_service("hooks")
        client_id = hooks.options["credentials"]["clientId"].decode("utf-8")
        hook["context"]["clientId"] = client_id
        hook_payload_rendered = render_action_hook(
            payload=hook["hook_payload"], context=hook["context"], delete_params=["existing_tasks", "release_history", "release_partner_config"]
        )
        logger.info("Cancel phase %s by hook %s with payload: %s", phase.name, hook["hook_id"], hook_payload_rendered)
        try:
            result = hooks.triggerHook(hook["hook_group_id"], hook["hook_id"], hook_payload_rendered)
            logger.debug("Done: %s", result)
        except TaskclusterRestFailure as e:
            abort(400, str(e))

    release.status = "aborted"
    session.commit()
    logger.info("Canceled release %s", release.name)
    notify_via_matrix(release.product, f"Release {release.name} was just canceled.")
    return release.json


def _rebuild_product_details(body):
    pulse_user = current_app.config["PULSE_USER"]
    exchange = f"exchange/{pulse_user}/{PROJECT_NAME}"
    logger.info("Sending pulse message `%s` to queue `%s` for route `%s`.", body, exchange, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS)
    current_app.pulse.publish(exchange, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS, body)


@auth.require_permissions([SCOPE_PREFIX + "/rebuild_product_details"])
def rebuild_product_details(body):
    _rebuild_product_details(body)
    return {"status": "ok"}


@auth.require_permissions([SCOPE_PREFIX + "/update_release_status"])
def update_release_status(name, body):
    session = current_app.db.session
    # Search in multiple release tables for possible match
    releases = list(filter(None, [session.query(product_model).filter(product_model.name == name).first() for product_model in (Release, XPIRelease)]))

    if not releases:
        abort(404, f"Release {name} not found")

    release = releases[0]

    status = body["status"]
    release.status = status
    if status == "shipped":
        release.completed = datetime.datetime.utcnow()
    session.commit()

    logger.info("Status of %s changed to %s", release.name, status)
    if status == "shipped" and release.product_details_enabled:
        logger.info("Regenerating product details after marking %s as shipped", release.name)
        _rebuild_product_details({})

    notify_via_matrix(release.product, f"Release {release.name} status changed to `{status}`.")

    return release.json


def phase_signoff(name, phase, body):
    session = current_app.db.session
    signoff = session.query(Signoff).filter(Signoff.uid == body).first_or_404()

    if signoff.signed:
        abort(409, "Already signed off")

    # we must require scope which depends on product and phase name
    required_permission = f"{SCOPE_PREFIX}/phase_signoff/{signoff.phase.release.product}/{signoff.phase.name}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    # Prevent the same user signing off for multiple signoffs
    phase_obj = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).first_or_404()

    users_ldap = current_user.get_ldap_groups()
    users_email = current_user.get_id()
    if users_email in [s.completed_by for s in phase_obj.signoffs]:
        abort(409, f"Already signed off by {users_email}")

    # signoff.permissions corresponds to the group in settings.py
    ldap_groups = current_app.config.get("LDAP_GROUPS", {})
    ldap_group = ldap_groups.get(signoff.permissions, [])
    if not set(users_ldap).intersection(set(ldap_group)):
        abort(401, f"User `{users_email}` is not in the `{signoff.permissions}`")

    signoff.completed = datetime.datetime.utcnow()
    signoff.signed = True
    signoff.completed_by = users_email

    session.commit()
    signoffs = [s.json for s in phase_obj.signoffs]

    # Schedule the phase when all signoffs are done
    if all([s.signed for s in phase_obj.signoffs]):
        schedule_phase(name, phase)

    release = phase_obj.release
    logger.info("Phase %s of %s signed off by %s", phase, release.name, users_email)
    notify_via_matrix(release.product, f"{phase} of {release.name} signed off by {users_email}.")

    return dict(signoffs=signoffs)


def disable_product(body):
    product = body["product"]
    branch = body["branch"]

    required_permission = f"{SCOPE_PREFIX}/disable_product/{product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    session = current_app.db.session

    dp = DisabledProduct(product=product, branch=branch)
    session.add(dp)
    session.commit()
    logger.info("Disabled %s on branch %s", product, branch)
    notify_via_matrix(product, f"Automatic releases disabled for {product} on {branch}")

    return 200


def enable_product(product, branch):
    session = current_app.db.session

    required_permission = f"{SCOPE_PREFIX}/enable_product/{product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    dp = session.query(DisabledProduct).filter(DisabledProduct.product == product).filter(DisabledProduct.branch == branch).first_or_404()
    session.delete(dp)
    session.commit()
    logger.info("Enabled %s on branch %s", product, branch)
    notify_via_matrix(product, f"Automatic releases enabled for {product} on {branch}")

    return 200


def _suggest_partials(product, branch, max_partials=3):
    """Return a list of suggested partials"""
    shipped_releases = reversed(list_releases(product, branch, status=["shipped"]))
    suggested_releases = list(shipped_releases)[:max_partials]
    suggested_partials = {}
    for release in suggested_releases:
        suggested_partials[release["version"]] = {
            "buildNumber": release["build_number"],
            "locales": get_locales(f"{HG_PREFIX}/{release['branch']}", release["revision"], product_to_appname(product)),
        }
    return suggested_partials


def get_signoff_emails(phases):
    additional_shipit_emails = set()
    if phases:
        for _phase in phases:
            if _phase.completed_by is not None:
                additional_shipit_emails.add(_phase.completed_by)
            additional_shipit_emails.update({signoff.completed_by for signoff in _phase.signoffs if signoff.completed_by is not None})

    return list(additional_shipit_emails)
