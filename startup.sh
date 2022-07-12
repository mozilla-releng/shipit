#!/bin/bash

set -e

scopes=('-s' 'hooks:trigger-hook:project-comm/in-tree-action-1-generic/*' \
        '-s' 'hooks:trigger-hook:project-comm/in-tree-action-1-release-promotion/*' \
        '-s' 'hooks:trigger-hook:project-gecko/in-tree-action-1-generic/*' \
        '-s' 'hooks:trigger-hook:project-gecko/in-tree-action-1-release-promotion/*' \
        '-s' 'hooks:trigger-hook:project-mobile/in-tree-action-1-generic/*' \
        '-s' 'hooks:trigger-hook:project-mobile/in-tree-action-1-release-promotion/*' \
        '-s' 'hooks:trigger-hook:project-xpi/in-tree-action-1-release-promotion/*')
export TASKCLUSTER_ROOT_URL='https://firefox-ci-tc.services.mozilla.com/' && eval $(taskcluster signin ${scopes[@]})
echo -n "Please enter your github token: "
read _token
export GITHUB_TOKEN="$_token"
docker-compose up
