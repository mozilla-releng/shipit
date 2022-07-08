#!/usr/bin/env bash
# We run this in shipit/api/. to pin all requirements.
#
# Usage: maintenance/pin.sh [<extra-pip-compile-multi-arguments>]
#
set -e
set -x

docker run -t -v $PWD:/src -w /src python:3.8 maintenance/pin-helper.sh $@
