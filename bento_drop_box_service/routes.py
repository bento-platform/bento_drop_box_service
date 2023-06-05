import asyncio

from fastapi import APIRouter, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import Response

from bento_lib.types import GA4GHServiceInfo, BentoExtraServiceInfo

from . import __version__
from .authz import authz_middleware
from .backends.dependency import BackendDependency
from .constants import BENTO_SERVICE_KIND, SERVICE_NAME, SERVICE_TYPE
from .config import ConfigDependency
from .logger import LoggerDependency


drop_box_router = APIRouter()

authz_view_dependency = authz_middleware.dep_require_permissions_on_resource(frozenset({"view:drop-box"}))
authz_edit_dependency = authz_middleware.dep_require_permissions_on_resource(frozenset({"edit:drop-box"}))


@drop_box_router.get("/tree", dependencies=(authz_view_dependency,))
async def drop_box_tree(backend: BackendDependency) -> Response:
    return JSONResponse(await backend.get_directory_tree())


@drop_box_router.get("/objects/{path:path}", dependencies=(authz_view_dependency,))
async def drop_box_retrieve(path: str, backend: BackendDependency):
    # Werkzeug's default is to encode URL to latin1
    # in case we have unicode characters in the filename
    try:
        path = path.encode('iso-8859-1').decode('utf8')
    except UnicodeDecodeError:
        pass

    return await backend.retrieve_from_path(path)


@drop_box_router.put("/objects/{path:path}", dependencies=(authz_edit_dependency,))
async def drop_box_upload(request: Request, path: str, backend: BackendDependency):
    # Werkzeug's default is to encode URL to latin1
    # in case we have unicode characters in the filename
    try:
        path = path.encode('iso-8859-1').decode('utf8')
    except UnicodeDecodeError:
        pass

    content_length = int(request.headers.get("Content-Length", "0"))
    if content_length == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided or no/zero content length specified")
    return await backend.upload_to_path(request, path, content_length)


async def _git_stdout(*args) -> str:
    git_proc = await asyncio.create_subprocess_exec(
        "git", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    res, _ = await git_proc.communicate()
    return res.decode().rstrip()


@drop_box_router.get("/service-info", dependencies=[authz_middleware.dep_public_endpoint()])
async def service_info(config: ConfigDependency, logger: LoggerDependency) -> Response:
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info

    bento_info: BentoExtraServiceInfo = {
        "serviceKind": BENTO_SERVICE_KIND
    }

    debug_mode = config.bento_debug
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
            logger.error(f"Error retrieving git information: {type(e).__name__}")

    # Do a little type checking
    info: GA4GHServiceInfo = {
        "id": config.service_id,
        "name": SERVICE_NAME,
        "type": SERVICE_TYPE,
        "description": "Drop box service for a Bento platform node.",
        "organization": {
            "name": "C3G",
            "url": "https://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:info@c3g.ca",
        "version": __version__,
        "environment": "dev" if debug_mode else "prod",
        "bento": bento_info,
    }

    return JSONResponse(info)
