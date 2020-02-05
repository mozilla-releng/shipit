import enum


@enum.unique
class Product(enum.Enum):
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
