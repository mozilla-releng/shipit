import enum


@enum.unique
class Product(enum.Enum):
    ANDROID_COMPONENTS = "android-components"  # Only used for product details
    APP_SERVICES = "app-services"
    DEVEDITION = "devedition"
    PINEBUILD = "pinebuild"
    FIREFOX = "firefox"
    FENIX = "fenix"  # Only used for product details
    FENNEC = "fennec"  # Only used for product details
    THUNDERBIRD = "thunderbird"
    FOCUS_ANDROID = "focus-android"  # Only used for product details
    FIREFOX_ANDROID = "firefox-android"
    MOZILLA_VPN = "mozilla-vpn"


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
