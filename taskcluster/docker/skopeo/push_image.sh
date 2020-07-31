#!/bin/sh
set -e

test $APP_VERSION
test $DEPLOYMENT_BRANCH
test $DEPLOY_SECRET_URL
test $DOCKER_REPO
test $MOZ_FETCHES_DIR
test $TASKCLUSTER_ROOT_URL
test $TASK_ID
test $VCS_HEAD_REPOSITORY
test $VCS_HEAD_REV

echo "=== Generating dockercfg ==="
mkdir -m 700 $HOME/.docker
curl $DEPLOY_SECRET_URL | jq '.secret.docker.skopeo' > $HOME/.docker/config.json
chmod 600 $HOME/.docker/config.json

cd $MOZ_FETCHES_DIR
unzstd image.tar.zst

echo "=== Inserting version.json into image ==="
# Create an OCI copy of image in order umoci can patch it
skopeo copy docker-archive:image.tar oci:shipit:final

cat > version.json <<EOF
{
    "commit": "${VCS_HEAD_REV}",
    "version": "${APP_VERSION}",
    "source": "${VCS_HEAD_REPOSITORY}",
    "build": "${TASKCLUSTER_ROOT_URL}/tasks/${TASK_ID}"
}
EOF

umoci insert --image shipit:final version.json /app/version.json

echo "=== Pushing to docker hub ==="
DOCKER_ARCHIVE_TAG="${DEPLOYMENT_BRANCH}-$(date +%Y%m%d%H%M%S)"
skopeo copy oci:shipit:final docker://$DOCKER_REPO:$DEPLOYMENT_BRANCH
# Print the digest to make the cloudops tooling work
skopeo inspect docker://$DOCKER_REPO:$DEPLOYMENT_BRANCH
skopeo copy oci:shipit:final docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG
skopeo inspect docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG

echo "=== Clean up ==="
rm -rf $HOME/.docker
