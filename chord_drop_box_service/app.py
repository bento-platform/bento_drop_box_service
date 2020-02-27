import os

from chord_lib.responses.flask_errors import (
    flask_error_wrap,
    flask_error_wrap_with_traceback,
    flask_bad_request_error,
    flask_not_found_error,
    flask_internal_server_error
)
from flask import Flask
from werkzeug.exceptions import BadRequest, NotFound

from chord_drop_box_service.backend import close_backend
from chord_drop_box_service.constants import SERVICE_NAME, SERVICE_TYPE
from chord_drop_box_service.routes import drop_box_service


SERVICE_DATA = os.environ.get("SERVICE_DATA", "data/")
MINIO_URL = os.environ.get("MINIO_URL", None)

application = Flask(__name__)
application.config.from_mapping(
    SERVICE_ID=os.environ.get("SERVICE_ID", SERVICE_TYPE),
    SERVICE_DATA_SOURCE='minio' if MINIO_URL else 'local',
    SERVICE_DATA=None if MINIO_URL else SERVICE_DATA,
    MINIO_URL=MINIO_URL,
    MINIO_USERNAME=os.environ.get('MINIO_USERNAME') if MINIO_URL else None,
    MINIO_PASSWORD=os.environ.get('MINIO_PASSWORD') if MINIO_URL else None,
    MINIO_BUCKET=os.environ.get('MINIO_BUCKET') if MINIO_URL else None,
    TRAVERSAL_LIMIT=16,
)

application.register_blueprint(drop_box_service)

# Generic catch-all
application.register_error_handler(Exception, flask_error_wrap_with_traceback(flask_internal_server_error,
                                                                              service_name=SERVICE_NAME))
application.register_error_handler(BadRequest, flask_error_wrap(flask_bad_request_error))
application.register_error_handler(NotFound, flask_error_wrap(flask_not_found_error))

application.teardown_appcontext(close_backend)
