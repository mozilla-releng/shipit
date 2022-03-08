# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Kubernetes docker image builds.
"""


import os

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def set_push_environment(config, jobs):
    """Set the environment variables for the push to docker hub task."""
    for job in jobs:
        # skip the task if we don't need to push the image
        if not config.params.get("deploy"):
            continue

        version_file = os.path.join(config.graph_config.vcs_root, "api",
                                    "version.txt")
        version = open(version_file).read().strip()

        env = job["worker"].setdefault("env", {})
        env.update({
            "DEPLOYMENT_BRANCH": config.params["deployment_branch"],
            "VCS_HEAD_REPOSITORY": config.params['head_repository'],
            "VCS_HEAD_REV": config.params['head_rev'],
            # TODO: Figure out if we still need to add the version
            "APP_VERSION": version,
        })
        yield job
