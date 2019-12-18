"""
Generate subset of OpenAPI specification

This script is used to generate a subset of OpenAPI api.yml spec.

Example:
    python openapi_subset.py api.yml api_public.yml
"""

import sys

import dpath
import oyaml as yaml  # oyaml preserves the order of the original document

# Sections to be copied from the original document, separated by "." (period).
sections = [
    "openapi",
    "info",
    "servers",
    "paths./releases.get",
    "paths./releases/{name}.get",
    "paths./releases/{name}/{phase}.get",
    "components.schemas.Phase",
    "components.schemas.Release",
    "components.schemas.Signoffs",
    "components.schemas.Signoff",
    "components.schemas.DisableProduct",
]


def main(input_file, output_file):

    full_api = yaml.safe_load(open(input_file))

    subset = {}
    for section in sections:
        source = dpath.util.get(full_api, section, separator=".")
        dpath.util.new(subset, section, source, separator=".")

    yaml.safe_dump(subset, open(output_file, "w"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
