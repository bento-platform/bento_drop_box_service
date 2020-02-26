from flask import Blueprint, current_app, jsonify, request
from chord_lib.auth.flask_decorators import flask_permissions_owner
from chord_lib.responses.flask_errors import *
from chord_drop_box_service import __version__
from chord_drop_box_service.backend import get_backend
from chord_drop_box_service.constants import *


drop_box_service = Blueprint("drop_box_service", __name__)


@drop_box_service.route("/tree", methods=["GET"])
@flask_permissions_owner
def drop_box_tree():
    backend = get_backend()

    if backend is None:
        return flask_internal_server_error("The service source data is not configured properly")

    return jsonify(backend.get_directory_tree())


@drop_box_service.route("/objects/<path:path>", methods=["GET", "PUT"])
@flask_permissions_owner
def drop_box_retrieve(path):
    # Werkzeug's default is to encode URL to latin1
    # in case we have unicode characters in the filename
    try:
        path = path.encode('iso-8859-1').decode('utf8')
    except UnicodeDecodeError:
        pass

    backend = get_backend()

    if backend is None:
        return flask_internal_server_error("The service source data is not configured properly")

    if request.method == "PUT":
        content_length = int(request.headers.get("Content-Length", "0"))
        if content_length == 0:
            return flask_bad_request_error("No file provided or no/zero content length specified")
        return backend.upload_to_path(request, path, content_length)

    return backend.retrieve_from_path(path)


@drop_box_service.route("/service-info", methods=["GET"])
def service_info():
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info
    return jsonify({
        "id": current_app.config["SERVICE_ID"],
        "name": SERVICE_NAME,
        "type": SERVICE_TYPE,
        "description": "Drop box service for a CHORD application.",
        "organization": {
            "name": "C3G",
            "url": "http://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": __version__
    })
