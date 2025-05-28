Ship It API and Frontend
========================

Ship It is Mozilla's internal tool for managing the releases of Firefox and other products.

Local Development
-----------------

First time setup
~~~~~~~~~~~~~~~~

1. Install ``taskcluster`` mozilla's task execution framework. Get the latest `Taskcluster shell client here <https://github.com/taskcluster/taskcluster/tree/main/clients/client-shell#readme>`__.
2.  Go to https://github.com/settings/tokens and generate a new token that has no scope at all. It will show as ``public access``. This token is just used to fetch commit and branch info. **COPY AND STORE THE TOKEN FOR LATER USE**
3. Run ``source startup.sh``. Confirm the Taskcluster client that opens in your browser, and provide your Github token when prompted. Initializing the database can take some time, the first time. You may have to ``Ctrl+C`` and ``docker-compose up`` a second time to get in a stable state.
4. Go to https://localhost:8015 (the API endpoint), https://localhost:8010 (the frontend one), and https://localhost:8016 (the public API one) and accept the TLS security warning (untrusted certificate). If you don't do so on all 3 ports, you may end up with the API that drops request to the API because of `CORS <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`__.

Subsequent Runs
~~~~~~~~~~~~~~~

Run: ``source startup.sh``

You should be all set to kick off some staging releases. The script will detect if your Taskcluster client has expired and automatically create a new one.

Running an Interactive Flask Shell for Development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to create an interactive shell environment for the Flask applications, which is useful for development and testing purposes.

Setting up for the Admin API:

1. Define the container in which the Flask application is running

::

    export SHIPIT_API_CONTAINER="shipit-api-1"

2. Access the Docker container's interactive shell

::

    docker exec -it "$SHIPIT_API_CONTAINER" /bin/bash

3. Once inside the container, set the environment variable for the Flask application and start the interactive Flask shell using Poetry

::

    export FLASK_APP="shipit_api.admin.flask:app"
    poetry run flask shell

Setting up for the Public API:

1. Define the container in which the Flask application is running

::

    export SHIPIT_API_CONTAINER="shipit-public-1"

2. Access the Docker container's interactive shell

::

    docker exec -it "$SHIPIT_API_CONTAINER" /bin/bash

3. Once inside the container, set the environment variable for the Flask application and start the interactive Flask shell using Poetry

::

    export FLASK_APP="shipit_api.public.flask:app"
    poetry run flask shell

To provide all required sign offs on staging xpi releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set ``XPI_LAX_SIGN_OFF=true``. This will enable you to run xpi releases in the shipit admin app on your own.
This is useful when testing patches on your local environment and on shipit's dev/staging environment.
When running locally add ``XPI_LAX_SIGN_OFF=true`` to the docker-compose.yml file in ``services.api.environment``.

To rebuild product-details
~~~~~~~~~~~~~~~~~~~~~~~~~~

product-details rely on a `pulse queue <https://github.com/mozilla-releng/shipit/blob/df379442c32baa7931767b058840bbb293135010/api/src/shipit_api/admin/api.py#L229>`__, which makes local test tricky.
This pulse queue is then consumed by `worker.py <https://github.com/mozilla-releng/shipit/blob/df379442c32baa7931767b058840bbb293135010/api/src/shipit_api/admin/worker.py#L42>`__. Although, there's a
way to by-pass the need for a pulse queue.

1. Define the container in which the api application is running

::

    export SHIPIT_API_CONTAINER="shipit-api-1"

2. Access the Docker container's interactive shell

::

    docker exec -it "$SHIPIT_API_CONTAINER" /bin/bash

3. ``poetry run shipit_rebuild_product_details --database-url="postgresql://shipituser:shipitpassword@db/shipitdb" --channel development``

4. This will ask you for some GitHub credentials. You can provide them if you want to update https://github.com/mozilla-releng/product-details. That said, you can also ``Ctrl+C`` and inspect the content of `/tmp/product-details` in the docker container. Changes are done here before they pushed to the git repo.

⚠️ If you decide to provide GitHub credentials, remember that GitHub accounts that enabled 2-factor-authentication have to provide a GitHub token
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
