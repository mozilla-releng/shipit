FROM python:3

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install -r requirements/base.txt

COPY . /app
RUN python setup.py install

CMD ["/app/docker.d/init.sh"]
