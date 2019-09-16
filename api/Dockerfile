FROM python:3

WORKDIR /app

COPY . /app

RUN pip install -r requirements/base.txt
RUN python setup.py install

CMD ["/app/docker.d/init.sh"]
