# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Create a task per job substitute-version
"""

from copy import deepcopy

from taskgraph.transforms.base import TransformSequence


transforms = TransformSequence()


def _replace_string(obj, subs):
    if isinstance(obj, dict):
        return {k: v.format(**subs) for k, v in obj.items()}
    elif isinstance(obj, list):
        for c in range(0, len(obj)):
            obj[c] = obj[c].format(**subs)
    else:
        obj = obj.format(**subs)
    return obj


def _resolve_replace_string(item, field, subs):
    # largely from resolve_keyed_by
    container, subfield = item, field
    while '.' in subfield:
        f, subfield = subfield.split('.', 1)
        if f not in container:
            return item
        container = container[f]
        if not isinstance(container, dict):
            return item

    if subfield not in container:
        return item

    container[subfield] = _replace_string(container[subfield], subs)
    return item



@transforms.add
def tasks_per_version(config, jobs):
    fields = [
        "description",
        "docker-repo",
        "run.command",
        "worker.command",
        "worker.docker-image",
    ]
    for job in jobs:
        for substitute_version in job.pop("substitute-versions"):
            task = deepcopy(job)
            subs = {"name": job["name"], "substitute_version": substitute_version}
            for field in fields:
                _resolve_replace_string(task, field, subs)
            task["attributes"]["substitute-version"] = substitute_version
            yield task


@transforms.add
def update_name_with_version(config, jobs):
    for job in jobs:
        job["name"] = "{}-{}".format(job["name"], job["attributes"]["substitute-version"])
        yield job
