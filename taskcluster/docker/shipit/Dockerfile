# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# WARNING: Update api/Dockerfile* files when you update this one. Or better,
# find a way to use the same Dockerfile
FROM          python:$PYTHON_VERSION

ARG APP_TYPE

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app


# %include api
COPY topsrcdir/api/requirements/poetry.txt /tmp/poetry.txt
RUN pip install -r /tmp/poetry.txt

ENV POETRY_CACHE_DIR=/builds/worker/poetry_cache

COPY topsrcdir/api/pyproject.toml /app/src/pyproject.toml
# --no-ansi is needed due to https://github.com/python-poetry/poetry/issues/7148
RUN cd /app/src && poetry install --only main --no-root --no-ansi

ADD topsrcdir/api/ /app/src
ADD topsrcdir/api/docker.d/init.sh /app/docker.d/

# --no-ansi is needed due to https://github.com/python-poetry/poetry/issues/7148
RUN cd /app/src && APP_TYPE=$APP_TYPE poetry install --only-root --no-ansi && rm -rf /app/src

ARG TASK_ID
ARG APP_VERSION
ARG VCS_HEAD_REV
ARG VCS_HEAD_REPOSITORY
ARG TASKCLUSTER_ROOT_URL

RUN echo "{\"commit\": \"$VCS_HEAD_REV\", \"version\": \"$APP_VERSION\", \"source\": \"$VCS_HEAD_REPOSITORY\", \"build\": \"$TASKCLUSTER_ROOT_URL/tasks/$TASK_ID\"}" > /app/version.json

ENV WEB_CONCURRENCY=3
USER app
WORKDIR /app

CMD ["/app/docker.d/init.sh", $APP_TYPE]
