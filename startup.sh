#!/bin/bash
export TASKCLUSTER_ROOT_URL="${TASKCLUSTER_ROOT_URL:-https://firefox-ci-tc.services.mozilla.com}"

scopes=('hooks:trigger-hook:project-app-services/in-tree-action-1-generic/*' \
        'hooks:trigger-hook:project-app-services/in-tree-action-1-release-promotion/*' \
        'hooks:trigger-hook:project-comm/in-tree-action-1-generic/*' \
        'hooks:trigger-hook:project-comm/in-tree-action-1-release-promotion/*' \
        'hooks:trigger-hook:project-gecko/in-tree-action-1-generic/*' \
        'hooks:trigger-hook:project-gecko/in-tree-action-1-release-promotion/*' \
        'hooks:trigger-hook:project-mobile/in-tree-action-1-generic/*' \
        'hooks:trigger-hook:project-mobile/in-tree-action-1-release-promotion/*' \
        'hooks:trigger-hook:project-mozillavpn/in-tree-action-1-generic/*' \
        'hooks:trigger-hook:project-mozillavpn/in-tree-action-1-release-promotion/*' \
        'hooks:trigger-hook:project-xpi/in-tree-action-1-release-promotion/*')

for project in "app-services" "gecko" "mobile" "mozillavpn" "xpi"; do
    # These scopes can be commented out if you don't have them on the target taskcluster instance.
    scopes+=("queue:cancel-task:${project}-level-1/*" "queue:seal-task-group:${project}-level-1/*")
done

function signin {
    scope_str=$(IFS=$'\n' ; echo "${scopes[*]}")
    eval "$(taskcluster signin --scope="$scope_str")"
}

if [[ -z "${TASKCLUSTER_CLIENT_ID}" ]]; then
    signin
else
    active_scopes=$(taskcluster api auth currentScopes)
    for scope in "${scopes[@]}"
    do
        if [[ $active_scopes != *"$scope"* ]]; then
            signin
            break
        fi
    done
fi

if [[ -z "${GITHUB_TOKEN}" ]]; then
    echo -n "Please enter your github token: "
    read -r _token
    export GITHUB_TOKEN="$_token"
fi
docker compose up
