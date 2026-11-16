FROM debian:13@sha256:9c6e381421d0f48d1b8133e573f33c185ee16cbf505eda9c4a8a4791b25ea8a6

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
