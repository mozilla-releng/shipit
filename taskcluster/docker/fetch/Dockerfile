FROM debian:13@sha256:2c91e484d93f0830a7e05a2b9d92a7b102be7cab562198b984a84fdbc7806d91

### Add worker user and setup its workspace.
RUN mkdir /builds && \
    groupadd -g 1000 worker && \
    useradd -u 1000 -g 1000 -d /builds/worker -s /bin/bash -m worker && \
    mkdir -p /builds/worker/workspace && \
    chown -R worker:worker /builds

# Declare default working folder
WORKDIR /builds/worker

# %include-run-task

RUN apt-get update && \
    apt-get install -y \
      gnupg \
      bzip2 \
      git \
      openssh-client \
      python3-requests \
      python3-zstd \
      unzip
