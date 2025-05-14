# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# WARNING: Update api/Dockerfile* files when you update this one. Or better,
# find a way to use the same Dockerfile
ARG PYTHON_VERSION
ARG UV_VERSION

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv
FROM python:$PYTHON_VERSION AS builder

COPY --from=uv /uv /bin

WORKDIR /app

# %include pyproject.toml
# %include uv.lock
ADD topsrcdir/pyproject.toml \
    topsrcdir/uv.lock \
    /app/

# %include api/products.yml
# %include api/trust-domains.yml
# %include api/pyproject.toml
ADD topsrcdir/api/products.yml \
    topsrcdir/api/trust-domains.yml \
    topsrcdir/api/pyproject.toml \
    /app/api/

# %include api/src
ADD topsrcdir/api/src \
    /app/api/src/

# Install dependencies
RUN uv sync --locked

FROM python:$PYTHON_VERSION

# %include api/docker.d
ADD topsrcdir/api/docker.d \
    /app/docker.d/

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app
USER app

ARG APP_TYPE
ARG APP_VERSION
ARG TASK_ID
ARG TASKCLUSTER_ROOT_URL
ARG VCS_HEAD_REPOSITORY
ARG VCS_HEAD_REV

COPY --from=builder --chown=app:app /app /app
RUN echo "{\"commit\": \"$VCS_HEAD_REV\", \"version\": \"$APP_VERSION\", \"source\": \"$VCS_HEAD_REPOSITORY\", \"build\": \"$TASKCLUSTER_ROOT_URL/tasks/$TASK_ID\"}" > /app/version.json

ENV WEB_CONCURRENCY 3
ENV APP_TYPE ${APP_TYPE}
ENV FLASK_APP shipit_api.$APP_TYPE.flask:app

ENTRYPOINT ["/bin/bash", "-c", "/app/docker.d/init.sh ${APP_TYPE}"]
