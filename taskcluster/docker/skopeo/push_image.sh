#!/bin/sh
set -e

test $DOCKER_REPO
test $DEPLOYMENT_BRANCH
test $DEPLOY_SECRET_URL
test $MOZ_FETCHES_DIR

echo "=== Generating dockercfg ==="
mkdir -m 700 $HOME/.docker
curl $DEPLOY_SECRET_URL | jq '.secret.docker.skopeo' > $HOME/.docker/config.json
chmod 600 $HOME/.docker/config.json

echo "=== Pushing to docker hub ==="
DOCKER_ARCHIVE_TAG="${DEPLOYMENT_BRANCH}-$(date +%Y%m%d%H%M%S)"
unzstd $MOZ_FETCHES_DIR/image.tar.zst
skopeo copy docker-archive:$MOZ_FETCHES_DIR/image.tar docker://$DOCKER_REPO:$DEPLOYMENT_BRANCH
# Print the digest to make the cloudops tooling work
skopeo inspect docker://$DOCKER_REPO:$DEPLOYMENT_BRANCH
skopeo copy docker-archive:$MOZ_FETCHES_DIR/image.tar docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG
skopeo inspect docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG

echo "=== Clean up ==="
rm -rf $HOME/.docker
