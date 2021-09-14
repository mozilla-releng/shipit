Ship It API and Frontend
========================


Local Development
-----------------

First setup
~~~~~~~~~~~

1. Run ``docker-compose up``. Initializing the database can take some time, the first time. You may have to ``Ctrl+C`` and ``docker-compose up`` a second time to get in a stable state.

2. Go to https://localhost:8015 (the API endpoint), https://localhost:8010 (the frontend one), and https://localhost:8016 (the public API one) and accept the TLS security warning (untrusted certificate). If you don't do so on all 3 ports, you may end up with the API that drops request to the API because of `CORS <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`__.

3. Stop the docker containers.

4. Install ``taskcluster`` mozilla's task execution framework. Get the latest `Taskcluster shell client here <https://github.com/taskcluster/taskcluster/tree/main/clients/client-shell#readme>`__

5.  Go to https://github.com/settings/tokens and generate a new token that has no scope at all. It will show as ``public access``. This token is just used to fetch commit and branch info. **COPY AND STORE THE TOKEN FOR LATER USE**

To run each time
~~~~~~~~~~~~~~~~

Run ``./startup.sh``


- `You would need to pass your github token to the script for each startup`
- `After running the startup script, if you stop the script you can simply run` ``docker-compose up`` `in the same terminal session to restart, this would maintain the environment prepared by the startup script for run and you won't need to provide your github token again unless you close the terminal session.`

You should be all set to kick off some staging releases.

To rebuild product-details
~~~~~~~~~~~~~~~~~~~~~~~~~~

product-details rely on a ``pulse queue <https://github.com/mozilla-releng/shipit/blob/df379442c32baa7931767b058840bbb293135010/api/src/shipit_api/admin/api.py#L229>``_, which makes local test tricky.
This pulse queue is then consumed by ``worker.py <https://github.com/mozilla-releng/shipit/blob/df379442c32baa7931767b058840bbb293135010/api/src/shipit_api/admin/worker.py#L42>``_. Although, there's a
way to by-pass the need for a pulse queue.

1. ``docker-compose run api bash``

2. ``shipit_rebuild_product_details --database-url="postgresql://shipituser:shipitpassword@db/shipitdb" --channel development``

3. This will ask you for some GitHub crendentials. You can provide them if you want to update https://github.com/mozilla-releng/product-details. That said, you can also ``Ctrl+C`` and inspect the content of `/tmp/product-details` in the docker container. Changes are done here before they pushed to the git repo.

⚠️ If you decide to provide GitHub crendentials, remember that GitHub accounts that enabled 2-factor-authentication have to provide a GitHub token
instead of their regular password. Instructions to generate a token are found above. This time tough, grant the ``public_repo`` scope.

Troubleshooting
~~~~~~~~~~~~~~~

**"Are you connected to the VPN?"**

You may see the error message ``Error contacting Shipit backend: Error: Network Error. Are you connected to the VPN?``. Be warned this is just a generic message and you don't have to
be connected to the VPN when locally running the instance. This error message can be misleading. Always look at the Firefox developer console, on the "network" tab to check what error
message the API actually returned. If you end up getting a CORS error, then redo the "first setup"

**docker-compose up just doesn't manage to start properly**

The easiest way is to purge docker and the local repository.

1. Stop any shipit docker container displayed by ``docker container ls``
1. Remove any shipit volume displayed by ``docker volume ls``
1. Purge the local repository of any file not tracked by git: ``git clean -fdx``

Deployed Environments
---------------------

We have a number of deployed Ship It environments. All of the backends respond to pushes to different Docker tags in https://hub.docker.com/r/mozilla/release-services. Each frontend has its own S3 bucket that is deployed to as part of CI on a particular branch. Below are further details about each:


Production
----------
Deploys in response to pushes to the ``production`` branch, if the ``CloudOps Stage`` deployment in successful (see below).

- Backend URL: https://shipit-api.mozilla-releng.net
- Backend Dockerhub Tag: ``shipit_api_dockerflow_production``
- Taskcluster Secret: project/releng/shipit/config:production
- Taskcluster Client ID: project/releng/shipit/production
- Frontend URL: https://shipit.mozilla-releng.net/
- Frontend S3 bucket: ``relengstatic-prod-shipitfrontend-static-website``
- Product Details URL: https://product-details.mozilla.org
- Logs: https://console.cloud.google.com/logs/query?project=moz-fx-shipitapi-prod-5cb2 (ask CloudOps for access)

When a production deployment begins, Jenkins first deploys to the canary environment. If that deployment succeeds, the deployment proceeds. If it fails, the deployment is aborted.

Dev
-------
Deploys in response to pushes to the ``dev`` branch.

- Backend URL: https://api.shipit.staging.mozilla-releng.net
- Backend Dockerhub Tag: ``shipit_api_dockerflow_staging``
- Taskcluster Secret: project/releng/shipit/config:staging
- Taskcluster Client ID: project/releng/shipit/production (yes, the same as production)
- Frontend URL: https://shipit.staging.mozilla-releng.net/
- Frontend S3 bucket: ``relengstatic-staging-shipitfrontend-static-website``
- Product Details URL: https://product-details.staging.mozilla-releng.net
- Public API URL: https://public-dev.shipitapi.nonprod.cloudops.mozgcp.net
- Logs: https://console.cloud.google.com/logs/query?project=moz-fx-shipitapi-nonprod-2690 (ask CloudOps for access)


FAQ
---

How to deploy `main` branch to `production`?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    # clone the repo, if not already
    $ git clone https://github.com/mozilla-releng/shipit.git
    # (optional) one can run dry-run to check changes beforehand
    $ git push --dry-run origin main:production
    # in git, the upstream remote defaults to `origin`
    $ git push origin main:production

