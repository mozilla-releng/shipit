# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import json
import logging

import click
import flask

from cli_common.pulse import create_consumer, run_consumer
from shipit_api.admin.product_details import rebuild
from shipit_api.common.config import BREAKPOINT_VERSION, PROJECT_NAME, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS

logger = logging.getLogger(__name__)


def rebuild_product_details(git_repo_url, folder_in_repo, app_channel, breakpoint_version):
    """Rebuild product details.
    """
    logger.debug("Rebuilding product details")

    async def rebuild_product_details_async(channel, body, envelope, properties):
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
        logger.info("Marked pulse message as acknowledged.")
        await rebuild(flask.current_app.db.session, app_channel, git_repo_url, folder_in_repo, breakpoint_version)
        logger.info("Product details rebuilt")

    return rebuild_product_details_async


@click.command()
@flask.cli.with_appcontext
def cmd():
    app_config = flask.current_app.config
    app_channel = app_config["APP_CHANNEL"]
    pulse_user = app_config["PULSE_USER"]
    pulse_pass = app_config["PULSE_PASSWORD"]
    git_repo_url = app_config["PRODUCT_DETAILS_GIT_REPO_URL"]
    folder_in_repo = "public/"
    exchange = f"exchange/{pulse_user}/{PROJECT_NAME}"

    rebuild_product_details_consumer = create_consumer(
        pulse_user,
        pulse_pass,
        exchange,
        PULSE_ROUTE_REBUILD_PRODUCT_DETAILS,
        rebuild_product_details(git_repo_url, folder_in_repo, app_channel, BREAKPOINT_VERSION),
    )
    logger.info("Listening for new messages on %s %s", exchange, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS)
    run_consumer(asyncio.gather(*[rebuild_product_details_consumer]))
