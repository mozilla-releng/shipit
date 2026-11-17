# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

ARG PYTHON_VERSION
ARG UV_VERSION

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv
FROM python:$PYTHON_VERSION AS builder

COPY --from=uv /uv /bin

WORKDIR /app

ARG SRC=topsrcdir

# %include pyproject.toml
# %include uv.lock
ADD ${SRC}/pyproject.toml \
    ${SRC}/uv.lock \
    /app/

# %include api/products.yml
# %include api/trust-domains.yml
# %include api/pyproject.toml
ADD ${SRC}/api/products.yml \
    ${SRC}/api/trust-domains.yml \
    ${SRC}/api/pyproject.toml \
    /app/api/

# %include api/src
ADD ${SRC}/api/src \
    /app/api/src/

# Install dependencies
RUN uv sync --locked --no-dev

FROM python:$PYTHON_VERSION

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

# %include api/docker.d
ADD ${SRC}/api/docker.d \
    /app/docker.d/

WORKDIR /app
USER app

ARG APP_TYPE

COPY --from=builder --chown=app:app /app /app
# /app/version.json is inserted by the push-image task (see
# taskcluster/docker/skopeo/push_image.sh)

ENV WEB_CONCURRENCY 3
ENV APP_TYPE ${APP_TYPE}

ENTRYPOINT ["/bin/bash", "-c", "/app/docker.d/init.sh ${APP_TYPE}"]
