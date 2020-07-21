# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.parameters import extend_parameters_schema
from voluptuous import (
    Any,
    Optional,
)

PUSH_TAGS = ("dev", "production")

shipit_schema = {
    Optional('docker_tag'): Any(basestring, None),
    Optional('push_docker_image'): Any(True, False, None),
}

extend_parameters_schema(shipit_schema)


def get_decision_parameters(graph_config, parameters):
    """Add repo-specific decision parameters.
    """
    if parameters["tasks_for"] == "github-pull-request":
        parameters["docker_tag"] = "github-pull-request"
    elif parameters["head_ref"].startswith("refs/heads/"):
        parameters["docker_tag"] = parameters["head_ref"].replace("refs/heads/", "")
        if parameters["docker_tag"] in PUSH_TAGS and parameters["level"] == "3":
            parameters["push_docker_image"] = True
