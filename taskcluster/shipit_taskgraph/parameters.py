# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Optional

from taskgraph.parameters import extend_parameters_schema
from taskgraph.util.schema import Schema

DEPLOYMENT_BRANCHES = ("dev", "production")

shipit_schema = Schema.from_dict(
    {
        "deployment_branch": Optional[str],
        "deploy": Optional[bool],
    },
    kw_only=True,
)

extend_parameters_schema(shipit_schema)


def get_decision_parameters(graph_config, parameters):
    """Add repo-specific decision parameters."""
    if parameters["tasks_for"] == "github-pull-request":
        parameters["deployment_branch"] = "github-pull-request"
    elif parameters["head_ref"].startswith("refs/heads/"):
        parameters["deployment_branch"] = parameters["head_ref"].replace("refs/heads/", "")
        if parameters["deployment_branch"] in DEPLOYMENT_BRANCHES and parameters["level"] == "3":
            parameters["deploy"] = True
