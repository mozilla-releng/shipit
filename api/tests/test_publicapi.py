# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pathlib import Path

import yaml

from cli_common.openapi_subset import PUBLIC_API_SECTIONS, extract


def test_public_api_subset():
    full_api_file = Path(__file__).parent.parent / "src/shipit_api/admin/api.yml"
    public_api_file = Path(__file__).parent.parent / "src/shipit_api/public/api.yml"
    full_api = yaml.safe_load(open(full_api_file))
    public_api = yaml.safe_load(open(public_api_file))
    generated_public_api = extract(full_api, PUBLIC_API_SECTIONS)
    # If this fails, check the diff; each file needs to match exactly, including the ordering of enum values
    assert generated_public_api == public_api
