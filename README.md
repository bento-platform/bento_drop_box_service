# chord_drop_box_service

![Build Status](https://api.travis-ci.com/c3g/chord_drop_box_service.svg?branch=master)
[![codecov](https://codecov.io/gh/c3g/chord_drop_box_service/branch/master/graph/badge.svg)](https://codecov.io/gh/c3g/chord_drop_box_service)

This is a small flask application providing files for ingestion (through `chord_web`,
for `chord_wes`). By default the file served are read on the existing filesystem but
these can also be read from a minIO instance (or AWS S3 for that matter).

## Environment Variables

If using the current filesystem to serve file, you can use the `SERVICE_DATA`
environment variable to point to some location (./data by default).

If a `MINIO_URL` variable is set, the application will try and connect to
a minIO instance, to do so you will also need to set `MINIO_USERNAME`,
`MINIO_PASSWORD` and `MINIO_BUCKET`.

## Running in Development

Development dependencies are described in `requirements.txt` and can be
installed using the following command:

```bash
pip install -r requirements.txt
```

To start the application:

```bash
FLASK_APP=chord_drop_box_service.app flask run
```
