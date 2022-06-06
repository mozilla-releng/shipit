#!/bin/bash
# This runs in docker to pin our requirements files.
set -e
SUFFIX=${SUFFIX:-txt}
if [ $# -gt 0 ]; then
    EXTRA_PCM_ARGS="$@"
fi

pip install --upgrade pip
pip install pip-compile-multi

ARGS="-g base -g public -g test -g local -g tox"
pip-compile-multi -o "$SUFFIX" $ARGS $EXTRA_PCM_ARGS
chmod 644 requirements/*.txt
