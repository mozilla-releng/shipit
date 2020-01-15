# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import dataclasses
import datetime

import slugid
import sqlalchemy as sa
import sqlalchemy.orm

from backend_common.db import db
from shipit_api.common.config import SIGNOFFS
from shipit_api.common.models import PhaseBase, ReleaseBase, SignoffBase


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

    def phase_signoffs(self, phase):
        return [
            XPISignoff(uid=slugid.nice(), name=req["name"], description=req["description"], permissions=req["permissions"])
            for req in SIGNOFFS.get("xpi", {}).get(self.xpi_type, {}).get(phase, [])
        ]

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
