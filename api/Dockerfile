FROM python:3.8

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install -r requirements/base.txt

COPY . /app
RUN APP_TYPE="admin" pip install -e .

ENV FLASK_APP shipit_api.admin.flask:app
ENV APP_SETTINGS /app/settings.py
ENV WEB_CONCURRENCY=3
USER app

CMD ["/app/docker.d/init.sh"]
