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
ADD topsrcdir/api/requirements/ /app/requirements/

RUN pip install -r /app/requirements/public.txt
RUN test "$APP_TYPE" = "admin" && pip install -r /app/requirements/base.txt || :

ADD topsrcdir/api/ /app/src
ADD topsrcdir/api/docker.d/init.sh /app/docker.d/

RUN APP_TYPE=$APP_TYPE pip install /app/src && rm -rf /app/src

ENV FLASK_APP shipit_api.$APP_TYPE.flask:app
ENV WEB_CONCURRENCY=3
USER app
WORKDIR /app

CMD ["/app/docker.d/init.sh"]
