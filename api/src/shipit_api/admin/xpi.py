import datetime
import logging

import taskcluster_urls
from flask import abort, current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from taskcluster.exceptions import TaskclusterRestFailure
from werkzeug.exceptions import BadRequest

from backend_common.auth import auth
from cli_common.taskcluster import get_root_url
from shipit_api.admin.api import do_schedule_phase
from shipit_api.admin.github import get_xpi_type
from shipit_api.admin.models import XPI, XPIPhase, XPIRelease, XPISignoff
from shipit_api.admin.tasks import UnsupportedFlavor, generate_phases
from shipit_api.common.config import SCOPE_PREFIX

logger = logging.getLogger(__name__)


def _xpi_type(revision, xpi_name):
    return get_xpi_type(current_app.config.get("XPI_MANIFEST_OWNER"), current_app.config.get("XPI_MANIFEST_REPO"), revision, xpi_name)


def add_release(body):
    # we must require scope which depends on XPI type
    xpi_type = _xpi_type(body["revision"], body["xpi_name"])
    required_permission = f"{SCOPE_PREFIX}/add_release/xpi/{xpi_type}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")
    session = current_app.db.session
    xpi = XPI(name=body["xpi_name"], revision=body["xpi_revision"], version=body["xpi_version"])
    # project name used in the TC routes and matches the repo name
    project = current_app.config.get("XPI_MANIFEST_REPO")
    release = XPIRelease(revision=body["revision"], xpi=xpi, build_number=body["build_number"], status="scheduled", xpi_type=xpi_type, project=project)
    try:
        common_input = {"build_number": release.build_number, "xpi_name": release.xpi_name, "revision": release.xpi_revision, "version": release.xpi_version}
        release.phases = generate_phases(release, common_input, verify_supported_flavors=False)
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
    return release.json, 201


def list_releases(xpi_name=None, xpi_version=None, build_number=None, status=["scheduled"]):
    session = current_app.db.session
    releases = session.query(XPIRelease)
    if xpi_name:
        releases = releases.filter(XPIRelease.xpi_name == xpi_name)
    if xpi_version:
        releases = releases.filter(XPIRelease.xpi_version == xpi_version)
        if build_number:
            releases = releases.filter(XPIRelease.build_number == build_number)
    elif build_number:
        raise BadRequest(description="Filtering by build_number without version is not supported.")
    releases = releases.filter(XPIRelease.status.in_(status))
    return [r.json for r in releases.all()]


def get_release(name):
    session = current_app.db.session
    release = session.query(XPIRelease).filter(XPIRelease.name == name).first_or_404()
    return release.json


def get_phase(name, phase):
    session = current_app.db.session
    phase = session.query(XPIPhase).filter(XPIRelease.id == XPIPhase.release_id).filter(XPIRelease.name == name).filter(XPIPhase.name == phase).first_or_404()
    return phase.json


def schedule_phase(name, phase):
    session = current_app.db.session
    phase = session.query(XPIPhase).filter(XPIRelease.id == XPIPhase.release_id).filter(XPIRelease.name == name).filter(XPIPhase.name == phase).first_or_404()

    # we must require scope which depends on XPI type
    xpi_type = _xpi_type(phase.release.revision, phase.release.xpi_name)
    required_permission = f"{SCOPE_PREFIX}/schedule_phase/xpi/{xpi_type}/{phase.name}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    phase = do_schedule_phase(session, phase)
    url = taskcluster_urls.ui(get_root_url(), f"/tasks/groups/{phase.task_id}")
    logger.info("Phase %s of %s started by %s. - %s", phase.name, phase.release.name, phase.completed_by, url)
    return phase.json


def abandon_release_xpi(name):
    session = current_app.db.session
    release = session.query(XPIRelease).filter(XPIRelease.name == name).first_or_404()
    # we must require scope which depends on XPI type
    xpi_type = _xpi_type(release.revision, release.xpi_name)
    required_permission = f"{SCOPE_PREFIX}/abandon_release/xpi/{xpi_type}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    # XPI doesn't support the "cancel-all" action task, just mark as aborted
    release.status = "aborted"
    session.commit()
    logger.info("Canceled release %s", release.name)
    return release.json


def get_phase_signoff(name, phase):
    session = current_app.db.session
    phase = session.query(XPIPhase).filter(XPIRelease.id == XPIPhase.release_id).filter(XPIRelease.name == name).filter(XPIPhase.name == phase).first_or_404()
    signoffs = [s.json for s in phase.signoffs]
    return dict(signoffs=signoffs)


def phase_signoff(name, phase, body):
    session = current_app.db.session
    signoff = session.query(XPISignoff).filter(XPISignoff.uid == body).first_or_404()

    if signoff.signed:
        abort(409, "Already signed off")

    phase_obj = (
        session.query(XPIPhase).filter(XPIRelease.id == XPIPhase.release_id).filter(XPIRelease.name == name).filter(XPIPhase.name == phase).first_or_404()
    )
    # we must require scope which depends on product and phase name
    xpi_type = _xpi_type(phase_obj.release.revision, phase_obj.release.xpi_name)
    required_permission = f"{SCOPE_PREFIX}/phase_signoff/xpi/{xpi_type}/{signoff.phase.name}"
    if not current_user.has_permissions(required_permission):
        user_permissions = ", ".join(current_user.get_permissions())
        abort(401, f"required permission: {required_permission}, user permissions: {user_permissions}")

    # Prevent the same user signing off for multiple signoffs
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

    release = phase_obj.release
    logger.info("Phase %s of %s signed off by %s", phase, release.name, who)
    return dict(signoffs=signoffs)


@auth.require_permissions([SCOPE_PREFIX + "/update_release_status"])
def update_release_status(name, body):
    session = current_app.db.session
    release = session.query(XPIRelease).filter(XPIRelease.name == name).first_or_404()

    status = body["status"]
    release.status = status
    if status == "shipped":
        release.completed = datetime.datetime.utcnow()

    session.commit()
    logger.info("Status of %s changed to %s", release.name, status)
    return release.json
