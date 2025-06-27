# WARNING: Update taskcluster/docker/k8s-image/Dockerfile file when you update
# this one. Or better, find a way to use the same Dockerfile
FROM python:3.12

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /uvx /bin/

COPY . /app

ENV WEB_CONCURRENCY=3
USER app

RUN uv sync --group dev

CMD ["/app/docker.d/init.sh", "admin"]
