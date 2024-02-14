import importlib
from functools import cache

from backend_common import get_products_config
from shipit_api.common.product import Product, get_key


@cache
def _get_version_class_per_product_name():
    version_class_per_product = {}
    for product_name, product_config in get_products_config().items():
        product_enum = Product[get_key(product_name)]
        version_class_path = product_config["version-class"]
        module_path = ".".join(version_class_path.split(".")[:-1])
        class_name = version_class_path.split(".")[-1]
        VersionClass = getattr(importlib.import_module(module_path), class_name, None)
        version_class_per_product[product_enum] = VersionClass

    return version_class_per_product


def parse_version(product, version):
    if isinstance(product, Product):
        product_enum = product
    else:
        try:
            product_enum = Product[get_key(product)]
        except KeyError:
            raise ValueError(f"Product {product} versions are not supported")

    try:
        VersionClass = _get_version_class_per_product_name()[product_enum]
    except KeyError:
        raise ValueError(f"Product {product} versions are not supported")

    return VersionClass.parse(version)
