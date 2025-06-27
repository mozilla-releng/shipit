# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# WARNING: Update api/Dockerfile* files when you update this one. Or better,
# find a way to use the same Dockerfile
# %ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION


RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app
USER app

# %ARG UV_VERSION
COPY --from=ghcr.io/astral-sh/uv:$UV_VERSION /uv /uvx /bin/

# %include pyproject.toml
# %include uv.lock
ADD --chown=app:app \
    topsrcdir/pyproject.toml \
    topsrcdir/uv.lock \
    /app/

# %include api/products.yml
# %include api/pyproject.toml
ADD --chown=app:app \
    topsrcdir/api/products.yml \
    topsrcdir/api/pyproject.toml \
    /app/api/

# %include api/docker.d
ADD --chown=app:app \
    topsrcdir/api/docker.d \
    /app/api/docker.d/

# %include api/src
ADD --chown=app:app \
    topsrcdir/api/src \
    /app/api/src/

# Install dependencies
RUN uv sync --locked --project api

ARG APP_TYPE
ARG APP_VERSION
ARG TASK_ID
ARG TASKCLUSTER_ROOT_URL
ARG VCS_HEAD_REPOSITORY
ARG VCS_HEAD_REV

RUN echo "{\"commit\": \"$VCS_HEAD_REV\", \"version\": \"$APP_VERSION\", \"source\": \"$VCS_HEAD_REPOSITORY\", \"build\": \"$TASKCLUSTER_ROOT_URL/tasks/$TASK_ID\"}" > /app/version.json

ENV WEB_CONCURRENCY 3
ENV APP_TYPE ${APP_TYPE}
ENV FLASK_APP shipit_api.$APP_TYPE.flask:app

ENTRYPOINT ["/bin/bash", "-c", "/app/api/docker.d/init.sh admin"]
