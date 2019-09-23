#/bin/sh
set -e

test $GIT_HEAD_REV
test $TASK_ID

cat > version.json <<EOF
{
    "commit": "${GIT_HEAD_REV}",
    "version": "$(cat ./version.txt)",
    "source": "https://github.com/mozilla-releng/shipit",
    "build": "https://tools.taskcluster.net/tasks/${TASK_ID}"
}
EOF

cat ./version.json
