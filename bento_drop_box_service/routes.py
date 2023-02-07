import asyncio
from quart import Blueprint, current_app, jsonify, request, Response
from bento_lib.auth.quart_decorators import quart_permissions_owner
from bento_lib.responses.quart_errors import (
    quart_bad_request_error,
    quart_internal_server_error
)
from bento_lib.types import GA4GHServiceInfo, BentoExtraServiceInfo
from bento_drop_box_service import __version__
from bento_drop_box_service.backend import get_backend
from bento_drop_box_service.constants import BENTO_SERVICE_KIND, SERVICE_NAME, SERVICE_TYPE


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


async def _git_stdout(*args) -> str:
    git_proc = await asyncio.create_subprocess_exec(
        "git", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    res, _ = await git_proc.communicate()
    return res.decode().rstrip()


@drop_box_service.route("/service-info", methods=["GET"])
async def service_info() -> Response:
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info

    bento_info: BentoExtraServiceInfo = {
        "serviceKind": BENTO_SERVICE_KIND
    }

    debug_mode = current_app.config["BENTO_DEBUG"]
    if debug_mode:
        try:
            if res_tag := await _git_stdout("describe", "--tags", "--abbrev=0"):
                # noinspection PyTypeChecker
                bento_info["gitTag"] = res_tag
            if res_branch := await _git_stdout("branch", "--show-current"):
                # noinspection PyTypeChecker
                bento_info["gitBranch"] = res_branch
            if res_commit := await _git_stdout("rev-parse", "HEAD"):
                # noinspection PyTypeChecker
                bento_info["gitCommit"] = res_commit

        except Exception as e:
            current_app.logger.error(f"Error retrieving git information: {type(e).__name__}")

    # Do a little type checking
    info: GA4GHServiceInfo = {
        "id": current_app.config["SERVICE_ID"],
        "name": SERVICE_NAME,
        "type": SERVICE_TYPE,
        "description": "Drop box service for a Bento platform node.",
        "organization": {
            "name": "C3G",
            "url": "https://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:info@c3g.ca",
        "version": __version__,
        "environment": "dev" if current_app.config["BENTO_DEBUG"] else "prod",
        "bento": bento_info,
    }

    return jsonify(info)
