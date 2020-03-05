# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json

import slugid
import sqlalchemy as sa
import sqlalchemy.orm

from backend_common.db import db
from shipit_api.common.config import SIGNOFFS


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
    product_details_enabled = True

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
        self.name = f"{product.capitalize()}-{version}-build{build_number}"
        self.product = product
        self.version = version
        self.branch = branch
        self.revision = revision
        self.build_number = build_number
        # Swagger doesn't let passing null values for strings, we use "falsy"
        # ones instead
        self.release_eta = release_eta or None
        self.partial_updates = partial_updates
        self.status = status
        self.product_key = product_key
        self.repo_url = repo_url

    def phase_signoffs(self, phase):
        return [
            Signoff(uid=slugid.nice(), name=req["name"], description=req["description"], permissions=req["permissions"])
            for req in SIGNOFFS.get(self.branch, {}).get(self.product, {}).get(phase, [])
        ]

    @property
    def project(self):
        return self.branch.split("/")[-1]


class DisabledProduct(db.Model):
    __tablename__ = "shipit_api_disabled_products"

    product = sa.Column(sa.String, nullable=False, primary_key=True)
    branch = sa.Column(sa.String, nullable=False, primary_key=True)
