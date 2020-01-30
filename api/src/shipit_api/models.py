# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import dataclasses
import datetime
import json
from functools import lru_cache

import slugid
import sqlalchemy as sa
import sqlalchemy.orm

import shipit_api.config
from backend_common.db import db
from shipit_api.release import bump_version, is_eme_free_enabled, is_partner_enabled
from shipit_api.tasks import extract_our_flavors, fetch_artifact, find_action, find_decision_task_id, generate_action_hook, render_action_hook


class SignoffBase:
    def __init__(self, uid, name, description, permissions):
        self.uid = uid
        self.name = name
        self.description = description
        self.permissions = permissions

    @property
    def json(self):
        return dict(
            uid=self.uid,
            name=self.name,
            description=self.description,
            permissions=self.permissions,
            completed=self.completed or "",
            completed_by=self.completed_by or "",
            signed=self.signed,
        )


class Signoff(db.Model, SignoffBase):
    __tablename__ = "shipit_api_signoffs"
    id = sa.Column(sa.Integer, primary_key=True)
    uid = sa.Column(sa.String, nullable=False, unique=True)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    permissions = sa.Column(sa.String, nullable=False)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    signed = sa.Column(sa.Boolean, default=False)
    phase_id = sa.Column(sa.Integer, sa.ForeignKey("shipit_api_phases.id"))
    phase = sqlalchemy.orm.relationship("Phase", back_populates="signoffs")


class PhaseBase:
    def __init__(self, name, task_id, task, context, submitted=False):
        self.name = name
        self.task_id = task_id
        self.task = task
        self.submitted = submitted
        self.context = context

    @property
    def task_json(self):
        return json.loads(self.task)

    @property
    def context_json(self):
        return json.loads(self.context)

    def rendered_hook_payload(self, extra_context={}):
        context = self.context_json
        previous_graph_ids = context["input"]["previous_graph_ids"]
        # The first ID is always the decision task ID. We need to update the
        # remaining tasks' IDs using their names.
        decision_task_id, remaining = previous_graph_ids[0], previous_graph_ids[1:]
        resolved_previous_graph_ids = [decision_task_id]
        other_phases = {p.name: p.task_id for p in self.release.phases}
        for phase_name in remaining:
            resolved_previous_graph_ids.append(other_phases[phase_name])
        # in case we skip a phase, the task ID is not defined, we want to
        # filter it out
        resolved_previous_graph_ids = filter(None, resolved_previous_graph_ids)
        context["input"]["previous_graph_ids"] = list(resolved_previous_graph_ids)
        if extra_context:
            context.update(extra_context)
        return render_action_hook(self.task_json["hook_payload"], context)

    @property
    def skipped(self):
        return bool(self.submitted and not self.task_id)

    @property
    def json(self):
        return {
            "name": self.name,
            "submitted": self.submitted,
            "actionTaskId": self.task_id or "",
            "created": self.created or "",
            "completed": self.completed or "",
            "skipped": self.skipped,
        }


class Phase(db.Model, PhaseBase):
    __tablename__ = "shipit_api_phases"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    submitted = sa.Column(sa.Boolean, nullable=False, default=False)
    task_id = sa.Column(sa.String, nullable=False)
    task = sa.Column(sa.Text, nullable=False)
    context = sa.Column(sa.Text, nullable=False)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    release_id = sa.Column(sa.Integer, sa.ForeignKey("shipit_api_releases.id"))
    release = sqlalchemy.orm.relationship("Release", back_populates="phases")
    signoffs = sqlalchemy.orm.relationship("Signoff", order_by=Signoff.id, back_populates="phase")


class ReleaseBase:
    def generate_phases(self):
        phases = []
        previous_graph_ids = [self.decision_task_id]
        for phase in self.release_promotion_flavors():
            input_ = copy.deepcopy(self.common_input)
            input_["release_promotion_flavor"] = phase["name"]
            input_["previous_graph_ids"] = list(previous_graph_ids)

            hook = generate_action_hook(
                task_group_id=self.decision_task_id, action_name="release-promotion", actions=self.actions, parameters=self.parameters, input_=input_
            )
            hook_no_context = {k: v for k, v in hook.items() if k != "context"}
            phase_obj = self.phase_class(name=phase["name"], task_id="", task=json.dumps(hook_no_context), context=json.dumps(hook["context"]))
            # we need to update input_['previous_graph_ids'] later, because
            # the task IDs cannot be set for hooks in advance
            if phase["in_previous_graph_ids"]:
                previous_graph_ids.append(phase["name"])

            phase_obj.signoffs = self.phase_signoffs(phase["name"])
            phases.append(phase_obj)
        self.phases = phases

    @property
    @lru_cache(maxsize=2048)
    def decision_task_id(self):
        return find_decision_task_id(self.repo_url, self.project, self.revision, self.product)

    @property
    def actions(self):
        return fetch_artifact(self.decision_task_id, "public/actions.json")

    @property
    def parameters(self):
        return fetch_artifact(self.decision_task_id, "public/parameters.yml")

    @property
    def allow_phase_skipping(self):
        # Phases can be skipped for betas and try only. The API doesn't enforce this.
        return self.product in ["firefox", "devedition"] and self.project in ["try", "beta"]

    @property
    def json(self):
        return {
            "name": self.name,
            "product": self.product,
            "branch": self.branch,
            "project": self.project,
            "version": self.version,
            "revision": self.revision,
            "build_number": self.build_number,
            "release_eta": self.release_eta or "",
            "status": self.status,
            "created": self.created or "",
            "completed": self.completed or "",
            "phases": [p.json for p in self.phases],
            "allow_phase_skipping": self.allow_phase_skipping,
        }


class Release(db.Model, ReleaseBase):
    __tablename__ = "shipit_api_releases"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False, unique=True)
    product = sa.Column(sa.String, nullable=False)
    version = sa.Column(sa.String, nullable=False)
    branch = sa.Column(sa.String, nullable=False)
    revision = sa.Column(sa.String, nullable=False)
    build_number = sa.Column(sa.Integer, nullable=False)
    release_eta = sa.Column(sa.DateTime)
    status = sa.Column(sa.String)  # TODO: move to Enum: shipped, abandoned, scheduled
    phases = sqlalchemy.orm.relationship("Phase", order_by=Phase.id, back_populates="release")
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)

    phase_class = Phase

    def __init__(self, product, version, branch, revision, build_number, release_eta, partial_updates, status, product_key=None, repo_url=""):
        self.branch = branch
        self.build_number = build_number
        self.name = f"{product.capitalize()}-{version}-build{build_number}"
        self.partial_updates = partial_updates
        self.product = product
        self.product_key = product_key
        # Swagger doesn't let passing null values for strings, we use "falsy"
        # ones instead
        self.release_eta = release_eta or None
        self.repo_url = repo_url  # XXX Not stored in the DB, just used for find_decision_task_id()
        self.revision = revision
        self.status = status
        self.version = version

    def phase_signoffs(self, phase):
        return [
            Signoff(uid=slugid.nice(), name=req["name"], description=req["description"], permissions=req["permissions"])
            for req in shipit_api.config.SIGNOFFS.get(self.branch, {}).get(self.product, {}).get(phase, [])
        ]

    @property
    def common_input(self):
        next_version = bump_version(self.version.replace("esr", ""))
        input_ = {
            "build_number": self.build_number,
            "next_version": next_version,
            # specify version rather than relying on in-tree version,
            # so if a version bump happens between the build and an action task
            # revision, we still use the correct version.
            "version": self.version,
            "release_eta": self.release_eta,
        }
        if not is_partner_enabled(self.product, self.version):
            input_["release_enable_partners"] = False
        if not is_eme_free_enabled(self.product, self.version):
            input_["release_enable_emefree"] = False

        if self.partial_updates:
            input_["partial_updates"] = self.partial_updates

        return input_

    @property
    def project(self):
        return self.branch.split("/")[-1]

    def release_promotion_flavors(self):
        relpro = find_action("release-promotion", self.actions)
        avail_flavors = relpro["schema"]["properties"]["release_promotion_flavor"]["enum"]
        our_flavors = extract_our_flavors(avail_flavors, self.product, self.version, self.partial_updates, self.product_key)
        return our_flavors


class DisabledProduct(db.Model):
    __tablename__ = "shipit_api_disabled_products"

    product = sa.Column(sa.String, nullable=False, primary_key=True)
    branch = sa.Column(sa.String, nullable=False, primary_key=True)


@dataclasses.dataclass
class XPI:
    name: str
    revision: str
    version: str


class XPISignoff(db.Model, SignoffBase):
    __tablename__ = "shipit_api_xpi_signoffs"
    id = sa.Column(sa.Integer, primary_key=True)
    uid = sa.Column(sa.String, nullable=False, unique=True)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    permissions = sa.Column(sa.String, nullable=False)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    signed = sa.Column(sa.Boolean, default=False)
    phase_id = sa.Column(sa.Integer, sa.ForeignKey("shipit_api_xpi_phases.id"))
    phase = sqlalchemy.orm.relationship("XPIPhase", back_populates="signoffs")


class XPIPhase(db.Model, PhaseBase):
    __tablename__ = "shipit_api_xpi_phases"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    submitted = sa.Column(sa.Boolean, nullable=False, default=False)
    task_id = sa.Column(sa.String, nullable=False)
    task = sa.Column(sa.Text, nullable=False)
    context = sa.Column(sa.Text, nullable=False)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    release_id = sa.Column(sa.Integer, sa.ForeignKey("shipit_api_xpi_releases.id"))
    release = sqlalchemy.orm.relationship("XPIRelease", back_populates="phases")
    signoffs = sqlalchemy.orm.relationship("XPISignoff", order_by=XPISignoff.id, back_populates="phase")


class XPIRelease(db.Model, ReleaseBase):
    __tablename__ = "shipit_api_xpi_releases"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False, unique=True)
    build_number = sa.Column(sa.Integer, nullable=False)
    xpi_name = sa.Column(sa.String, nullable=False)
    xpi_revision = sa.Column(sa.String, nullable=False)
    xpi_version = sa.Column(sa.String, nullable=False)
    revision = sa.Column(sa.String, nullable=False)
    status = sa.Column(sa.String)
    phases = sqlalchemy.orm.relationship("XPIPhase", order_by=XPIPhase.id, back_populates="release")
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)

    phase_class = XPIPhase

    def __init__(self, revision, xpi, build_number, status, xpi_type, project, repo_url=""):
        self.name = f"{xpi.name}-{xpi.version}-build{build_number}"
        self.xpi_name = xpi.name
        self.xpi_revision = xpi.revision
        self.xpi_version = xpi.version
        self.build_number = build_number
        self.revision = revision
        self.status = status
        self.xpi_type = xpi_type
        self.project = project
        self.repo_url = repo_url
        self.product = xpi.name

    def phase_signoffs(self, phase):
        return [
            XPISignoff(uid=slugid.nice(), name=req["name"], description=req["description"], permissions=req["permissions"])
            for req in shipit_api.config.SIGNOFFS.get("xpi", {}).get(self.xpi_type, {}).get(phase, [])
        ]

    @property
    def common_input(self):
        return {"build_number": self.build_number, "xpi_name": self.xpi_name, "revision": self.xpi_revision, "version": self.xpi_version}

    def release_promotion_flavors(self):
        relpro = find_action("release-promotion", self.actions)
        # return as is, no sanity check similar to gecko-based products
        flavors = relpro["schema"]["properties"]["release_promotion_flavor"]["enum"]
        return [{"name": name, "in_previous_graph_ids": True} for name in flavors]

    @property
    def json(self):
        return {
            "name": self.name,
            "revision": self.revision,
            "xpi_name": self.xpi_name,
            "xpi_revision": self.xpi_revision,
            "xpi_version": self.xpi_version,
            "build_number": self.build_number,
            "status": self.status,
            "created": self.created or "",
            "completed": self.completed or "",
            "phases": [p.json for p in self.phases],
        }
