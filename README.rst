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

There is also a "CloudOps Stage" environment (which is different than the "Staging" environment below) that is deployment as part of the production pipeline. When a production deployment begins, Jenkins first deploys to this environment. If that deployment succeeds, the deployment proceeds. If it fails, the deployment is aborted. The URL for this backend is https://stage.shipitapi.nonprod.cloudops.mozgcp.net.

Staging
-------
Deploys in response to pushes to the ``staging`` branch.

- Backend URL: https://api.shipit.staging.mozilla-releng.net
- Backend Dockerhub Tag: ``shipit_api_dockerflow_staging``
- Taskcluster Secret: project/releng/shipit/config:staging
- Taskcluster Client ID: project/releng/shipit/production (yes, the same as production)
- Frontend URL: https://shipit.staging.mozilla-releng.net/
- Frontend S3 bucket: ``relengstatic-staging-shipitfrontend-static-website``
- Product Details URL: https://product-details.staging.mozilla-releng.net

Two important notes about staging:

1) The backend URL is actually a CNAME for dev.shipitapi.nonprod.cloudops.mozgcp.net. Despite the fact that the real FQDN says "dev", we refer to this environment as "staging".
2) There is *also* a CloudOps environment known as "stage", at stage.shipitapi.nonprod.cloudops.mozgcp.net, which we do not use (more on that in the "CloudOps staging" section below).


Testing
-------
Deploys in response to pushes to the ``testing`` branch.

- Backend URL: https://testing.shipitapi.nonprod.cloudops.mozgcp.net
- Backend Dockerhub Tag: ``shipit_api_dockerflow_testing``
- Taskcluster Secret: project/releng/shipit/config:testing
- Taskcluster Client ID: project/releng/shipit/dev
- Frontend URL: https://shipit.testing.mozilla-releng.net/
- Frontend S3 bucket: ``relengstatic-testing-shipitfrontend-static-website``
- Product Details URL: https://product-details.testing.mozilla-releng.net
