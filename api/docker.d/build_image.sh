#/bin/sh
set -e

test $DOCKER_REPO
test $DOCKER_TAG
test $DOCKERFILE

docker build -f $DOCKERFILE -t $DOCKER_REPO:$DOCKER_TAG .
