# WARNING: Update taskcluster/docker/k8s-image/Dockerfile file when you update
# this one. Or better, find a way to use the same Dockerfile
FROM python:3.9

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app

COPY requirements/poetry.txt /tmp/poetry.txt
RUN pip install -r /tmp/poetry.txt

COPY . /app

ENV WEB_CONCURRENCY=3
USER app

RUN poetry install --only main
RUN poetry install --only dev

CMD ["/app/docker.d/init.sh", "admin"]
