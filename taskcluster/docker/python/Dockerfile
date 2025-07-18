# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# %ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION

# Add worker user
RUN mkdir -p /builds && \
    groupadd -g 1000 -o worker && \
    useradd -d /builds/worker -s /bin/bash -m worker -g 1000 -o -u 1000 && \
    mkdir -p /builds/worker/artifacts && \
    chown worker:worker /builds/worker /builds/worker/artifacts

# %include-run-task

# %ARG UV_VERSION
COPY --from=ghcr.io/astral-sh/uv:$UV_VERSION /uv /uvx /bin/

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.task-cache/uv
WORKDIR /builds/worker

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
