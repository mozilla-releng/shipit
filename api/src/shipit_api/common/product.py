import enum

from backend_common import get_product_names


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


Product = enum.Enum("Product", {get_key(product): product for product in get_product_names(include_legacy=True)})
