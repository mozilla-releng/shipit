from pathlib import Path

import pytest
from openapi_spec_validator import validate

from backend_common import build_api_specification


@pytest.mark.parametrize("api_name", ("admin", "public"))
def test_validate_spec(api_name):
    root_dir = Path(__file__).parent.parent / "src/shipit_api" / api_name
    spec_dict = build_api_specification(root_dir)
    validate(spec_dict)
