# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM golang:1.14

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq \
    && apt-get install -y zstd jq \
    && apt-get clean

RUN GO111MODULE=on CGO_ENABLED=0 go get -tags 'exclude_graphdriver_devicemapper exclude_graphdriver_btrfs containers_image_openpgp' github.com/containers/skopeo/cmd/skopeo@v1.1.0

COPY push_image.sh /usr/local/bin/
RUN chmod a+x /usr/local/bin/push_image.sh
CMD ["push_image.sh"]

VOLUME /workspace
