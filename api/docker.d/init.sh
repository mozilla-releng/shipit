#!/bin/bash

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

cert="${MY_DIR}/cert.pem"
key="${MY_DIR}/key.pem"

EXTRA_ARGS=""
if [ "$APP_CHANNEL" == "development" ]
then
    test $HOST
    test $PORT
    # Local development only - we don't want these in deployed environments
    EXTRA_ARGS="--bind $HOST:$PORT --workers 3 --timeout 3600 --reload --reload-engine=poll --certfile=$cert --keyfile=$key"
fi

exec /usr/local/bin/gunicorn shipit_api.flask:app --log-file - $EXTRA_ARGS
