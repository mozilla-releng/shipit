#!/bin/sh
set -e

test $DOCKER_REPO
test $DOCKER_TAG
test $DEPLOY_SECRET_URL
test $IMAGE_URL


echo "=== Generating dockercfg ==="
mkdir -m 700 /root/.docker
wget -O- $DEPLOY_SECRET_URL | jq '.secret.docker.skopeo' > /root/.docker/config.json
chmod 600 /root/.docker/config.json

echo "==== Getting image ==="
wget -O /workspace/image.tar.zst $IMAGE_URL
unzstd /workspace/image.tar.zst


echo "=== Pushing to docker hub ==="
DOCKER_ARCHIVE_TAG="${DOCKER_TAG}-$(date +%Y%m%d%H%M%S)"
skopeo --authfile /root/.docker/config.json --insecure-policy copy docker-archive:/workspace/image.tar docker://$DOCKER_REPO:$DOCKER_TAG
skopeo inspect docker://$DOCKER_REPO:$DOCKER_TAG
skopeo --authfile /root/.docker/config.json --insecure-policy copy docker-archive:/workspace/image.tar docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG
skopeo inspect docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG

echo "=== Clean up ==="
rm -rf /root/.docker
