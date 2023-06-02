# Bento Drop Box Service

![Test Status](https://github.com/bento-platform/bento_drop_box_service/workflows/Test/badge.svg)
![Lint Status](https://github.com/bento-platform/bento_drop_box_service/workflows/Lint/badge.svg)
[![codecov](https://codecov.io/gh/bento-platform/bento_drop_box_service/branch/master/graph/badge.svg)](https://codecov.io/gh/bento-platform/bento_drop_box_service)

This is a small Quart application providing files for ingestion (through `bento_web`,
for `bento_wes`). By default, the file served are read on the existing filesystem, but
these can also be read from a minIO instance (or AWS S3 for that matter).

**Requires:** Python 3.10+ and Poetry 1.5+



## Environment Variables

Set `SERVICE_URL` to the base URL of the service (e.g. `https://bentov2.local/api/drop-box`).
This is used for file URI generation.

If using the current filesystem to serve file, you can use the `SERVICE_DATA`
environment variable to point to some location (./data by default).

If the `MINIO_URL` variable is set, the application will try to connect to
a minIO instance. To do so, you will also need to set `MINIO_USERNAME`,
`MINIO_PASSWORD` and `MINIO_BUCKET`.



## Running in Development

Poetry is used to manage dependencies.

### Getting set up

1. Create a virtual environment for the project:
   ```bash
   virtualenv -p python3 ./env
   source env/bin/activate
   ```
2. Install `poetry`:
   ```bash
   pip install poetry
   ```
3. Install project dependencies:
   ```bash
   poetry install
   ```

### Running the service locally

To run the service in development mode, use the following command:

```bash
QUART_ENV=development QUART_APP=bento_service_registry.app quart run
```

### Running tests

To run tests and linting, run Tox:

```bash
tox
```


## Deploying


The `bento_drop_box_service` service can be deployed with an ASGI server like 
Hypercorn, specifying `bento_drop_box_service.app:application` as the 
ASGI application.

It is best to then put an HTTP server software such as NGINX in front of 
Hypercorn. 

**Quart applications should NEVER be deployed in production via the Quart 
development server, i.e. `quart run`!**
