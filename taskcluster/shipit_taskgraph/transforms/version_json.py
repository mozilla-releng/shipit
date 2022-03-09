# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Generate version.json args
"""

import os

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def add_version_json_args(config, jobs):
    """Generate version.json args for K8S image"""
    for job in jobs:
        version_file = os.path.join(config.graph_config.vcs_root, "api",
                                    "version.txt")
        version = open(version_file).read().strip()
        args = job.get('args', {})

        args["VCS_HEAD_REPOSITORY"] = config.params['head_repository']
        # TODO: Figure out if we still need to add the version
        args["APP_VERSION"] = version
        # TODO: VCS_HEAD_REV should not affect the docker digest and cause
        # rebuilds on every push
        args["VCS_HEAD_REV"] = config.params['head_rev']

        yield job
