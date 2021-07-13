# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from taskgraph.parameters import extend_parameters_schema
from voluptuous import (
    Any,
    Optional,
)

DEPLOYMENT_BRANCHES = ("dev", "production")

shipit_schema = {
    Optional("deployment_branch"): Any(str, None),
    Optional("deploy"): Any(True, False, None),
}

extend_parameters_schema(shipit_schema)


def get_decision_parameters(graph_config, parameters):
    """Add repo-specific decision parameters.
    """
    if parameters["tasks_for"] == "github-pull-request":
        parameters["deployment_branch"] = "github-pull-request"
    elif parameters["head_ref"].startswith("refs/heads/"):
        parameters["deployment_branch"] = parameters["head_ref"].replace("refs/heads/", "")
        if parameters["deployment_branch"] in DEPLOYMENT_BRANCHES and parameters["level"] == "3":
            parameters["deploy"] = True
