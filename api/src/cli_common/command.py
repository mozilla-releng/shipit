# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import shlex
import subprocess

import click

logger = logging.getLogger(__name__)


def hide_secrets(text, secrets):
    if type(text) is bytes:
        encode_secret, xxx = lambda x: bytes(x, encoding="utf-8"), b"XXX"
    elif type(text) is str:
        encode_secret, xxx = lambda x: x, "XXX"
    else:
        return text

    for secret in secrets:
        if type(secret) is not str:
            continue
        text = text.replace(encode_secret(secret), xxx)
    return text


def run(command, stream=False, handle_stream_line=None, log_command=True, log_output=True, secrets=[], **kwargs):
    """Run a command through subprocess"""

    if type(command) is str:
        command_as_string = command
        command = shlex.split(command)
    else:
        command_as_string = " ".join(command)

    if len(command) == 0:
        raise click.ClickException("Can't run an empty command.")

    _kwargs = dict(stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # no interactions
    _kwargs.update(kwargs)

    if stream:
        _kwargs["bufsize"] = 1

    if log_command:
        logger.debug("Running command: %s, %s", hide_secrets(command_as_string, secrets), _kwargs)

    with subprocess.Popen(command, **_kwargs) as proc:
        if stream:
            output = []
            for line in proc.stdout:
                line = line.decode("utf-8", "ignore")
                line = line.rstrip("\n")
                if log_output:
                    logger.debug(hide_secrets(line, secrets))
                output.append(line)
                if handle_stream_line:
                    handle_stream_line(line)
            output = "\n".join(output)
            # TODO: When needed we should also add possibility to stream stdout
            #  and sterr separatly using asyncio.subprocess:
            #    https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/
            #  You can still pipe stderr into stdout which is enough for now.
            error = ""
        else:
            output, error = proc.communicate()

    return proc.returncode, output, error


def run_check(command, **kwargs):
    """Run a command through subprocess and check for output"""

    if type(command) is str:
        command_as_string = command
        command = shlex.split(command)
    else:
        command_as_string = " ".join(command)

    returncode, output, error = run(command, **kwargs)

    if returncode != 0:
        secrets = kwargs.get("secrets", [])
        logger.info(
            "Command failed with code: %s, %s, %s, %s",
            returncode,
            hide_secrets(command_as_string, secrets),
            hide_secrets(output, secrets),
            hide_secrets(error, secrets),
        )
        raise click.ClickException(hide_secrets(f"`{command[0]}` failed with code: {returncode}.", secrets))

    return output
