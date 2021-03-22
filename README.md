# Bento Drop Box Service

![Test Status](https://github.com/bento-platform/bento_drop_box_service/workflows/Test/badge.svg)
![Lint Status](https://github.com/bento-platform/bento_drop_box_service/workflows/Lint/badge.svg)
[![codecov](https://codecov.io/gh/bento-platform/bento_drop_box_service/branch/master/graph/badge.svg)](https://codecov.io/gh/bento-platform/bento_drop_box_service)

This is a small flask application providing files for ingestion (through `bento_web`,
for `bento_wes`). By default, the file served are read on the existing filesystem, but
these can also be read from a minIO instance (or AWS S3 for that matter).



## Environment Variables

If using the current filesystem to serve file, you can use the `SERVICE_DATA`
environment variable to point to some location (./data by default).

If the `MINIO_URL` variable is set, the application will try to connect to
a minIO instance. To do so, you will also need to set `MINIO_USERNAME`,
`MINIO_PASSWORD` and `MINIO_BUCKET`.



## Running in Development

Development dependencies are described in `requirements.txt` and can be
installed using the following command:

```bash
pip install -r requirements.txt
```

To start the application:

```bash
FLASK_APP=bento_drop_box_service.app flask run
```



## Deploying


The `bento_drop_box_service` service can be deployed with a WSGI server like 
Gunicorn or UWSGI, specifying `bento_drop_box_service.app:application` as the 
WSGI application.

It is best to then put an HTTP server software such as NGINX in front of 
Gunicorn. 

**Flask applications should NEVER be deployed in production via the Flask 
development server, i.e. `flask run`!**
