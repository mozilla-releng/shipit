
Ship It API and Frontend
========================

See `api` and `frontend` READMEs for more details on each.


Local Development
-----------------
Use `docker-compose up` to run them both. The API will be available at https://localhost:8015. The frontend will be available at https://localhost:8010

Deployed Environments
---------------------

We have a number of deployed Ship It environments. All of the backends respond to pushes to different Docker tags in https://hub.docker.com/r/mozilla/release-services. Each frontend has its own S3 bucket that is deployed to as part of CI on a particular branch. Below are further details about each:


Production
----------
* Backend URL: https://shipit-api.mozilla-releng.net
* Backend Dockerhub Tag: `shipit_api_dockerflow_production`
* Backend Deploys: In response to pushes to the `production` branch
* Frontend URL: https://shipit.mozilla-releng.net/
* Frontend Deploys: In response to pushes to the `production` branch
* Frontend S3 bucket: `relengstatic-prod-shipitfrontend-static-website`
* Product Details URL: https://product-details.mozilla.org

Staging
-------
* Backend URL: https://api.shipit.staging.mozilla-releng.net
* Backend Dockerhub Tag: `shipit_api_dockerflow_staging`
* Backend Deploys: In response to pushes to the `staging` branch
* Frontend URL: https://shipit.staging.mozilla-releng.net/
* Frontend S3 bucket: `relengstatic-staging-shipitfrontend-static-website`
* Frontend Deploys: In response to pushes to the `staging` branch
* Product Details URL: https://product-details.staging.mozilla-releng.net

Two important notes about staging:
1) The backend URL is actually a CNAME for dev.shipitapi.nonprod.cloudops.mozgcp.net, but we call this environment "staging".
2) There is _also_ a CloudOps staging environment at stage.shipitapi.nonprod.cloudops.mozgcp.net, which we do not use (more on that in the "CloudOps staging" section below).

Testing
-------
* Backend URL: https://testing.shipitapi.nonprod.cloudops.mozgcp.net
* Backend Dockerhub Tag: `shipit_api_dockerflow_testing`
* Backend Deploys: In response to pushes to the `testing` branch
* Frontend URL: https://shipit.testing.mozilla-releng.net/
* Frontend S3 bucket: `relengstatic-testing-shipitfrontend-static-website`
* Frontend Deploys: In response to pushes to the `testing` branch
* Product Details URL: https://product-details.testing.mozilla-releng.net

CloudOps Staging
----------------
* Backend URL: https://stage.shipitapi.nonprod.cloudops.mozgcp.net
* Backend Dockerhub Tag: `shipit_api_dockerflow_production`
* Backend Deploys: In response to pushes to the `production` branch

This environment solely exists as part of the CloudOps deployment pipeline for the production backend. When the `shipit_api_dockerflow_production` tag is updated on Dockerhub, their pipeline first deploys to this staging environment. If that deployment is successful, it deploys to production. If that deployment fails, the deploy is aborted.
