# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Kubernetes docker image builds.
"""

from __future__ import absolute_import, print_function, unicode_literals
from copy import deepcopy

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def set_push_environment(config, jobs):
    """Set the environment variables for the push to docker hub task."""
    for job in jobs:
        # skip the task if we don't need to push the image
        if not config.params.get("push_docker_image"):
            continue

        deploy_config = config.graph_config["deploy"][config.params["docker_tag"]]
        scopes = job.setdefault("scopes", [])
        scopes.extend(deploy_config["extra-scopes"])

        env = job["worker"].setdefault("env", {})
        env.update({
            "DOCKER_TAG": config.params["docker_tag"],
            "FRONTEND_TASKCLUSTER_ROOT_URL": deploy_config["frontend-taskcluster-root-url"],
            "RELEASE_CHANNEL": config.params["docker_tag"],
            "SHIPIT_API_URL": deploy_config["shipit-api-url"],
            "SHIPIT_PUBLIC_API_URL": deploy_config["shipit-public-api-url"],
            "WEBSITE_BUCKET": deploy_config["website-bucket"],
        })
        yield job

