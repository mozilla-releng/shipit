# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import collections
import functools
import hashlib
import io
import json
import logging
import os
import pathlib
import re
import shutil
import typing
import urllib.parse
from datetime import datetime, timedelta, timezone

import aiohttp
import arrow
import backoff
import click
import mypy_extensions
import sqlalchemy
import sqlalchemy.orm
from mozilla_version.gecko import FirefoxVersion
from mozilla_version.mobile import MobileVersion

import cli_common.command
import cli_common.utils
import shipit_api.common.config
import shipit_api.common.models
from shipit_api.admin.release import parse_version
from shipit_api.common.product import Product, ProductCategory

logger = logging.getLogger(__name__)

File = str
ReleaseDetails = mypy_extensions.TypedDict(
    "ReleaseDetails",
    {"category": str, "product": str, "build_number": int, "description": typing.Optional[str], "is_security_driven": bool, "version": str, "date": str},
)
Releases = mypy_extensions.TypedDict("Releases", {"releases": typing.Dict[str, ReleaseDetails]})
L10n = str
ReleaseL10n = mypy_extensions.TypedDict("ReleaseL10n", {"platforms": typing.List[str], "revision": str})
ReleaseL10ns = typing.Dict[L10n, ReleaseL10n]
ReleasesHistory = typing.Dict[str, str]
PrimaryBuildDetails = mypy_extensions.TypedDict("PrimaryBuildDetails", {"filesize": float})
PrimaryBuild = mypy_extensions.TypedDict("PrimaryBuild", {"Linux": PrimaryBuildDetails, "OS X": PrimaryBuildDetails, "Windows": PrimaryBuildDetails})
PrimaryBuilds = typing.Dict[str, typing.Dict[str, PrimaryBuild]]
FirefoxVersions = mypy_extensions.TypedDict(
    "FirefoxVersions",
    {
        "FIREFOX_NIGHTLY": str,
        "FIREFOX_AURORA": str,
        "FIREFOX_ESR": str,
        "FIREFOX_ESR_NEXT": str,
        "FIREFOX_ESR115": str,
        "LATEST_FIREFOX_DEVEL_VERSION": str,
        "FIREFOX_DEVEDITION": str,
        "LATEST_FIREFOX_OLDER_VERSION": str,
        "LATEST_FIREFOX_RELEASED_DEVEL_VERSION": str,
        "LATEST_FIREFOX_VERSION": str,
        "LAST_SOFTFREEZE_DATE": str,
        "LAST_STRINGFREEZE_DATE": str,
        "LAST_MERGE_DATE": str,
        "LAST_RELEASE_DATE": str,
        "NEXT_SOFTFREEZE_DATE": str,
        "NEXT_STRINGFREEZE_DATE": str,
        "NEXT_MERGE_DATE": str,
        "NEXT_RELEASE_DATE": str,
    },
)
L10nChangeset = mypy_extensions.TypedDict("L10nChangeset", {"changeset": str})
L10n = mypy_extensions.TypedDict("L10n", {"locales": typing.Dict[str, L10nChangeset], "submittedAt": str, "shippedAt": str, "name": str})
Language = mypy_extensions.TypedDict("Language", {"English": str, "native": str})
Languages = typing.Dict[str, Language]
MobileDetailsBuildLocale = mypy_extensions.TypedDict("MobileDetailsBuildLocale", {"code": str, "english": str, "native": str})
MobileDetailsBuildDownload = mypy_extensions.TypedDict("MobileDetailsBuildDownload", {"android": str})
MobileDetailsBuild = mypy_extensions.TypedDict("MobileDetailsBuild", {"locale": MobileDetailsBuildLocale, "download": MobileDetailsBuildDownload})
MobileDetails = mypy_extensions.TypedDict(
    "MobileDetails",
    {
        "nightly_version": str,
        "alpha_version": str,
        "beta_version": str,
        "version": str,
        "ios_beta_version": str,
        "ios_version": str,
        "builds": typing.List[MobileDetailsBuild],
        "beta_builds": typing.List[MobileDetailsBuild],
        "alpha_builds": typing.List[MobileDetailsBuild],
    },
)
MobileVersions = mypy_extensions.TypedDict(
    "MobileVersions", {"nightly_version": str, "alpha_version": str, "beta_version": str, "version": str, "ios_beta_version": str, "ios_version": str}
)
Region = typing.Dict[str, str]
ThunderbirdVersions = mypy_extensions.TypedDict(
    "ThunderbirdVersions",
    {
        "LATEST_THUNDERBIRD_VERSION": str,
        "LATEST_THUNDERBIRD_ALPHA_VERSION": str,
        "LATEST_THUNDERBIRD_DEVEL_VERSION": str,
        "LATEST_THUNDERBIRD_NIGHTLY_VERSION": str,
        "THUNDERBIRD_ESR": str,
        "THUNDERBIRD_ESR_NEXT": str,
    },
)
IndexListing = str
ProductDetails = typing.Dict[
    File,
    typing.Union[
        Releases, ReleasesHistory, PrimaryBuilds, FirefoxVersions, MobileVersions, MobileDetails, Region, L10n, Languages, ThunderbirdVersions, IndexListing
    ],
]
Products = typing.List[Product]

A = typing.TypeVar("A")
B = typing.TypeVar("B")


def with_default(a: typing.Optional[A], func: typing.Callable[[A], B], default: B) -> B:
    if a is None:
        return default
    return func(a)


def to_isoformat(d: datetime) -> str:
    return arrow.get(d).isoformat()


def from_isoformat(s: str) -> datetime:
    return datetime.fromisoformat(s)


def to_format(d: datetime, format: str) -> str:
    return arrow.get(d).format(format)


def from_format(s: str, format: str) -> datetime:
    return datetime.strptime(s, format)


YMD_DATE_FORMAT = "%Y-%m-%d"


def iso_to_ymd(s: str) -> str:
    return from_isoformat(s).strftime(YMD_DATE_FORMAT)


def dt_to_ymd(d: datetime) -> str:
    return d.strftime(YMD_DATE_FORMAT)


def from_ymd_format(s: str) -> datetime:
    return from_format(s, YMD_DATE_FORMAT)


def create_index_listing_html(folder: pathlib.Path, items: typing.Set[pathlib.Path]) -> str:
    folder = "/" / folder  # noqa : T484 Unsupported left operand type for / ("str")
    with io.StringIO() as html:

        def write(x):
            return html.write(f"{x}{os.linesep}")

        write("<!doctype html>")
        write("<html>")
        write("  <head>")
        write(f"    <title>Index of {folder}</title>")
        write("  </head>")
        write("  <body>")
        write(f"    <h1>Index of {folder}</h1>")
        write("    <ul>")
        if folder != folder.parent:
            write(f'      <li><a href="{folder.parent}">Parent Directory</a></li>')
        for item in sorted(items):
            is_dir = item.suffix not in [".json", ".html"]
            itemStr = is_dir and f"{item.name}/" or f"{item.name}"
            write(f'      <li><a href="{itemStr}">{itemStr}</a></li>')
        write("    </ul>")
        write("  </body>")
        write("</html>")

        return html.getvalue()


def create_index_listing(product_details: ProductDetails) -> ProductDetails:
    new_product_details: ProductDetails = dict()
    folders: typing.Dict[pathlib.Path, typing.List[pathlib.Path]] = dict()

    for file_, content in product_details.items():
        new_product_details[file_] = content

        path = pathlib.Path(file_)
        for folder in list(path.parents):
            folders.setdefault(folder, [])
            folders[folder].append(path)
            path = folder

    for folder, items in folders.items():
        new_product_details[str(folder / "index.html")] = create_index_listing_html(folder, set(items))

    return new_product_details


@backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_time=60)
async def fetch_l10n_data(
    session: aiohttp.ClientSession, release: shipit_api.common.models.Release, raise_on_failure: bool, use_cache: bool = True
) -> typing.Tuple[shipit_api.common.models.Release, typing.Optional[ReleaseL10ns]]:
    # Fenix and some thunderbird on the betas don't have l10n in the repository
    if (
        Product(release.product) is Product.THUNDERBIRD
        and release.branch == "releases/comm-beta"
        and release.revision in ["3e01e0dc6943", "481fea2011e6", "85cb8f907b18", "92950b2fd2dc", "c614b6e7cf58", "e277e3f0ab13", "efd290b55a35", "f87ba53e04ff"]
    ) or Product(release.product) in (Product.FENIX, Product.ANDROID_COMPONENTS, Product.FOCUS_ANDROID, Product.FIREFOX_ANDROID, Product.APP_SERVICES):
        return (release, None)

    url_file = {
        Product.FIREFOX: "browser/locales/l10n-changesets.json",
        Product.DEVEDITION: "browser/locales/l10n-changesets.json",
        Product.THUNDERBIRD: "mail/locales/l10n-changesets.json",
    }[Product(release.product)]
    url = f"{shipit_api.common.config.HG_PREFIX}/{release.branch}/raw-file/{release.revision}/{url_file}"

    cache_dir = shipit_api.common.config.PRODUCT_DETAILS_CACHE_DIR / "fetch_l10n_data"
    cache = cache_dir / hashlib.sha256(url.encode("utf-8")).hexdigest()
    if use_cache:
        os.makedirs(cache_dir, exist_ok=True)
        if cache.exists():
            logger.debug(f"Cache hit for {url}")
            with cache.open() as f:
                changesets = json.load(f)
            return (release, changesets)

    logger.debug(f"Fetching {url}")
    changesets = dict()
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            logger.debug(f"Fetched {url}")
            changesets = await response.json()
            if use_cache:
                with cache.open("w+") as f:
                    f.write(json.dumps(changesets))
    except Exception:
        logger.info("Failed to fetch %s, %s", url, release.json)
        if raise_on_failure:
            raise

    return (release, changesets)


def get_old_product_details(directory: str) -> ProductDetails:
    if not os.path.isdir(directory):
        return dict()

    data = dict()
    for root_, _, files in os.walk(directory):
        root = pathlib.Path(root_)
        for file__ in files:
            if not file__.endswith(".json"):
                continue
            file_ = root / file__
            with file_.open() as f:
                data[str(file_.relative_to(directory))] = json.load(f)

    return data


def get_releases_from_db(db_session: sqlalchemy.orm.Session, breakpoint_version: int) -> typing.List[shipit_api.common.models.Release]:
    """
    SELECT *
    FROM shipit_api_releases as r
    WHERE cast(split_part(r.version, '.', 1) as int) > 20;
    """
    Release = shipit_api.common.models.Release
    query = db_session.query(Release)
    # Using cast and split_part is postgresql specific
    query = query.filter(Release.status == "shipped")
    query = query.filter(sqlalchemy.cast(sqlalchemy.func.split_part(Release.version, ".", 1), sqlalchemy.Integer) >= breakpoint_version)
    return query.all()


def get_product_channel_version(db_session: sqlalchemy.orm.Session, product: str, channel: str):
    Version = shipit_api.common.models.Version
    query = db_session.query(Version)
    version = query.filter_by(product_name=product, product_channel=channel).first()
    return version.current_version


def get_product_categories(product: Product, version: str) -> typing.List[ProductCategory]:
    # typically, these are dot releases that are considered major
    SPECIAL_FIREFOX_MAJORS = ["14.0.1", "125.0.1"]
    SPECIAL_THUNDERBIRD_MAJORS = ["14.0.1", "38.0.1"]

    def patternize_versions(versions):
        if not versions:
            return ""
        return "|" + "|".join([v.replace(r".", r"\.") for v in versions])

    categories = []
    categories_mapping: typing.List[typing.Tuple[ProductCategory, str]] = []

    if product is Product.THUNDERBIRD:
        special_majors = patternize_versions(SPECIAL_THUNDERBIRD_MAJORS)
    else:
        special_majors = patternize_versions(SPECIAL_FIREFOX_MAJORS)

    categories_mapping.append((ProductCategory.MAJOR, r"([0-9]+\.[0-9]+%s)$" % special_majors))
    categories_mapping.append((ProductCategory.MAJOR, r"([0-9]+\.[0-9]+(esr|)%s)$" % special_majors))
    categories_mapping.append((ProductCategory.STABILITY, r"([0-9]+\.[0-9]+\.[0-9]+$|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$)"))
    categories_mapping.append((ProductCategory.STABILITY, r"([0-9]+\.[0-9]+\.[0-9]+(esr|)$|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(esr|)$)"))
    # We had 38.0.5b2
    categories_mapping.append((ProductCategory.DEVELOPMENT, r"([0-9]+\.[0-9]|[0-9]+\.[0-9]+\.[0-9])(b|rc|build|plugin)[0-9]+$"))

    # Ugly hack to manage the next ESR (when we have two overlapping esr)
    if shipit_api.common.config.ESR_NEXT:
        categories_mapping.append((ProductCategory.ESR, shipit_api.common.config.ESR_NEXT + r"(\.[0-9]+){1,2}esr$"))
    else:
        categories_mapping.append((ProductCategory.ESR, shipit_api.common.config.CURRENT_ESR + r"(\.[0-9]+){1,2}esr$"))

    for product_category, version_pattern in categories_mapping:
        if re.match(version_pattern, version):
            categories.append(product_category)

    return categories


def get_releases(
    breakpoint_version: int, products: Products, releases: typing.List[shipit_api.common.models.Release], old_product_details: ProductDetails
) -> Releases:
    """This file holds historical information about all Firefox, Firefox for
    Mobile (aka Fennec), Firefox Dev Edition and Thunderbird releases we
    shipped in the past.

    This function will output to the following files:
     - all.json
     - devedition.json
     - firefox.json
     - mobile_android.json
     - thunderbird.json

    Example:::

        "firefox-58.0": {
            "category":           "major",
            "product":            "firefox",
            "build_number":       6,
            "description":        "",
            "is_security_driven": false,
            "version":            "58.0",
            "date":               "2018-01-23",
        }
    """
    details = dict()

    for product in products:
        #
        # get release details from the JSON files up to breakpoint_version
        #
        product_file = f"1.0/{product.value}.json"
        if product in [Product.FENNEC, Product.FENIX, Product.FIREFOX_ANDROID]:
            product_file = "1.0/mobile_android.json"

        old_releases = typing.cast(typing.Dict[str, ReleaseDetails], old_product_details.get(product_file, {}).get("releases", dict()))  # noqa
        for product_with_version in old_releases:
            # product_with_version looks like "Fennec-1.0". There is nothing after the version
            if "-" not in product_with_version:
                raise ValueError(f'Invalid product_with_version "{product_with_version}". It must contain a -')
            product_string, version_string = product_with_version.rsplit("-", 1)

            # XXX Both Fennec and Fenix output to mobile_android.json. We don't want to
            # parse Fennec version number as if it were Fenix because the parser is
            # strict. So, this skip statement below is to make sure we don't try to
            # parse version numbers with the wrong parser.
            if product_string.lower() != product.value.lower():
                continue

            version = parse_version(product, version_string)
            if version.major_number >= breakpoint_version:
                continue
            details[product_with_version] = old_releases[product_with_version]

        #
        # get release history from the database
        #
        for release in releases:
            if release.product != product.value:
                continue
            categories = get_product_categories(Product(release.product), release.version)
            release_version = release.version
            for category in categories:
                if release_version.endswith("esr"):
                    release_version = release_version[: -len("esr")]
                details[f"{release.product}-{release.version}"] = dict(
                    category=category.value,
                    product=release.product,
                    build_number=release.build_number,
                    description=None,
                    is_security_driven=False,  # TODO: we don't have this field anymore
                    version=release_version,
                    date=with_default(release.completed, functools.partial(to_format, format="YYYY-MM-DD"), default=""),
                )

    return dict(releases=details)


def get_release_history(
    breakpoint_version: int,
    product: Product,
    product_category: ProductCategory,
    releases: typing.List[shipit_api.common.models.Release],
    old_product_details: ProductDetails,
) -> ReleasesHistory:
    """This file contains all the Product release dates for releases in that
    category.

    This function will output to the following files:
     - firefox_history_development_releases.json
     - firefox_history_major_releases.json
     - firefox_history_stability_releases.json
     - mobile_history_development_releases.json
     - mobile_history_major_releases.json
     - mobile_history_stability_releases.json
     - thunderbird_history_development_releases.json
     - thunderbird_history_major_releases.json
     - thunderbird_history_stability_releases.json

    Example:::

        {
            ...
            "59.0b11": "2018-02-20",
            "59.0b12": "2018-02-23",
            "59.0b13": "2018-02-27",
            "59.0b14": "2018-03-02",
            ...
        }
    """
    if Product.DEVEDITION is product:
        raise click.ClickException(f'We don\'t generate product history for "{product.value}" product.')

    if ProductCategory.ESR is product_category:
        raise click.ClickException(f'We don\'t generate product history for "{product_category.value}" product category.')

    history = dict()

    #
    # Get release history from the JSON files up to breakpoint_version.
    # There are 2 reasons we use this method:
    #
    # 1. To speed up product details generation. All releases before the
    # breakpoint version, will be used as they are presented in the JSON files.
    # As a result they won't be retrieved from the database, and more
    # importantly, the corresponding l10n data won't be fetched from
    # hg.mozilla.org.
    #
    # 2. Some really old releases use different data structure (versioning,
    # l10n info, branches, etc). Instead of creating a special case per
    # exception, we just serve the data as is.
    product_file = f"1.0/{product.value}_history_{product_category.name.lower()}_releases.json"
    if product in [Product.FENNEC, Product.FENIX, Product.FIREFOX_ANDROID]:
        product_file = f"1.0/mobile_history_{product_category.name.lower()}_releases.json"

    old_history = typing.cast(ReleasesHistory, old_product_details.get(product_file, {}))
    for version_string in old_history:
        version = parse_version(product, version_string)
        if version.major_number >= breakpoint_version:
            continue
        history[version_string] = old_history[version_string]

    #
    # get release history from the database
    #
    for release in releases:
        if product.value != release.product:
            continue

        if release.status != "shipped":
            continue

        release_version = parse_version(release.product, release.version)
        if release_version is None or release_version.major_number < breakpoint_version:
            continue

        # short term hack: 125.0.1 is a major release. we should replace this with
        # something that uses MozillaVersion to determine categories
        if (
            product_category is ProductCategory.MAJOR
            and release_version.major_number == 125
            and release_version.patch_number == 1
            and release_version.beta_number is None
            and not release_version.is_esr
        ):
            # history_version is a copy of stuff further down - we need it now, before
            # this release gets skipped
            history_version = release.version
            if history_version.endswith("esr"):
                history_version = history_version[: -len("esr")]
            history[history_version] = with_default(release.completed, functools.partial(to_format, format="YYYY-MM-DD"), default="")
            continue

        # skip all releases which don't fit into product category
        if product_category is ProductCategory.MAJOR and (
            release_version.patch_number is not None or release_version.beta_number is not None or release_version.is_esr
        ):
            continue

        elif product_category is ProductCategory.DEVELOPMENT and (release_version.beta_number is None or release_version.is_esr):
            continue

        elif product_category is ProductCategory.STABILITY and (release_version.beta_number is not None or release_version.patch_number is None):
            continue

        history_version = release.version
        if history_version.endswith("esr"):
            history_version = history_version[: -len("esr")]

        history[history_version] = with_default(release.completed, functools.partial(to_format, format="YYYY-MM-DD"), default="")

    # Sort the releases in their chronological order
    # TODO: the consumers should not rely on this order, see bug 1541636
    ordered_history = collections.OrderedDict(sorted(history.items(), key=lambda x: x[1]))
    return ordered_history


async def get_primary_builds(
    breakpoint_version: int,
    product: Product,
    releases: typing.List[shipit_api.common.models.Release],
    releases_l10n: typing.Dict[shipit_api.common.models.Release, ReleaseL10ns],
    old_product_details: ProductDetails,
    firefox_nightly_version: str,
    thunderbird_nightly_version: str,
) -> PrimaryBuilds:
    """This file contains all the Thunderbird builds we provide per locale. The
    filesize fields have the same value for all lcoales, this is not a bug,
    we are keeping these fields with this schema for historical reasons only
    but no longer populate them with fresh data.

    This function will output to the following files:
     - firefox_primary_builds.json
     - thunderbird_primary_builds.json

    Example:::

        {
            "el": {
                "52.6.0": {
                    "Windows": {
                        "filesize": 25.1,
                    },
                    "OS X": {
                        "filesize": 50.8,
                    },
                    "Linux": {
                        "filesize": 31.8,
                    },
                },
            }
        }
    """

    if product is Product.FIREFOX:
        firefox_versions = await get_firefox_versions(releases, firefox_nightly_version)
        # make sure that Devedition is included in the list
        products = [Product.FIREFOX, Product.DEVEDITION]
        versions = set(
            [
                firefox_versions["FIREFOX_NIGHTLY"],
                firefox_versions["FIREFOX_DEVEDITION"],
                firefox_versions["LATEST_FIREFOX_RELEASED_DEVEL_VERSION"],
                firefox_versions["LATEST_FIREFOX_VERSION"],
                firefox_versions["FIREFOX_ESR"],
            ]
        )
        if firefox_versions["FIREFOX_ESR_NEXT"]:
            versions.add(firefox_versions["FIREFOX_ESR_NEXT"])
        if firefox_versions["FIREFOX_ESR115"]:
            versions.add(firefox_versions["FIREFOX_ESR115"])
    elif product is Product.THUNDERBIRD:
        thunderbird_versions = get_thunderbird_versions(releases, thunderbird_nightly_version)
        products = [Product.THUNDERBIRD]
        versions = set(
            [
                thunderbird_versions["LATEST_THUNDERBIRD_VERSION"],
                thunderbird_versions["LATEST_THUNDERBIRD_DEVEL_VERSION"],
                thunderbird_versions["LATEST_THUNDERBIRD_NIGHTLY_VERSION"],
                thunderbird_versions["THUNDERBIRD_ESR"],
            ]
        )
        if thunderbird_versions["THUNDERBIRD_ESR_NEXT"]:
            versions.add(thunderbird_versions["THUNDERBIRD_ESR_NEXT"])
    else:
        raise click.ClickException(f'We don\'t generate product history for "{product.value}" product.')

    builds: PrimaryBuilds = dict()

    for release in releases:
        # Skip other products and older versions
        if Product(release.product) not in products or release.version not in versions:
            continue
        # Make sure to add en-US, it's not listed in the l10n changesets file
        for l10n in list(releases_l10n.get(release, {}).keys()) + ["en-US"]:
            # for compatibility with shipit v1, skip ja-JP-mac
            if l10n == "ja-JP-mac":
                continue
            builds.setdefault(l10n, dict())
            if product is Product.THUNDERBIRD:
                builds[l10n][release.version] = {"Windows": {"filesize": 25.1}, "OS X": {"filesize": 50.8}, "Linux": {"filesize": 31.8}}
            else:
                builds[l10n][release.version] = {"Windows": {"filesize": 0}, "OS X": {"filesize": 0}, "Linux": {"filesize": 0}}

    return builds


def get_latest_version(
    releases: typing.List[shipit_api.common.models.Release], product: Product, branch: str = None, filter_closure: typing.Optional[typing.Callable] = None
) -> str:
    """Get latest version

    Get the latest shipped version for a particular branch/product,
    optionally for a particular major version. The results should be sorted
    by version, not by date, because we may publish a correction release
    for old users (this has been done in the past).
    """
    filtered_releases = [r for r in releases if r.product == product.value and (r.branch == branch if branch else True)]
    if filter_closure:
        filtered_releases = list(filter(filter_closure, filtered_releases))
    releases_ = sorted(filtered_releases, reverse=True, key=lambda r: parse_version(product, r.version))
    if len(releases_) == 0:
        # XXX: should we fallback to old_product_details?
        return ""
    return releases_[0].version


def get_firefox_esr_version(releases: typing.List[shipit_api.common.models.Release], branch: str, product: Product) -> str:
    """Return latest ESR version

    Get the latest version using CURRENT_ESR major version. Sometimes, when we
    have 2 overlapping ESR releases we want to point this to the older version,
    while ESR_NEXT will be pointing to the next release.
    """
    return get_latest_version(releases, product, branch)


def get_firefox_esr_next_version(releases: typing.List[shipit_api.common.models.Release], branch: str, product: Product, esr_next: typing.Optional[str]) -> str:
    """Next ESR version

    Return an empty string when there is only one ESR release published. If
    ESR_NEXT is set to a false value, return an empty string. Otherwise get
    latest version for ESR_NEXT major version.
    """
    if not esr_next:
        return ""
    else:
        return get_latest_version(releases, product, branch)


@backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_time=60)
async def fetch_firefox_release_schedule_data(
    releases: typing.List[shipit_api.common.models.Release], session: aiohttp.ClientSession, firefox_nightly_version: str
):
    firefox_nightly_mozilla_version = FirefoxVersion.parse(firefox_nightly_version)
    current_nightly_version_major_number = firefox_nightly_mozilla_version.major_number
    previous_nightly_version_major_number = current_nightly_version_major_number - 1
    url_template = "https://whattrainisitnow.com/api/release/schedule/?version={version}"
    try:
        url = url_template.format(version=current_nightly_version_major_number)
        async with session.get(url) as response:
            response.raise_for_status()
            logger.debug(f"Fetched {url}")
            current_nightly_version_schedule = await response.json()
        url = url_template.format(version=previous_nightly_version_major_number)
        async with session.get(url) as response:
            response.raise_for_status()
            logger.debug(f"Fetched {url}")
            previous_nightly_version_schedule = await response.json()
    except Exception:
        logger.info("Failed to fetch %s", url)
        raise
    last_softfreeze_date = iso_to_ymd(previous_nightly_version_schedule["soft_code_freeze"])
    last_merge_date = iso_to_ymd(previous_nightly_version_schedule["merge_day"])
    releases_after_last_merge_date = sorted(
        [
            release
            for release in releases
            if release.product == Product.FIREFOX.value
            and FirefoxVersion.parse(release.version).is_release
            and release.status == "shipped"
            and release.completed is not None
            and release.completed.replace(tzinfo=timezone.utc) > from_isoformat(previous_nightly_version_schedule["merge_day"])
        ],
        key=lambda release: FirefoxVersion.parse(release.version),
    )
    if not releases_after_last_merge_date:
        logger.info(f"No Firefox releases shipped after the last merge date ({last_merge_date})")
        last_release_date = dt_to_ymd(from_ymd_format(last_merge_date) + timedelta(days=1))
        logger.info(f"Assuming a Firefox release will be shipped on {last_release_date} (the day after the last merge date)")
    else:
        first_release_after_last_merge_date = releases_after_last_merge_date[0]
        last_release_date = dt_to_ymd(first_release_after_last_merge_date.completed)
    next_softfreeze_date = iso_to_ymd(current_nightly_version_schedule["soft_code_freeze"])
    next_merge_date = iso_to_ymd(current_nightly_version_schedule["merge_day"])
    next_release_date = dt_to_ymd(from_isoformat(current_nightly_version_schedule["merge_day"]) + timedelta(days=1))
    last_stringfreeze_date = dt_to_ymd(from_ymd_format(last_softfreeze_date) + timedelta(days=1))
    next_stringfreeze_date = dt_to_ymd(from_ymd_format(next_softfreeze_date) + timedelta(days=1))
    return {
        "LAST_SOFTFREEZE_DATE": last_softfreeze_date,
        "LAST_MERGE_DATE": last_merge_date,
        "LAST_RELEASE_DATE": last_release_date,
        "NEXT_SOFTFREEZE_DATE": next_softfreeze_date,
        "NEXT_MERGE_DATE": next_merge_date,
        "NEXT_RELEASE_DATE": next_release_date,
        "LAST_STRINGFREEZE_DATE": last_stringfreeze_date,
        "NEXT_STRINGFREEZE_DATE": next_stringfreeze_date,
    }


async def get_firefox_versions(releases: typing.List[shipit_api.common.models.Release], firefox_nightly_version: str) -> FirefoxVersions:
    """All the versions we ship for Firefox for Desktop

    This function will output to the following files:
     - firefox_versions.json

    Example:::
        {
            "FIREFOX_NIGHTLY":                        "60.0a1",
            "FIREFOX_AURORA":                         "",
            "FIREFOX_ESR":                            "52.6.0esr",
            "FIREFOX_ESR_NEXT":                       "",
            "LATEST_FIREFOX_DEVEL_VERSION":           "59.0b14",
            "FIREFOX_DEVEDITION":                     "59.0b14",
            "LATEST_FIREFOX_OLDER_VERSION":           "3.6.28",
            "LATEST_FIREFOX_RELEASED_DEVEL_VERSION":  "59.0b14",
            "LATEST_FIREFOX_VERSION":                 "58.0.2",
            "LAST_SOFTFREEZE_DATE":                   "2019-03-11",
            "LAST_STRINGFREEZE_DATE":                 "2019-03-12",
            "LAST_MERGE_DATE":                        "2019-03-18",
            "LAST_RELEASE_DATE":                      "2019-03-19",
            "NEXT_SOFTFREEZE_DATE":                   "2019-05-06",
            "NEXT_STRINGFREEZE_DATE":                 "2019-05-07",
            "NEXT_MERGE_DATE":                        "2019-05-13",
            "NEXT_RELEASE_DATE":                      "2019-05-14"
        }
    """
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=50), timeout=aiohttp.ClientTimeout(total=30)) as session:
        firefox_release_schedule_data = await fetch_firefox_release_schedule_data(releases, session, firefox_nightly_version)

    return dict(
        FIREFOX_NIGHTLY=firefox_nightly_version,
        FIREFOX_AURORA=shipit_api.common.config.FIREFOX_AURORA,
        LATEST_FIREFOX_VERSION=get_latest_version(releases, Product.FIREFOX, shipit_api.common.config.RELEASE_BRANCH),
        FIREFOX_ESR=get_firefox_esr_version(releases, f"{shipit_api.common.config.ESR_BRANCH_PREFIX}{shipit_api.common.config.CURRENT_ESR}", Product.FIREFOX),
        FIREFOX_ESR_NEXT=get_firefox_esr_next_version(
            releases, f"{shipit_api.common.config.ESR_BRANCH_PREFIX}{shipit_api.common.config.ESR_NEXT}", Product.FIREFOX, shipit_api.common.config.ESR_NEXT
        ),
        FIREFOX_ESR115=get_firefox_esr_next_version(releases, f"{shipit_api.common.config.ESR_BRANCH_PREFIX}115", Product.FIREFOX, "115"),
        LATEST_FIREFOX_DEVEL_VERSION=get_latest_version(releases, Product.FIREFOX, shipit_api.common.config.BETA_BRANCH),
        LATEST_FIREFOX_RELEASED_DEVEL_VERSION=get_latest_version(releases, Product.FIREFOX, shipit_api.common.config.BETA_BRANCH),
        FIREFOX_DEVEDITION=get_latest_version(releases, Product.DEVEDITION, shipit_api.common.config.BETA_BRANCH),
        LATEST_FIREFOX_OLDER_VERSION=shipit_api.common.config.LATEST_FIREFOX_OLDER_VERSION,
        LAST_SOFTFREEZE_DATE=firefox_release_schedule_data["LAST_SOFTFREEZE_DATE"],
        LAST_STRINGFREEZE_DATE=firefox_release_schedule_data["LAST_STRINGFREEZE_DATE"],
        LAST_MERGE_DATE=firefox_release_schedule_data["LAST_MERGE_DATE"],
        LAST_RELEASE_DATE=firefox_release_schedule_data["LAST_RELEASE_DATE"],
        NEXT_SOFTFREEZE_DATE=firefox_release_schedule_data["NEXT_SOFTFREEZE_DATE"],
        NEXT_STRINGFREEZE_DATE=firefox_release_schedule_data["NEXT_STRINGFREEZE_DATE"],
        NEXT_MERGE_DATE=firefox_release_schedule_data["NEXT_MERGE_DATE"],
        NEXT_RELEASE_DATE=firefox_release_schedule_data["NEXT_RELEASE_DATE"],
    )


def get_regions(old_product_details: ProductDetails) -> ProductDetails:
    """The files in this folder store the localized names for countries. The
    data was extracted from our Gecko localization files and converted to
    JSON as we needed it for projects that needed to associate product and
    regional data. Those files are updated by the l10n-drivers team.

    This function will output to the following files:
     - regions.json

    Example:::

        {
            "af": "Afghanistan",
            "za": "Afrique du Sud",
            "qz": "Akrotiri",
            "al": "Albanie",
            ...
        }
    """
    regions: ProductDetails = dict()
    for file_, content in old_product_details.items():
        if file_.startswith("1.0/regions/"):
            regions[file_[len("1.0/") :]] = content
    return regions


def get_l10n(
    releases: typing.List[shipit_api.common.models.Release],
    releases_l10n: typing.Dict[shipit_api.common.models.Release, ReleaseL10ns],
    old_product_details: ProductDetails,
) -> ProductDetails:
    """This folder contains the l10n changeset per locale used for each build.
    The translation of our products is done in separate l10n repositories,
    each locale provides a good known version of their translations through
    a sign off process with l10n-drivers and these changeset per locale are
    used to build Firefox, Thunderbird and Fennec.

    This function will output to the following files:
     - l10n/<file>.json

    Example for l10n/Firefox-58.0-build6.json file:::
        {
            "locales": {
                "pa-IN": {
                    "changeset": "5634ac6e7d9b",
                },
                "gd": {
                    "changeset": "da7de9b6e635",
                },
                …
            },
            "submittedAt": "2018-01-18T22:53:08+00:00",
            "shippedAt": "2018-01-23T13:20:26+00:00",
            "name": "Firefox-58.0-build6",
        }
    """
    # populate with old data first, stripping the '1.0/' prefix
    data: ProductDetails = {file_.replace("1.0/", ""): content for file_, content in old_product_details.items() if file_.startswith("1.0/l10n/")}

    for release, locales in releases_l10n.items():
        # XXX: for some reason we didn't generate l10n for devedition in old_product_details
        if Product(release.product) is Product.DEVEDITION:
            continue
        data[f"l10n/{release.name}.json"] = {
            "locales": {locale: dict(changeset=content["revision"]) for locale, content in locales.items()},
            "submittedAt": with_default(release.created, to_isoformat, default=""),
            "shippedAt": with_default(release.completed, to_isoformat, default=""),
            "name": release.name,
        }

    return data


def get_languages(old_product_details: ProductDetails) -> Languages:
    """List of all the supported BCP-47 locales with their English and native names.

    This function will output to the following files:
     - languages.json

    Example:::

        {
            "cs": {
                "English": "Czech",
                "native":  "Čeština",
            },
            "csb": {
                "English": "Kashubian",
                "native":  "Kaszëbsczi",
            },
            "cy": {
                "English": "Welsh",
                "native":  "Cymraeg",
            },
            ...
        }

    """
    languages = old_product_details.get("1.0/languages.json")

    if languages is None:
        raise click.ClickException('"1.0/languages.json" does not exist in old product details"')

    # I can not use isinstance with generics (like Languages) for this reason
    # I'm casting to output type
    # https://gist.github.com/garbas/0cf4b6c3c34d1aa311225df283db19a6

    return typing.cast(Languages, languages)


def get_mobile_details(releases: typing.List[shipit_api.common.models.Release], firefox_nightly_version: str) -> MobileDetails:
    """This file contains all the release information for Firefox for Android
    and Firefox for iOS. We are keeping this file around for backward
    compatibility with consumers and only the version numbers are updated
    today. The builds, beta_builds and alpha_builds sections are static.

    If you are interested in getting the version number we ship per channel
    use mobile_versions.json instead of this file.

    This function will output to the following files:
     - mobile_details.json

    Example:::
        {
            "nightly_version": "60.0a1",
            "alpha_version": "60.0a1",
            "beta_version": "59.0b13",
            "version": "58.0.2",
            "ios_beta_version": "9.1",
            "ios_version": "9.0",
            "builds": [
                    {
                        "locale": {
                            "code": "ar",
                            "english": "Arabic",
                            "native": "\u0639\u0631\u0628\u064a"
                        }
                    },
                    {
                        "locale": {
                            "code": "be",
                            "english": "Belarusian",
                            "native": "\u0411\u0435\u043b\u0430\u0440\u0443\u0441\u043a\u0430\u044f"
                        }
                    },
                    …
                ],
            "beta_builds": [
                {
                    "locale": {
                        "code": "cs",
                        "english": "Czech",
                        "native": "\u010ce\u0161tina"
                    },
                    "download": {
                        "android": "market://details?id=org.mozilla.firefox_beta"
                    }
                },
                {
                    "locale": {
                        "code": "de",
                        "english": "German",
                        "native": "Deutsch"
                    },
                    "download": {
                        "android": "market://details?id=org.mozilla.firefox_beta"
                    }
                },
                …
            ],
            "alpha_builds": [
                {
                    "locale": {
                        "code": "en-US",
                        "english": "English (US)",
                        "native": "English (US)"
                    },
                    "download": {
                        "android": "market://details?id=org.mozilla.firefox"
                    }
                }
            ]
            },
        }
    """
    mobile_versions = get_mobile_versions(releases, firefox_nightly_version)
    mobile_details = json.loads(shipit_api.common.config.MOBILE_DETAILS_TEMPLATE)
    mobile_details.update(mobile_versions)
    return mobile_details


def get_mobile_versions(releases: typing.List[shipit_api.common.models.Release], firefox_nightly_version: str) -> MobileVersions:
    """This file contains all the versions we ship for Firefox for Android

    This function will output to the following files:
     - mobile_versions.json

    Example:::

        {
            "nightly_version": "60.0a1",
            "alpha_version": "60.0a1",
            "beta_version": "59.0b13",
            "version": "58.0.2",
            "ios_beta_version": "9.1",
            "ios_version": "9.0",
        }
    """
    return dict(
        ios_beta_version=shipit_api.common.config.IOS_BETA_VERSION,
        ios_version=shipit_api.common.config.IOS_VERSION,
        nightly_version=firefox_nightly_version,
        alpha_version=firefox_nightly_version,
        beta_version=get_latest_version(releases, Product.FIREFOX_ANDROID, filter_closure=lambda r: MobileVersion.parse(r.version).is_beta),
        version=get_latest_version(releases, Product.FIREFOX_ANDROID, filter_closure=lambda r: MobileVersion.parse(r.version).is_release),
    )


def get_thunderbird_versions(releases: typing.List[shipit_api.common.models.Release], thunderbird_nightly_version: str) -> ThunderbirdVersions:
    """

    This function will output to the following files:
     - thunderbird_versions.json

    Example:::

        {
            "LATEST_THUNDERBIRD_VERSION":         "52.6.0",
            "LATEST_THUNDERBIRD_ALPHA_VERSION":   "54.0a2",
            "LATEST_THUNDERBIRD_DEVEL_VERSION":   "59.0b2",
            "LATEST_THUNDERBIRD_NIGHTLY_VERSION": "60.0a1",
            "THUNDERBIRD_ESR": "115.8.0esr",
            "THUNDERBIRD_ESR_NEXT": ""
        }
    """
    return dict(
        LATEST_THUNDERBIRD_VERSION=get_latest_version(releases, Product.THUNDERBIRD, shipit_api.common.config.THUNDERBIRD_RELEASE_BRANCH),
        LATEST_THUNDERBIRD_DEVEL_VERSION=get_latest_version(releases, Product.THUNDERBIRD, shipit_api.common.config.THUNDERBIRD_BETA_BRANCH),
        LATEST_THUNDERBIRD_NIGHTLY_VERSION=thunderbird_nightly_version,
        LATEST_THUNDERBIRD_ALPHA_VERSION=shipit_api.common.config.LATEST_THUNDERBIRD_ALPHA_VERSION,
        THUNDERBIRD_ESR=get_firefox_esr_version(
            releases, f"{shipit_api.common.config.THUNDERBIRD_ESR_BRANCH_PREFIX}{shipit_api.common.config.CURRENT_ESR}", Product.THUNDERBIRD
        ),
        THUNDERBIRD_ESR_NEXT=get_firefox_esr_next_version(
            releases,
            f"{shipit_api.common.config.THUNDERBIRD_ESR_BRANCH_PREFIX}{shipit_api.common.config.ESR_NEXT}",
            Product.THUNDERBIRD,
            shipit_api.common.config.ESR_NEXT,
        ),
    )


def get_thunderbird_beta_builds() -> typing.Dict:
    """This file is empty and not used today.

    This function will output to the following files:
     - thunderbird_beta_builds.json

    Example:::

        {}
    """
    return dict()


def sanity_check_firefox_builds(firefox_versions: FirefoxVersions, firefox_primary_builds: PrimaryBuilds, version_key: str, min_builds: int = 20) -> None:
    version = firefox_versions.get(version_key)
    if not version:
        return

    builds = len([locale for locale, build in firefox_primary_builds.items() if version in build])

    if builds < min_builds:
        raise click.ClickException(f"Too few firefox primary builds for {version_key}")


def sanity_check_thunderbuild_builds(
    thunderbird_versions: ThunderbirdVersions, thunderbird_primary_builds: PrimaryBuilds, version_key: str, min_builds: int = 20
) -> None:
    version = thunderbird_versions.get(version_key)
    if not version:
        return

    builds = len([locale for locale, build in thunderbird_primary_builds.items() if version in build])

    if builds < min_builds:
        raise click.ClickException(f"Too few thunderbird primary builds for {version_key}")


def sanity_checks(product_details: ProductDetails) -> None:
    for version_key in (
        "FIREFOX_NIGHTLY",
        "FIREFOX_DEVEDITION",
        "FIREFOX_ESR",
        "FIREFOX_ESR115",
        "LATEST_FIREFOX_DEVEL_VERSION",
        "LATEST_FIREFOX_RELEASED_DEVEL_VERSION",
        "LATEST_FIREFOX_VERSION",
    ):
        sanity_check_firefox_builds(
            typing.cast(FirefoxVersions, product_details["1.0/firefox_versions.json"]),
            typing.cast(PrimaryBuilds, product_details["1.0/firefox_primary_builds.json"]),
            version_key,
        )

    # so far p-d only lists builds for the latest version
    # bedrock uses the locales for the release channel to
    # build download pages for the other channels
    for version_key in ("LATEST_THUNDERBIRD_VERSION",):
        sanity_check_thunderbuild_builds(
            typing.cast(ThunderbirdVersions, product_details["1.0/thunderbird_versions.json"]),
            typing.cast(PrimaryBuilds, product_details["1.0/thunderbird_primary_builds.json"]),
            version_key,
        )


def run_check(*arg, **kw):
    return cli_common.utils.retry(lambda: cli_common.command.run_check(*arg, **kw))


async def rebuild(
    db_session: sqlalchemy.orm.Session,
    git_branch: str,
    git_repo_url: str,
    folder_in_repo: str,
    breakpoint_version: typing.Optional[int],
    clean_working_copy: bool = True,
):
    secrets = [urllib.parse.urlparse(git_repo_url).password]

    # Sometimes we want to work from a clean working copy
    if clean_working_copy and shipit_api.common.config.PRODUCT_DETAILS_DIR.exists():
        shutil.rmtree(shipit_api.common.config.PRODUCT_DETAILS_DIR)

    # Clone/pull latest product details
    logger.info(f"Getting latest product details from {cli_common.command.hide_secrets(git_repo_url, secrets)}.")
    if shipit_api.common.config.PRODUCT_DETAILS_DIR.exists():
        # Checkout the branch we are working on
        logger.info(f"Checkout {git_branch} branch.")
        run_check(["git", "checkout", git_branch], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
        run_check(["git", "pull"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
        # make sure checkout is clean by removing changes to existing files
        run_check(["git", "reset", "--hard", "HEAD"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
        # make sure checkout is clean by removing files which are new
        run_check(["git", "clean", "-xfd"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
    else:
        run_check(
            ["git", "clone", "-b", git_branch, git_repo_url, shipit_api.common.config.PRODUCT_DETAILS_DIR.name],
            cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR.parent,
            secrets=secrets,
        )
        run_check(["git", "config", "http.postBuffer", "12M"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
        run_check(["git", "config", "user.email", "release-services+robot@mozilla.com"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
        run_check(["git", "config", "user.name", "Release Services Robot"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)

    # XXX: we need to implement how to figure out breakpoint_version from old_product_details
    # if breakpoint_version is not provided we should figure it out from old_product_details
    # and if we can not figure it out we should use shipit_api.common.config.BREAKPOINT_VERSION
    # breakpoint_version should always be higher then shipit_api.common.config.BREAKPOINT_VERSION
    if breakpoint_version is None:
        breakpoint_version = shipit_api.common.config.BREAKPOINT_VERSION
    logger.info(f"Breakpoint version is {breakpoint_version}")

    # get data from older product-details
    logger.info(f"Reading old product details from {shipit_api.common.config.PRODUCT_DETAILS_DIR / folder_in_repo}")
    old_product_details = get_old_product_details(shipit_api.common.config.PRODUCT_DETAILS_DIR / folder_in_repo)

    # get all the releases from the database from (including)
    # breakpoint_version on
    logger.info("Getting old releases from the database")
    releases = get_releases_from_db(db_session, breakpoint_version)

    # get the current nightly version from the database
    logger.info("Getting the current nightly version from the database")
    firefox_nightly_version = get_product_channel_version(db_session, "firefox", "nightly")
    thunderbird_nightly_version = get_product_channel_version(db_session, "thunderbird", "nightly")

    # Also fetch latest nightly builds with their L10N info
    nightly_builds = [
        shipit_api.common.models.Release(
            product=Product.FIREFOX.value,
            version=firefox_nightly_version,
            branch="mozilla-central",
            revision="default",
            build_number=None,
            release_eta=None,
            partial_updates=None,
            status=None,
        ),
        shipit_api.common.models.Release(
            product=Product.THUNDERBIRD.value,
            version=thunderbird_nightly_version,
            branch="comm-central",
            revision="default",
            build_number=None,
            release_eta=None,
            partial_updates=None,
            status=None,
        ),
    ]
    logger.info("Getting locales from hg.mozilla.org for each release from database")
    # use limit_per_host=50 since hg.mozilla.org doesn't like too many connections
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=50), timeout=aiohttp.ClientTimeout(total=30)) as session:
        raise_on_failure = git_branch in ["production", "staging"]
        releases_l10n = await asyncio.gather(*[fetch_l10n_data(session, release, raise_on_failure) for release in releases])
        nightly_l10n = await asyncio.gather(*[fetch_l10n_data(session, release, raise_on_failure) for release in nightly_builds])

    releases_l10n = {release: changeset for (release, changeset) in releases_l10n if changeset is not None}
    nightly_l10n = {release: changeset for (release, changeset) in nightly_l10n if changeset is not None}

    combined_releases = releases + nightly_builds
    combined_l10n = releases_l10n.copy()
    combined_l10n.update(nightly_l10n)

    # combine old and new data
    product_details: ProductDetails = {
        "all.json": get_releases(
            breakpoint_version,
            [Product.DEVEDITION, Product.FIREFOX, Product.FENIX, Product.FENNEC, Product.THUNDERBIRD],
            releases,
            old_product_details,
        ),  # consider adding `android-components` at some point.
        "devedition.json": get_releases(breakpoint_version, [Product.DEVEDITION], releases, old_product_details),
        "firefox.json": get_releases(breakpoint_version, [Product.FIREFOX], releases, old_product_details),
        "firefox_history_development_releases.json": get_release_history(
            breakpoint_version, Product.FIREFOX, ProductCategory.DEVELOPMENT, releases, old_product_details
        ),
        "firefox_history_major_releases.json": get_release_history(breakpoint_version, Product.FIREFOX, ProductCategory.MAJOR, releases, old_product_details),
        "firefox_history_stability_releases.json": get_release_history(
            breakpoint_version, Product.FIREFOX, ProductCategory.STABILITY, releases, old_product_details
        ),
        "firefox_primary_builds.json": await get_primary_builds(
            breakpoint_version, Product.FIREFOX, combined_releases, combined_l10n, old_product_details, firefox_nightly_version, thunderbird_nightly_version
        ),
        "firefox_versions.json": await get_firefox_versions(releases, firefox_nightly_version),
        "languages.json": get_languages(old_product_details),
        "mobile_android.json": get_releases(breakpoint_version, [Product.FENNEC, Product.FENIX, Product.FIREFOX_ANDROID], releases, old_product_details),
        "mobile_details.json": get_mobile_details(releases, firefox_nightly_version),
        "mobile_history_development_releases.json": get_release_history(
            breakpoint_version, Product.FENNEC, ProductCategory.DEVELOPMENT, releases, old_product_details
        ),
        "mobile_history_major_releases.json": get_release_history(breakpoint_version, Product.FENNEC, ProductCategory.MAJOR, releases, old_product_details),
        "mobile_history_stability_releases.json": get_release_history(
            breakpoint_version, Product.FENNEC, ProductCategory.STABILITY, releases, old_product_details
        ),
        "mobile_versions.json": get_mobile_versions(releases, firefox_nightly_version),
        "thunderbird.json": get_releases(breakpoint_version, [Product.THUNDERBIRD], releases, old_product_details),
        "thunderbird_beta_builds.json": get_thunderbird_beta_builds(),
        "thunderbird_history_development_releases.json": get_release_history(
            breakpoint_version, Product.THUNDERBIRD, ProductCategory.DEVELOPMENT, releases, old_product_details
        ),
        "thunderbird_history_major_releases.json": get_release_history(
            breakpoint_version, Product.THUNDERBIRD, ProductCategory.MAJOR, releases, old_product_details
        ),
        "thunderbird_history_stability_releases.json": get_release_history(
            breakpoint_version, Product.THUNDERBIRD, ProductCategory.STABILITY, releases, old_product_details
        ),
        "thunderbird_primary_builds.json": await get_primary_builds(
            breakpoint_version, Product.THUNDERBIRD, combined_releases, combined_l10n, old_product_details, firefox_nightly_version, thunderbird_nightly_version
        ),
        "thunderbird_versions.json": get_thunderbird_versions(releases, thunderbird_nightly_version),
    }

    product_details.update(get_regions(old_product_details))
    product_details.update(get_l10n(releases, releases_l10n, old_product_details))

    #  add '1.0/' infront of each file path
    product_details = {f"1.0/{file_}": content for file_, content in product_details.items()}

    # create index.html for every folder
    product_details = create_index_listing(product_details)

    # run sanity checks
    sanity_checks(product_details)

    if shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR.exists():
        shutil.rmtree(shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR)

    for file__, content in product_details.items():
        new_file = shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR / file__

        # we must ensure that all needed folders exists
        os.makedirs(new_file.parent, exist_ok=True)

        # write content into json file
        with new_file.open("w+") as f:
            if new_file.suffix == ".json":
                f.write(json.dumps(content, sort_keys=(not isinstance(content, collections.OrderedDict)), indent=4))
            else:
                f.write(content)

    # remove all top level items in folder_in_repo
    for item in os.listdir(shipit_api.common.config.PRODUCT_DETAILS_DIR / folder_in_repo):
        item = shipit_api.common.config.PRODUCT_DETAILS_DIR / folder_in_repo / item
        if item.exists():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                os.unlink(item)

    # Move new files to be commited
    for item in os.listdir(shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR):
        shutil.move(shipit_api.common.config.PRODUCT_DETAILS_NEW_DIR / item, shipit_api.common.config.PRODUCT_DETAILS_DIR / folder_in_repo / item)

    # Add, commit and push changes
    run_check(["git", "add", "."], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)

    # check if there is something to commit
    output = run_check(["git", "status", "--short"], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
    if output != b"":
        # XXX: we need a better commmit message, maybe mention what triggered this update
        commit_message = "Updating product details"
        run_check(["git", "commit", "-m", commit_message], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
        run_check(["git", "push", "origin", git_branch], cwd=shipit_api.common.config.PRODUCT_DETAILS_DIR, secrets=secrets)
