from bento_lib.auth.permissions import P_VIEW_DROP_BOX, P_INGEST_DROP_BOX, P_DELETE_DROP_BOX
from bento_lib.auth.resources import RESOURCE_EVERYTHING
from fastapi import APIRouter, Form, Query, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import Response
from typing import Annotated

from .authz import authz_middleware
from .backends.dependency import BackendDependency


drop_box_router = APIRouter()

VIEW_PERMISSION_SET = frozenset({P_VIEW_DROP_BOX})

authz_view_dependency = authz_middleware.dep_require_permissions_on_resource(VIEW_PERMISSION_SET)
authz_ingest_dependency = authz_middleware.dep_require_permissions_on_resource(frozenset({P_INGEST_DROP_BOX}))
authz_delete_dependency = authz_middleware.dep_require_permissions_on_resource(frozenset({P_DELETE_DROP_BOX}))


@drop_box_router.get("/tree", dependencies=(authz_view_dependency,))
async def drop_box_tree(
    backend: BackendDependency,
    include: Annotated[list[str] | None, Query()] = None,
    ignore: Annotated[list[str] | None, Query()] = None,
) -> Response:
    return JSONResponse(await backend.get_directory_tree(include=include, ignore=ignore))


@drop_box_router.get("/tree/{path:path}", dependencies=(authz_view_dependency,))
async def drop_box_subtree(
    backend: BackendDependency,
    path: str | None,
    include: Annotated[list[str] | None, Query()] = None,
    ignore: Annotated[list[str] | None, Query()] = None,
) -> Response:
    # Same as /tree endpoint, but accepts a subpath in order to return a directory sub-tree.
    # Useful to download files for WES workflows that take a directory input.
    tree = await backend.get_directory_tree(sub_path=path, include=include, ignore=ignore)
    return JSONResponse(tree)


@drop_box_router.get("/objects/{path:path}", dependencies=(authz_view_dependency,))
async def drop_box_retrieve(path: str, backend: BackendDependency):
    return await backend.retrieve_from_path(path)


@drop_box_router.post("/objects/{path:path}")
async def drop_box_retrieve_post(
    request: Request,
    path: str,
    token: Annotated[str, Form()],
    backend: BackendDependency,
):
    # Check the token we received in the POST body against the authorization service
    await authz_middleware.async_check_authz_evaluate(
        request,
        VIEW_PERMISSION_SET,
        RESOURCE_EVERYTHING,
        set_authz_flag=True,
        headers_getter=(lambda _r: {"Authorization": f"Bearer {token}"}),
    )

    return await backend.retrieve_from_path(path)


@drop_box_router.put("/objects/{path:path}", dependencies=(authz_ingest_dependency,))
async def drop_box_upload(request: Request, path: str, backend: BackendDependency):
    content_length = int(request.headers.get("Content-Length", "0"))
    if content_length == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided or no/zero content length specified"
        )
    return await backend.upload_to_path(request, path, content_length)


@drop_box_router.delete(
    "/objects/{path:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(authz_delete_dependency,),
)
async def drop_box_delete(path: str, backend: BackendDependency):
    return await backend.delete_at_path(path)
