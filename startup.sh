export TASKCLUSTER_ROOT_URL='https://firefox-ci-tc.services.mozilla.com/' && eval $(taskcluster signin)
echo -n "Please enter you github token: "
read _token
export GITHUB_TOKEN='$_token'
docker-compose up