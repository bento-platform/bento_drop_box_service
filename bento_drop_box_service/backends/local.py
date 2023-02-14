from __future__ import annotations

import aiofiles
import aiofiles.os
import aiofiles.ospath
import os
import pathlib

from bento_lib.responses.quart_errors import quart_bad_request_error, quart_not_found_error
from typing import Tuple, TypedDict
from quart import current_app, send_file, Request, Response
from werkzeug.utils import secure_filename

from .base import DropBoxBackend


# TODO: py3.10: remove in favour of [str].removeprefix(...)
def _str_removeprefix_polyfill(s: str, prefix: str) -> str:
    return s[len(prefix):] if s.startswith(prefix) else s


# TODO: py3.11: individual optional fields
class DropBoxEntry(TypedDict, total=False):
    name: str
    filePath: str
    uri: str
    size: int
    last_modified: float
    last_metadata_change: float
    contents: tuple[DropBoxEntry, ...]


class LocalBackend(DropBoxBackend):
    async def _get_directory_tree(
        self,
        root_path: pathlib.Path,
        sub_path: Tuple[str, ...],
        level: int = 0,
    ) -> tuple[DropBoxEntry, ...]:
        root_path = root_path.absolute()
        entries: list[DropBoxEntry] = []
        sub_path_str: str = "/".join(sub_path)
        current_dir = (root_path / sub_path_str).absolute()
        # noinspection PyUnresolvedReferences
        for entry in (await aiofiles.os.listdir(current_dir)):
            if (level < current_app.config["TRAVERSAL_LIMIT"] or not (
                    await aiofiles.ospath.isdir(current_dir))) and entry[0] != ".":
                if "/" in entry:
                    self.logger.warning(f"Skipped entry with a '/' in its name: {entry}")
                    continue

                entry_path = current_dir / entry
                entry_path_stat = entry_path.stat()

                entries.append({
                    "name": entry,
                    "filePath": str(entry_path),
                    **({
                        "contents": await self._get_directory_tree(root_path, (*sub_path, entry), level=level + 1),
                    } if (await aiofiles.ospath.isdir(entry_path)) else {
                        "size": entry_path_stat.st_size,
                        "last_modified": entry_path_stat.st_mtime,
                        "last_metadata_change": entry_path_stat.st_ctime,
                        "uri": (
                            current_app.config["SERVICE_URL"] +
                            "/objects" +
                            _str_removeprefix_polyfill(str(entry_path), str(root_path))
                        ),
                    })
                })

        return tuple(entries)

    async def get_directory_tree(self) -> tuple[DropBoxEntry, ...]:
        root_path: pathlib.Path = pathlib.Path(current_app.config["SERVICE_DATA"])
        return await self._get_directory_tree(root_path, (".",))

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
        root_path: pathlib.Path = pathlib.Path(current_app.config["SERVICE_DATA"]).absolute()
        directory_items: tuple[DropBoxEntry, ...] = await self.get_directory_tree()

        # Manually crawl through the tree to only return items which are explicitly in the tree.

        # Otherwise, find the file if it exists and return it.
        # TODO: Deal with slashes in file names
        path_parts: list[str] = _str_removeprefix_polyfill(path, str(root_path)).lstrip("/").split("/")

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

                    return await send_file(
                        node["filePath"],
                        mimetype="application/octet-stream",
                        as_attachment=True,
                        attachment_filename=node["name"])

                directory_items = node["contents"]

            except StopIteration:
                return quart_not_found_error("Nothing found at specified path")
