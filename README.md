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
* Backend Dockerhub Tag: shipit_api_dockerflow_production
* Backend Deploys: In response to pushes to the `production` branch
* Frontend URL: https://shipit.mozilla-releng.net/
* Frontend Deploys: In response to pushes to the `production` branch
* Frontend S3 bucket: relengstatic-prod-shipitfrontend-static-website
* Product Details URL: https://product-details.mozilla.org

Staging
-------
* Backend URL: https://stage.shipitapi.nonprod.cloudops.mozgcp.net
* Backend Dockerhub Tag: shipit_api_dockerflow_production
* Backend Deploys: In response to pushes to the `production` branch
* Frontend URL: https://shipit.staging.mozilla-releng.net/
* Frontend S3 bucket: relengstatic-staging-shipitfrontend-static-website
* Frontend Deploys: In response to pushes to the `staging` branch
* Product Details URL: https://product-details.staging.mozilla-releng.net

Testing
-------
* Backend URL: https://testing.shipitapi.nonprod.cloudops.mozgcp.net
* Backend Dockerhub Tag: shipit_api_dockerflow_testing
* Backend Deploys: In response to pushes to the `testing` branch
* Frontend URL: https://shipit.testing.mozilla-releng.net/
* Frontend S3 bucket: relengstatic-testing-shipitfrontend-static-website
* Frontend Deploys: In response to pushes to the `testing` branch
* Product Details URL: https://product-details.testing.mozilla-releng.net

Dev
---
* Backend URL: https://dev.shipitapi.nonprod.cloudops.mozgcp.net
* Backend Dockerhub Tag: shipit_api_dockerflow_dev
* Backend Deploys: In response to pushes to the `dev` branch

Dev does not have a frontend nor product details equivalent.
