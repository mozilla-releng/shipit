# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Deployment secret related environment variables
"""

from __future__ import absolute_import, print_function, unicode_literals

from six import text_type
from voluptuous import Required, Optional

from taskgraph.transforms.base import TransformSequence
from taskgraph.transforms.task import task_description_schema
from taskgraph.util.schema import Schema, taskref_or_string

transforms = TransformSequence()

deploy_schema = Schema(
    {
        Required('name'): text_type,
        Required('job-from'): task_description_schema['job-from'],
        Required("description"): task_description_schema['job-from'],
        Required("project"): text_type,
        Required("image-task-id"): taskref_or_string,
        Optional("variant"): text_type,
        Required("dependencies"): {text_type: text_type},
    }
)

transforms.add_validate(deploy_schema)


CLOUDOPS_DEPLOY_ROUTE = "cloudops.deploy.v1.{project}.{environment}"


@transforms.add
def build_task(config, jobs):
    """Set the environment variables for the push to docker hub task."""
    for job in jobs:
        # skip the task if we don't need to push the image
        if not config.params.get("deploy"):
            continue

        route = CLOUDOPS_DEPLOY_ROUTE.format(
            project=job["project"], environment=config.params["deployment_branch"],
        )
        deploy = {
            "image-task-id": job["image-task-id"],
        }
        if "variant" in job:
            deploy["variant"] = job["variant"]

        task = {
            'name': job['name'],
            "description": job["description"],
            "worker-type": "succeed",
            "dependencies": job["dependencies"],
            "extra": {"cloudops-deploy": deploy},
            "routes": [route],
        }
        yield task
