# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Kubernetes docker image builds.
"""

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def set_push_environment(config, jobs):
    """Set the environment variables for the push to docker hub task."""
    for job in jobs:
        # skip the task if we don't need to push the image
        if not config.params.get("deploy"):
            continue

        env = job["worker"].setdefault("env", {})
        env.update({"DEPLOYMENT_BRANCH": config.params["deployment_branch"]})
        yield job

