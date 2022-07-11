# WARNING: Update taskcluster/docker/k8s-image/Dockerfile file when you update
# this one. Or better, find a way to use the same Dockerfile
FROM python:3.9

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install -r requirements/base.txt

COPY . /app
RUN APP_TYPE="admin" pip install -e .

ENV FLASK_APP shipit_api.admin.flask:app
ENV WEB_CONCURRENCY=3
USER app

CMD ["/app/docker.d/init.sh"]
