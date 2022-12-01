from quart import Blueprint, current_app, jsonify, request, Response
from bento_lib.auth.quart_decorators import quart_permissions_owner
from bento_lib.responses.quart_errors import (
    quart_bad_request_error,
    quart_internal_server_error
)
from bento_drop_box_service import __version__
from bento_drop_box_service.backend import get_backend
from bento_drop_box_service.constants import SERVICE_NAME, SERVICE_TYPE


drop_box_service = Blueprint("drop_box_service", __name__)


@drop_box_service.route("/tree", methods=["GET"])
@quart_permissions_owner
async def drop_box_tree() -> Response:
    if (backend := await get_backend()) is not None:
        return jsonify(await backend.get_directory_tree())

    return quart_internal_server_error("The service source data is not configured properly")


@drop_box_service.route("/objects/<path:path>", methods=["GET", "PUT"])
@quart_permissions_owner
async def drop_box_retrieve(path) -> Response:
    # Werkzeug's default is to encode URL to latin1
    # in case we have unicode characters in the filename
    try:
        path = path.encode('iso-8859-1').decode('utf8')
    except UnicodeDecodeError:
        pass

    backend = await get_backend()

    if backend is None:
        return quart_internal_server_error("The service source data is not configured properly")

    if request.method == "PUT":
        content_length = int(request.headers.get("Content-Length", "0"))
        if content_length == 0:
            return quart_bad_request_error("No file provided or no/zero content length specified")
        return await backend.upload_to_path(request, path, content_length)

    return await backend.retrieve_from_path(path)


@drop_box_service.route("/service-info", methods=["GET"])
async def service_info() -> Response:
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info
    return jsonify({
        "id": current_app.config["SERVICE_ID"],
        "name": SERVICE_NAME,
        "type": SERVICE_TYPE,
        "description": "Drop box service for a Bento platform node.",
        "organization": {
            "name": "C3G",
            "url": "http://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": __version__,
        "env": "dev" if current_app.config["BENTO_DEBUG"] else "prod",
    })
