import enum

from mozilla_version.gecko import GeckoVersion

from backend_common import get_product_names


@enum.unique
class ProductCategory(enum.Enum):
    MAJOR = "major"
    DEVELOPMENT = "dev"
    STABILITY = "stability"
    ESR = "esr"


def get_product_category(version: GeckoVersion):
    if version.is_major:
        return ProductCategory.MAJOR
    elif version.is_development:
        return ProductCategory.DEVELOPMENT
    elif version.is_stability:
        return ProductCategory.STABILITY
    elif version.is_esr:
        return ProductCategory.ESR
    raise ValueError(f"Unknown category for version: {version}")


# Keys of Product will have underscores where the product name may have hyphens.
# So all hyphens are translated to underscores as a rule.
def get_key(name):
    return name.upper().replace("-", "_")


Product = enum.Enum("Product", {get_key(product): product for product in get_product_names(include_legacy=True)})
