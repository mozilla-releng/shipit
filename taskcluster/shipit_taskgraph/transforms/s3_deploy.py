# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
S3 deploy environment variables
"""


from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def set_frontend_push_environment(config, jobs):
    """Set the environment variables for the push to S3."""
    for job in jobs:
        # skip the task if we don't need to push the image
        if not config.params.get("deploy"):
            continue

        deploy_config = config.graph_config["deploy"][config.params["deployment_branch"]]
        env = job["worker"].setdefault("env", {})
        env.update({
            "DEPLOYMENT_BRANCH": config.params["deployment_branch"],
            "FRONTEND_TASKCLUSTER_ROOT_URL": deploy_config["frontend-taskcluster-root-url"],
            "SHIPIT_API_URL": deploy_config["shipit-api-url"],
            "SHIPIT_PUBLIC_API_URL": deploy_config["shipit-public-api-url"],
            "FRONTEND_BUCKET": deploy_config["frontend-bucket"],
        })
        yield job
