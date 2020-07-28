# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Deployment secret related environment variables
"""

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def set_secret(config, jobs):
    """Set the environment variables for the push to docker hub task."""
    for job in jobs:
        # skip the task if we don't need to push the image
        if not config.params.get("deploy"):
            continue

        deploy_config = config.graph_config["deploy"][config.params["deployment_branch"]]
        scopes = job.setdefault("scopes", [])
        scopes.append("secrets:get:{}".format(deploy_config["secret"]))

        env = job["worker"].setdefault("env", {})
        env.update({
            "DEPLOY_SECRET_URL": "http://taskcluster/secrets/v1/secret/{}".format(deploy_config["secret"])
        })
        yield job
