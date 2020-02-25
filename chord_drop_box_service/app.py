import os
import sys
import traceback

import boto3
from flask import Flask
from werkzeug.exceptions import BadRequest, NotFound

from chord_drop_box_service import __version__
from chord_lib.auth.flask_decorators import flask_permissions_owner
from chord_lib.responses.flask_errors import *

SERVICE_TYPE = "ca.c3g.chord:drop-box:{}".format(__version__)
SERVICE_NAME = "CHORD Drop Box Service"

SERVICE_DATA = os.environ.get("SERVICE_DATA", "data/")
MINIO_URL = os.environ.get("MINIO_URL", None)

application = Flask(__name__)
application.config.from_mapping(
    SERVICE_ID=os.environ.get("SERVICE_ID", SERVICE_TYPE),
    SERVICE_NAME=SERVICE_NAME,
    SERVICE_TYPE=SERVICE_TYPE,
    SERVICE_DATA_SOURCE='minio' if MINIO_URL else 'local',
    SERVICE_DATA=None if MINIO_URL else SERVICE_DATA,
    MINIO_URL=MINIO_URL,
    MINIO_USERNAME=os.environ.get('MINIO_USERNAME') if MINIO_URL else None,
    MINIO_PASSWORD=os.environ.get('MINIO_PASSWORD') if MINIO_URL else None,
    MINIO_BUCKET=os.environ.get('MINIO_BUCKET') if MINIO_URL else None,
    TRAVERSAL_LIMIT=16,
)

# Generic catch-all
application.register_error_handler(Exception, flask_error_wrap_with_traceback(flask_internal_server_error,
                                                                              service_name=SERVICE_NAME))
application.register_error_handler(BadRequest, flask_error_wrap(flask_bad_request_error))
application.register_error_handler(NotFound, flask_error_wrap(flask_not_found_error))


# Make data directory/ies if needed
if application.config['SERVICE_DATA_SOURCE'] == 'local':
    os.makedirs(application.config["SERVICE_DATA"], exist_ok=True)

if application.config['SERVICE_DATA_SOURCE'] == 'minio':
    minio = boto3.resource(
        's3',
        endpoint_url=application.config['MINIO_URL'],
        aws_access_key_id=application.config['MINIO_USERNAME'],
        aws_secret_access_key=application.config['MINIO_PASSWORD']
    )
    bucket = minio.Bucket(application.config['MINIO_BUCKET'])
else:
    minio = None
    bucket = None


from chord_drop_box_service import routes
