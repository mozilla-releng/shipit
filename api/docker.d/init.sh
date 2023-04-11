#!/bin/bash

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

if [ $1 == "public" ]; then
    export FLASK_APP="shipit_api.public.flask:app"
elif [ $1 == "admin" ]; then
    export FLASK_APP="shipit_api.admin.flask:app"
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
    # More than 1 worker causes race conditions when migrating the database.
    # They resolve themselves after a restart...but it's preferable not to have them at all.
    EXTRA_ARGS="--bind $HOST:$PORT --workers 1 --timeout 3600 --reload --reload-engine=poll --certfile=$cert --keyfile=$key"
fi

exec poetry run gunicorn $FLASK_APP --log-file - $EXTRA_ARGS
