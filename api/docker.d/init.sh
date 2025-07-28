#!/bin/bash

set -e

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

if [ $1 == "worker" ]; then
    export FLASK_APP="shipit_api.admin.flask:flask_app"
    exec /app/.venv/bin/flask worker
fi

if [ $1 == "public" ]; then
    export ASGI_APP="shipit_api.public.flask:app"
elif [ $1 == "admin" ]; then
    export ASGI_APP="shipit_api.admin.flask:app"
else
    echo "first arg must be 'public' or 'admin'"
    exit 1
fi

EXTRA_ARGS=""
if [ "$APP_CHANNEL" == "development" ]
then
    test $HOST
    test $PORT

    cert="${MY_DIR}/cert.pem"
    key="${MY_DIR}/key.pem"

    # Local development only - we don't want these in deployed environments
    # >1 worker is incompatible with --reload
    EXTRA_ARGS="--host $HOST --port $PORT --workers 1 --reload --ssl-certfile=$cert --ssl-keyfile=$key"
fi

exec /app/.venv/bin/uvicorn $ASGI_APP $EXTRA_ARGS
