#!/bin/bash

exec /usr/local/bin/gunicorn shipit_api.flask:app --bind $HOST:$PORT --workers 2 --timeout 3600 --reload --reload-engine=poll --log-file -
