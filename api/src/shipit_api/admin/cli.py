# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import functools
import io
import json
import os
import typing
from datetime import datetime

import aiohttp
import backoff
import click
import mohawk
import requests
import sqlalchemy
import sqlalchemy.orm

from backend_common.log import configure_logging
from shipit_api.admin.flask import flask_app
from shipit_api.admin.product_details import rebuild
from shipit_api.common.config import BREAKPOINT_VERSION
from shipit_api.common.models import NightlyRelease, Release, Version


def coroutine(f):
    """A generic function to create a main asyncio loop"""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_time=60)
async def download_json_file(session, url, file_):
    click.echo(f"=> Downloading {url}")
    async with session.get(url) as response:
        response.raise_for_status()

        content = await response.json()

        file_dir = os.path.dirname(file_)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        with io.open(file_, "w+") as f:
            f.write(json.dumps(content, sort_keys=True, indent=4))
        click.echo(f"=> Downloaded to {file_}")

        return (url, file_)


@click.command(name="upload-product-details")
@click.option("--download-dir", required=True, type=click.Path(exists=False, file_okay=False, writable=True, readable=True))
@click.option("--url", default="https://ship-it.mozilla.org")
@coroutine
async def download_product_details(url: str, download_dir: str):
    """Download product details from `url` to `download_dir`."""
    configure_logging()

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/json_exports.json") as response:
            if response.status != 200:
                response.raise_for_status()
            paths = await response.json()

        await asyncio.gather(
            *[
                download_json_file(session, f"{url}{path}", f"{download_dir}{path}")
                for path in paths
                if path.endswith(".json") and not os.path.exists(f"{download_dir}{path}")
            ]
        )

    click.echo("All files were downloaded successfully!")


@click.command(name="rebuild-product-details")
@click.option("--database-url", type=str, required=True, default="postgresql://127.0.0.1:9000/services")
@click.option("--git-repo-url", type=str, required=True, default="https://github.com/mozilla-releng/product-details")
@click.option("--folder-in-repo", type=str, required=True, default="public/")
@click.option(
    "--channel",
    type=click.Choice(["local", "main", "testing", "dev", "production"]),
    required=True,
    default=os.environ.get("DEPLOYMENT_BRANCH", "main"),
)
@click.option("--breakpoint-version", default=BREAKPOINT_VERSION, type=int)
@click.option("--clean-working-copy", is_flag=True)
@coroutine
async def rebuild_product_details(
    database_url: str, git_repo_url: str, folder_in_repo: str, channel: str, breakpoint_version: typing.Optional[int] = None, clean_working_copy: bool = False
):
    configure_logging()
    if channel == "local":
        channel = "main"
    engine = sqlalchemy.create_engine(database_url)
    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    click.echo("Product details are building ...")
    await rebuild(session, channel, git_repo_url, folder_in_repo, breakpoint_version, clean_working_copy)
    click.echo("Product details have been rebuilt")


def get_taskcluster_headers(request_url, method, content, taskcluster_client_id, taskcluster_access_token):
    hawk = mohawk.Sender(
        {"id": taskcluster_client_id, "key": taskcluster_access_token, "algorithm": "sha256"}, request_url, method, content, content_type="application/json"
    )
    return {"Authorization": hawk.request_header, "Content-Type": "application/json"}


@click.command(name="shipit-import")
@click.option("--api-from", default="https://shipit-api.mozilla-releng.net")
@click.option("--limit-releases", default=100, help="Only import N releases. Use -1 to import all releases, 0 to skip importing releases entirely.")
def shipit_import(api_from, limit_releases):
    configure_logging()

    with flask_app.app_context():
        session = flask_app.db.session

        if limit_releases != 0:
            # Import releases
            click.echo("Fetching release list...")
            req = requests.get(f"{api_from}/releases?status=shipped")
            req.raise_for_status()
            releases = req.json()
            # Pull the most recent N releases when limiting; they're more important
            # for testing in most cases.
            releases.sort(key=lambda r: datetime.fromisoformat(r["created"]), reverse=True)
            release_count = len(releases) if limit_releases == -1 else limit_releases

            for release in releases[:release_count]:
                if session.query(Release).filter(Release.name == release["name"]).first():
                    click.echo(f"{release['name']} already exists, skipping...")
                    continue

                click.echo(f"Importing {release['name']}")

                r = Release(
                    product=release["product"],
                    version=release["version"],
                    branch=release["branch"],
                    revision=release["revision"],
                    build_number=release["build_number"],
                    release_eta=release.get("release_eta"),
                    partial_updates=release.get("partials"),
                    status=release["status"],
                )
                r.created = release["created"]
                r.completed = release["completed"] or release["created"]
                session.add(r)
                session.commit()

            # Import nightly releases
            click.echo("Fetching nightly release list...")
            for product, channel in (("firefox", "nightly"), ("thunderbird", "nightly")):
                click.echo(f"Importing {product} {channel} nightly releases")
                before_buildid = None
                imported = 0
                while True:
                    if limit_releases != -1 and imported >= limit_releases:
                        break

                    params = {"product": product, "channel": channel, "limit": 500, "order": "desc"}
                    if before_buildid:
                        params["before_buildid"] = before_buildid
                    req = requests.get(f"{api_from}/nightly-release", params=params)
                    req.raise_for_status()
                    nightlies = req.json()
                    if not nightlies:
                        break

                    for nightly in nightlies:
                        if limit_releases != -1 and imported >= limit_releases:
                            break
                        before_buildid = nightly["buildid"]

                        if (
                            session.query(NightlyRelease)
                            .filter(
                                NightlyRelease.product == nightly["product"],
                                NightlyRelease.channel == nightly["channel"],
                                NightlyRelease.buildid == nightly["buildid"],
                            )
                            .first()
                        ):
                            click.echo(f"{product} {channel} {nightly['buildid']} already exists, skipping...")
                            continue

                        click.echo(f"Importing {product} {channel} {nightly['buildid']}")
                        n = NightlyRelease(
                            product=nightly["product"],
                            channel=nightly["channel"],
                            version=nightly["version"],
                            buildid=nightly["buildid"],
                            locales=nightly["locales"],
                        )
                        session.add(n)
                        session.commit()

                        imported += 1

                    if len(nightlies) < 500:
                        break

        # Import Versions
        # only import the two entries we need to rebuild product details for now
        click.echo("Importing Version information...")
        for product, channel in (("firefox", "nightly"), ("thunderbird", "nightly")):
            click.echo(f"Importing {product} {channel} Version information")
            req = requests.get(f"{api_from}/versions/{product}/{channel}")
            req.raise_for_status()
            version = req.json()

            if v := session.query(Version).filter(Version.product_name == product, Version.product_channel == channel).first():
                v.current_version = version
            else:
                v = Version(product_name=product, product_channel=channel, current_version=version)

            session.add(v)
            session.commit()


@click.command(name="trigger-product-details")
@click.option("--base-url", default="https://shipit-api.mozilla-releng.net")
@click.option("--taskcluster-client-id", help="Taskcluster Client ID", required=True, prompt=True)
@click.option("--taskcluster-access-token", help="Taskcluster Access token", required=True, prompt=True, hide_input=True)
def trigger_product_details(base_url: str, taskcluster_client_id: str, taskcluster_access_token: str):
    configure_logging()
    data = "{}"
    url = f"{base_url}/product-details"
    click.echo(f"Triggering product details rebuild on {url} url ... ", nl=False)
    headers = get_taskcluster_headers(url, "post", data, taskcluster_client_id, taskcluster_access_token)
    # skip ssl verification when working against development instances
    verify = not any(map(lambda x: x in base_url, ["localhost", "127.0.0.1"]))
    r = requests.post(url, headers=headers, verify=verify, data=data)
    r.raise_for_status()
    click.echo(click.style("Product details triggered successfully!", fg="green"))
