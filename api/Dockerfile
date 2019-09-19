FROM python:3

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install -r requirements/base.txt

COPY . /app
RUN python setup.py install

ENV APP_NAME shipit_api
ENV APP_SETTINGS /app/settings.py
ENV FLASK_APP shipit_api.flask:app
ENV WEB_CONCURRENCY=3

CMD ["/app/docker.d/init.sh"]
