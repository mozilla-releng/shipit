# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import json
import logging

import click
import flask
from decouple import Config

import cli_common.pulse
import shipit_api.common.config
from backend_common.taskcluster import get_secrets
from shipit_api.admin.product_details import rebuild

logger = logging.getLogger(__name__)


def rebuild_product_details(default_git_repo_url, default_folder_in_repo, default_channel, default_breakpoint_version, default_clean_working_copy):
    """Rebuild product details.
    """
    logger.debug("Rebuilding product details")
    root_url = flask.current_app.config["TASKCLUSTER_ROOT_URL"]
    client_id = flask.current_app.config["TASKCLUSTER_CLIENT_ID"]
    access_token = flask.current_app.config["TASKCLUSTER_ACCESS_TOKEN"]
    secret = flask.current_app.config["TASKCLUSTER_SECRET"]
    logger.debug(f"Fetching secrets from {secret}")
    secrets = Config(repository=get_secrets(secret, shipit_api.common.config.PROJECT_NAME, root_url, client_id, access_token))

    git_repo_url = secrets("PRODUCT_DETAILS_GIT_REPO_URL", default=default_git_repo_url)
    default_channel = default_channel or secrets("APP_CHANNEL", default="master")
    default_breakpoint_version = secrets("BREAKPOINT_VERSION", default=default_breakpoint_version)

    async def rebuild_product_details_async(channel, body, envelope, properties):
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
        logger.info("Marked pulse message as acknowledged.")

        body = json.loads(body.decode("utf-8"))

        logger.debug("Get rebuild parameters from request payload: %s", body)
        breakpoint_version = body.get("breakpoint_version", default_breakpoint_version)
        clean_working_copy = body.get("clean_working_copy", default_clean_working_copy)
        channel_ = body.get("channel", default_channel)
        folder_in_repo = body.get("folder_in_repo", default_folder_in_repo)

        if None in (channel_, git_repo_url, folder_in_repo):
            raise click.ClickException("One of the rebuild product details parameters is not set correctly.")

        await rebuild(flask.current_app.db.session, channel_, git_repo_url, folder_in_repo, breakpoint_version, clean_working_copy)
        logger.info("Product details rebuilt")

    return rebuild_product_details_async


@click.command()
@click.option("--git-repo-url", type=str, required=False, default=None)
@click.option("--folder-in-repo", type=str, required=True, default="public/")
@click.option("--channel", type=click.Choice(["master", "testing", "staging", "production"]), default=None)
@click.option("--breakpoint-version", default=shipit_api.common.config.BREAKPOINT_VERSION, type=int)
@click.option("--clean-working-copy", is_flag=True, default=True)
@flask.cli.with_appcontext
def cmd(git_repo_url, folder_in_repo, channel, breakpoint_version, clean_working_copy):
    pulse_user = flask.current_app.config["PULSE_USER"]
    pulse_pass = flask.current_app.config["PULSE_PASSWORD"]
    exchange = f"exchange/{pulse_user}/{shipit_api.common.config.PROJECT_NAME}"
    rebuild_product_details_consumer = cli_common.pulse.create_consumer(
        pulse_user,
        pulse_pass,
        exchange,
        shipit_api.common.config.PULSE_ROUTE_REBUILD_PRODUCT_DETAILS,
        rebuild_product_details(git_repo_url, folder_in_repo, channel, breakpoint_version, clean_working_copy),
    )
    logger.info("Listening for new messages on %s %s", exchange, shipit_api.common.config.PULSE_ROUTE_REBUILD_PRODUCT_DETAILS)
    cli_common.pulse.run_consumer(asyncio.gather(*[rebuild_product_details_consumer]))
