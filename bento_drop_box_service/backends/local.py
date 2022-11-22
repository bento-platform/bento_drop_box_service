from __future__ import annotations

import aiofiles
import aiofiles.os
import aiofiles.ospath
import os

from bento_lib.responses.quart_errors import quart_bad_request_error, quart_not_found_error
from typing import TypedDict
from quart import current_app, send_file, Request, Response
from werkzeug.utils import secure_filename

from .base import DropBoxBackend


# TODO: py3.11: individual optional fields
class DropBoxEntry(TypedDict, total=False):
    name: str
    path: str
    size: int
    contents: tuple[DropBoxEntry, ...]


class LocalBackend(DropBoxBackend):
    async def _get_directory_tree(self, directory: str, level: int = 0) -> tuple[DropBoxEntry, ...]:
        entries: list[DropBoxEntry] = []
        # for some reason this doesn't work as a comprehension
        # noinspection PyUnresolvedReferences
        for entry in (await aiofiles.os.listdir(directory)):
            if (level < current_app.config["TRAVERSAL_LIMIT"] or not (
                    await aiofiles.ospath.isdir(os.path.join(directory, entry)))) and entry[0] != ".":
                entries.append({
                    "name": entry,
                    "path": os.path.abspath(os.path.join(directory, entry)),
                    **({
                        "contents": await self._get_directory_tree(os.path.join(directory, entry), level=level + 1),
                    } if (await aiofiles.ospath.isdir(os.path.join(directory, entry))) else {
                        "size": await aiofiles.ospath.getsize(os.path.join(directory, entry)),
                    })
                })

        return tuple(entries)

    async def get_directory_tree(self) -> tuple[DropBoxEntry, ...]:
        return await self._get_directory_tree(current_app.config["SERVICE_DATA"])

    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        # TODO: This might not be secure (ok for now due to permissions check)
        upload_path = os.path.realpath(os.path.join(current_app.config["SERVICE_DATA"],
                                                    os.path.dirname(path), secure_filename(os.path.basename(path))))
        if not os.path.realpath(os.path.join(current_app.config["SERVICE_DATA"], path)).startswith(
                os.path.realpath(current_app.config["SERVICE_DATA"])):
            # TODO: Mark against user
            return quart_bad_request_error("Cannot upload outside of the drop box")

        if os.path.exists(upload_path):
            return quart_bad_request_error("Cannot upload to an existing path")

        try:
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        except FileNotFoundError:  # blank dirname
            pass

        with aiofiles.open(upload_path, "wb") as f:
            async for chunk in request.body:
                await f.write(chunk)

        return current_app.response_class(status=204)

    async def retrieve_from_path(self, path: str) -> Response:
        directory_items: tuple[DropBoxEntry, ...] = await self.get_directory_tree()

        # Otherwise, find the file if it exists and return it.
        path_parts = path.split("/")  # TODO: Deal with slashes in file names

        while len(path_parts) > 0:
            part = path_parts[0]
            path_parts = path_parts[1:]

            if part not in {item["name"] for item in directory_items}:
                return quart_not_found_error("Nothing found at specified path")

            try:
                node = next(item for item in directory_items if item["name"] == part)

                if "contents" not in node:
                    if len(path_parts) > 0:
                        return quart_bad_request_error("Cannot retrieve a directory")

                    return await send_file(node["path"], mimetype="application/octet-stream", as_attachment=True,
                                           attachment_filename=node["name"])

                directory_items = node["contents"]

            except StopIteration:
                return quart_not_found_error("Nothing found at specified path")
