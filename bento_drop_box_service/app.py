import os

from bento_lib.responses.quart_errors import (
    quart_error_wrap,
    quart_error_wrap_with_traceback,
    quart_bad_request_error,
    quart_not_found_error,
    quart_internal_server_error
)
from quart import Quart
from werkzeug.exceptions import BadRequest, NotFound

from bento_drop_box_service.backend import close_backend
from bento_drop_box_service.constants import SERVICE_NAME, SERVICE_TYPE
from bento_drop_box_service.routes import drop_box_service


SERVICE_DATA = os.environ.get("SERVICE_DATA", "data/")
MINIO_URL = os.environ.get("MINIO_URL", None)

application = Quart(__name__)
application.config.from_mapping(
    BENTO_DEBUG=os.environ.get(
        "CHORD_DEBUG", os.environ.get("BENTO_DEBUG", os.environ.get("QUART_ENV", "production"))
    ).strip().lower() in ("true", "1", "development"),
    SERVICE_ID=os.environ.get("SERVICE_ID", str(":".join(list(SERVICE_TYPE.values())[:2]))),
    SERVICE_DATA_SOURCE="minio" if MINIO_URL else "local",
    SERVICE_DATA=None if MINIO_URL else SERVICE_DATA,
    MINIO_URL=MINIO_URL,
    MINIO_USERNAME=os.environ.get("MINIO_USERNAME") if MINIO_URL else None,
    MINIO_PASSWORD=os.environ.get("MINIO_PASSWORD") if MINIO_URL else None,
    MINIO_BUCKET=os.environ.get("MINIO_BUCKET") if MINIO_URL else None,
    MINIO_RESOURCE=None,  # manual application-wide override for MinIO boto3 resource
    TRAVERSAL_LIMIT=16,
)

application.register_blueprint(drop_box_service)

# Generic catch-all
application.register_error_handler(Exception, quart_error_wrap_with_traceback(quart_internal_server_error,
                                                                              service_name=SERVICE_NAME))
application.register_error_handler(BadRequest, quart_error_wrap(quart_bad_request_error))
application.register_error_handler(NotFound, quart_error_wrap(quart_not_found_error))

application.teardown_appcontext(close_backend)
