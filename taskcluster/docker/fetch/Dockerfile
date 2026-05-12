FROM debian:trixie-20260505@sha256:e2d08da6f42ef4b09b165d55528a12727aeed8240dc9edf888e3ec07e10ef9da

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
