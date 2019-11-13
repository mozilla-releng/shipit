#/bin/sh
set -e

test $GIT_HEAD_REV
test $TASK_ID

cat > version.json <<EOF
{
    "commit": "${GIT_HEAD_REV}",
    "version": "$(cat ./version.txt)",
    "source": "${REPO_URL}",
    "build": "${TASKCLUSTER_ROOT_URL}/tasks/${TASK_ID}"
}
EOF

cat ./version.json
