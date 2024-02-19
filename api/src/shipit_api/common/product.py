import enum
import pathlib
from functools import cache

import yaml

_CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
_SWAGGER_API_YML_PATH = (_CURRENT_DIR / ".." / ".." / "backend_common" / "api.yml").resolve()
_PRODUCT_ENUM_KEYS = "components.schemas.ProductOutput.enum"


@enum.unique
class ProductCategory(enum.Enum):
    MAJOR = "major"
    DEVELOPMENT = "dev"
    STABILITY = "stability"
    ESR = "esr"


# Keys of Product will have underscores where the product name may have hyphens.
# So all hyphens are translated to underscores as a rule.
def get_key(name):
    return name.upper().replace("-", "_")


def _resolve_dict_keys(dict_, keys):
    value = dict_
    path = keys.split(".")
    for key in path:
        value = value[key]
    return value


@cache
def _generate_product_enum():
    with open(_SWAGGER_API_YML_PATH) as f:
        swagger_spec = yaml.load(f, Loader=yaml.CLoader)

    try:
        products = _resolve_dict_keys(swagger_spec, _PRODUCT_ENUM_KEYS)
    except KeyError:
        raise KeyError(f"Cannot find in keys {_PRODUCT_ENUM_KEYS}: {_SWAGGER_API_YML_PATH}")

    return enum.Enum("Product", {get_key(product): product for product in products})


Product = _generate_product_enum()
