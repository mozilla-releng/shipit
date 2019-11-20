# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from collections import defaultdict

import taskcluster_urls
from flask import abort, current_app, jsonify
from flask_login import current_user
from mozilla_version.gecko import DeveditionVersion, FennecVersion, FirefoxVersion, ThunderbirdVersion
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest

from backend_common.auth import auth
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from shipit_api.config import PROJECT_NAME, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS, SCOPE_PREFIX
from shipit_api.models import DisabledProduct, Phase, Release, Signoff
from shipit_api.release import Product
from shipit_api.tasks import ArtifactNotFound, UnsupportedFlavor, fetch_artifact, generate_action_hook, render_action_hook

logger = get_logger(__name__)

VERSION_CLASSES = {
    Product.FIREFOX.value: FirefoxVersion,
    Product.FENNEC.value: FennecVersion,
    Product.THUNDERBIRD.value: ThunderbirdVersion,
    Product.DEVEDITION.value: DeveditionVersion,
}


def good_version(release):
    """Can the version be parsed by mozilla_version

    Some ancient versions cannot be parsed by the mozilla_version module. This
    function helps to skip the versions that are not supported.
    Example versions that cannot be parsed:
    1.1, 1.1b1, 2.0.0.1
    """
    product = release["product"]
    if product not in VERSION_CLASSES:
        raise ValueError(f"Product {product} versions are not supported")
    try:
        VERSION_CLASSES[product].parse(release["version"])
        return True
    except ValueError:
        return False


def notify_via_irc(product, message):
    owners_section = current_app.config.get("IRC_NOTIFICATIONS_OWNERS_PER_PRODUCT")
    channels_section = current_app.config.get("IRC_NOTIFICATIONS_CHANNELS_PER_PRODUCT")

    if not (owners_section and channels_section):
        logger.info(f'Product "{product}" IRC notifications are not enabled')
        return

    owners = owners_section.get(product, owners_section.get("default"))
    channels = channels_section.get(product, channels_section.get("default"))

    if owners and channels:
        owners = ": ".join(owners)
        for channel in channels:
            current_app.notify.irc({"channel": channel, "message": f"{owners}: {message}"})


def add_release(body):
    # we must require scope which depends on product
    required_permission = f'{SCOPE_PREFIX}/add_release/{body["product"]}'
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    session = current_app.db.session
    product = body["product"]
    r = Release(
        product=product,
        version=body["version"],
        branch=body["branch"],
        revision=body["revision"],
        build_number=body["build_number"],
        release_eta=body.get("release_eta"),
        status="scheduled",
        partial_updates=body.get("partial_updates"),
        product_key=body.get("product_key"),
    )
    try:
        r.generate_phases(partner_urls=current_app.config.get("PARTNERS_URL"), github_token=current_app.config.get("GITHUB_TOKEN"))
        session.add(r)
        session.commit()
        release = r.json
    except UnsupportedFlavor as e:
        raise BadRequest(description=e.description)

    notify_via_irc(product, f"New release ({product} {r.version} build{r.build_number}) was just created.")

    return release, 201


def list_releases(product=None, branch=None, version=None, build_number=None, status=["scheduled"]):
    session = current_app.db.session
    releases = session.query(Release)
    if product:
        releases = releases.filter(Release.product == product)
    if branch:
        releases = releases.filter(Release.branch == branch)
    if version:
        releases = releases.filter(Release.version == version)
        if build_number:
            releases = releases.filter(Release.build_number == build_number)
    elif build_number:
        raise BadRequest(description="Filtering by build_number without version" " is not supported.")
    releases = releases.filter(Release.status.in_(status))
    releases = [r.json for r in releases.all()]
    # filter out not parsable releases, like 1.1, 1.1b1, etc
    releases = filter(good_version, releases)
    return sorted(releases, key=lambda r: VERSION_CLASSES[r["product"]].parse(r["version"]))


def get_release(name):
    session = current_app.db.session
    try:
        release = session.query(Release).filter(Release.name == name).one()
        return release.json
    except NoResultFound:
        abort(404)


def get_phase(name, phase):
    session = current_app.db.session
    try:
        phase = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).one()
        return phase.json
    except NoResultFound:
        abort(404)


def schedule_phase(name, phase):
    session = current_app.db.session
    try:
        phase = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).one()
    except NoResultFound:
        abort(404)

    # we must require scope which depends on product
    required_permission = f"{SCOPE_PREFIX}/schedule_phase/{phase.release.product}/{phase.name}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    if phase.submitted:
        abort(409, "Already submitted!")

    for signoff in phase.signoffs:
        if not signoff.signed:
            abort(400, "Pending signoffs")

    hook = phase.task_json

    if "hook_payload" not in hook:
        raise ValueError("Action tasks are not supported")

    hooks = get_service("hooks")
    client_id = hooks.options["credentials"]["clientId"].decode("utf-8")
    extra_context = {"clientId": client_id}
    result = hooks.triggerHook(hook["hook_group_id"], hook["hook_id"], phase.rendered_hook_payload(extra_context=extra_context))
    phase.task_id = result["status"]["taskId"]

    phase.submitted = True
    phase.completed_by = current_user.get_id()
    completed = datetime.datetime.utcnow()
    phase.completed = completed
    if all([ph.submitted for ph in phase.release.phases]):
        phase.release.status = "shipped"
        phase.release.completed = completed
    session.commit()

    root_url = hooks.options["rootUrl"]
    url = taskcluster_urls.ui(root_url, f"/tasks/groups/{phase.task_id}")

    notify_via_irc(
        phase.release.product,
        f"Phase {phase.name} was just scheduled for release {phase.release.product} {phase.release.version} build{phase.release.build_number} - {url}",
    )

    return phase.json


def abandon_release(name):
    session = current_app.db.session
    try:
        release = session.query(Release).filter(Release.name == name).one()

        # we must require scope which depends on product
        required_permission = f"{SCOPE_PREFIX}/abandon_release/{release.product}"
        if not current_user.has_permissions(required_permission):
            user_permissions = ", ".join(current_user.get_permissions())
            abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

        # Cancel all submitted task groups first
        for phase in filter(lambda x: x.submitted, release.phases):
            try:
                actions = fetch_artifact(phase.task_id, "public/actions.json")
                parameters = fetch_artifact(phase.task_id, "public/parameters.yml")
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
            res = hooks.triggerHook(hook["hook_group_id"], hook["hook_id"], hook_payload_rendered)
            logger.debug("Done: %s", res)

        release.status = "aborted"
        session.commit()
        release_json = release.json
    except NoResultFound:
        abort(404)

    notify_via_irc(release.product, f"Release {release.product} {release.version} build{release.build_number} was just canceled.")

    return release_json


@auth.require_permissions([SCOPE_PREFIX + "/rebuild_product_details"])
def rebuild_product_details(options):
    pulse_user = current_app.config["PULSE_USER"]
    exchange = f"exchange/{pulse_user}/{PROJECT_NAME}"

    logger.info(f"Sending pulse message `{options}` to queue `{exchange}` for " f"route `{PULSE_ROUTE_REBUILD_PRODUCT_DETAILS}`.")

    try:
        current_app.pulse.publish(exchange, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS, options)
    except Exception as e:
        import traceback

        msg = "Can't send notification to pulse."
        trace = traceback.format_exc()
        logger.error(f"{msg}\nException:{e}\nTraceback: {trace}")
    return jsonify({"ok": "ok"})


@auth.require_permissions([SCOPE_PREFIX + "/update_release_status"])
def update_release_status(name, body):
    session = current_app.db.session
    try:
        r = session.query(Release).filter(Release.name == name).one()
    except NoResultFound:
        abort(404)

    status = body["status"]
    r.status = status
    if status == "shipped":
        r.completed = datetime.datetime.utcnow()
    session.commit()
    release = r.json

    notify_via_irc(r.product, f"Release {r.product} {r.version} build{r.build_number} status changed to `{status}`.")

    return release


def get_phase_signoff(name, phase):
    session = current_app.db.session
    try:
        phase = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).one()
        signoffs = [s.json for s in phase.signoffs]
        return dict(signoffs=signoffs)
    except NoResultFound:
        abort(404)


def phase_signoff(name, phase, uid):
    session = current_app.db.session
    try:
        signoff = session.query(Signoff).filter(Signoff.uid == uid).one()
    except NoResultFound:
        abort(404, "Sign off does not exist")

    if signoff.signed:
        abort(409, "Already signed off")

    # we must require scope which depends on product and phase name
    required_permission = f"{SCOPE_PREFIX}/phase_signoff/{signoff.phase.release.product}/{signoff.phase.name}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    try:
        # Prevent the same user signing off for multiple signoffs
        phase_obj = session.query(Phase).filter(Release.id == Phase.release_id).filter(Release.name == name).filter(Phase.name == phase).one()
    except NoResultFound:
        abort(404, "Phase not found")

    who = current_user.get_id()
    if who in [s.completed_by for s in phase_obj.signoffs]:
        abort(409, f"Already signed off by {who}")

    signoff.completed = datetime.datetime.utcnow()
    signoff.signed = True
    signoff.completed_by = who

    session.commit()
    signoffs = [s.json for s in phase_obj.signoffs]

    # Schedule the phase when all signoffs are done
    if all([s.signed for s in phase_obj.signoffs]):
        schedule_phase(name, phase)

    r = phase_obj.release
    notify_via_irc(r.product, f"{phase} of {r.product} {r.version} build{r.build_number} signed off by {who}.")

    return dict(signoffs=signoffs)


def get_disabled_products():
    session = current_app.db.session
    ret = defaultdict(list)
    for row in session.query(DisabledProduct).all():
        ret[row.product].append(row.branch)
    return ret


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

    return 200


def enable_product(product, branch):
    session = current_app.db.session

    required_permission = f"{SCOPE_PREFIX}/enable_product/{product}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    try:
        dp = session.query(DisabledProduct).filter(DisabledProduct.product == product).filter(DisabledProduct.branch == branch).one()
        session.delete(dp)
        session.commit()
        return 200
    except NoResultFound:
        abort(404)
