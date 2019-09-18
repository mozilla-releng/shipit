#!/bin/bash

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

cert="${MY_DIR}/cert.pem"
key="${MY_DIR}/key.pem"

exec /usr/local/bin/gunicorn shipit_api.flask:app --bind $HOST:$PORT --workers 2 --timeout 3600 --reload --reload-engine=poll --certfile=$cert --keyfile=$key --log-file -
