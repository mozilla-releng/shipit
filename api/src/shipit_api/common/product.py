import enum


@enum.unique
class Product(enum.Enum):
    ANDROID_COMPONENTS = "android-components"
    DEVEDITION = "devedition"
    FIREFOX = "firefox"
    FENIX = "fenix"
    FENNEC = "fennec"
    THUNDERBIRD = "thunderbird"


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
