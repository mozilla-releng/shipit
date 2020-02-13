# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import sys

import dpath.util
import oyaml

# Sections to be copied from the original document, separated by "." (period).
PUBLIC_API_SECTIONS = [
    "openapi",
    "info",
    "servers",
    "paths./releases.get",
    "paths./releases/{name}.get",
    "paths./releases/{name}/{phase}.get",
    "paths./disabled-products.get",
    "components.schemas.Phase",
    "components.schemas.Release",
    "components.schemas.Signoffs",
    "components.schemas.Signoff",
    "components.schemas.DisableProduct",
]


def extract(full_api, sections):
    subset = {}
    for section in sections:
        source = dpath.util.get(full_api, section, separator=".")
        dpath.util.new(subset, section, source, separator=".")
    return subset


def main(input_file, output_file):
    full_api = oyaml.safe_load(open(input_file))
    subset = extract(full_api, PUBLIC_API_SECTIONS)
    oyaml.safe_dump(subset, open(output_file, "w"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
