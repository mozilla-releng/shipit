Ship It API and Frontend
========================

See ``api`` and ``frontend`` READMEs for more details on each.


Local Development
-----------------
Use ``docker-compose up`` to run them both. The API will be available at https://localhost:8015. The frontend will be available at https://localhost:8010

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
