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



## Running in Development

Poetry is used to manage dependencies.

### Getting set up

1. Install `poetry`:
   ```bash
   pip install poetry
   ```
2. Install project dependencies inside a Poetry-managed virtual environment:
   ```bash
   poetry install
   ```

### Running the service locally

To run the service in development mode, use the following command:

```bash
poetry run python -m debugpy --listen "0.0.0.0:5678" -m uvicorn \
  "bento_drop_box_service.app:application" \
  --host 0.0.0.0 \
  --port 5000 \
  --reload
```

### Running tests

To run tests and linting, run Tox:

```bash
poetry run tox
```



## Deploying


The `bento_drop_box_service` service can be deployed with an ASGI server like 
Uvicorn, specifying `bento_drop_box_service.app:application` as the 
ASGI application.

It is best to then put an HTTP server software such as NGINX in front of 
Hypercorn. 
