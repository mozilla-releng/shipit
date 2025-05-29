# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# WARNING: Update api/Dockerfile* files when you update this one. Or better,
# find a way to use the same Dockerfile
FROM python:3.12

ARG APP_TYPE

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/

# %include api/pyproject.toml
# %include pyproject.toml
# %include uv.lock
ADD topsrcdir/api/pyproject.toml api/pyproject.toml
ADD topsrcdir/pyproject.toml pyproject.toml
ADD topsrcdir/uv.lock uv.lock

# Install dependencies
RUN uv sync --no-install-project --locked

# %include api
ADD topsrcdir/api/ src
ADD topsrcdir/api/docker.d/init.sh docker.d/

# Install the project
RUN uv sync --no-default-groups --locked

ARG TASK_ID
ARG APP_VERSION
ARG VCS_HEAD_REV
ARG VCS_HEAD_REPOSITORY
ARG TASKCLUSTER_ROOT_URL

RUN echo "{\"commit\": \"$VCS_HEAD_REV\", \"version\": \"$APP_VERSION\", \"source\": \"$VCS_HEAD_REPOSITORY\", \"build\": \"$TASKCLUSTER_ROOT_URL/tasks/$TASK_ID\"}" > /app/version.json

ENV WEB_CONCURRENCY 3
ENV APP_TYPE ${APP_TYPE}
ENV FLASK_APP shipit_api.$APP_TYPE.flask:app
USER app
WORKDIR /app/src

ENTRYPOINT ["/bin/bash", "-c", "/app/docker.d/init.sh $APP_TYPE"]
