from __future__ import annotations

import aiofiles
import aiofiles.os
import aiofiles.ospath
import os
import pathlib

from bento_lib.responses.quart_errors import quart_bad_request_error, quart_not_found_error
from fastapi import status
from fastapi.requests import Request
from fastapi.responses import FileResponse
from starlette.responses import Response
from typing import TypedDict
from werkzeug.utils import secure_filename

from .base import DropBoxBackend


# TODO: py3.11: individual optional fields
class DropBoxEntry(TypedDict, total=False):
    name: str
    filePath: str
    relativePath: str
    uri: str
    size: int
    lastModified: float
    lastMetadataChange: float
    contents: tuple[DropBoxEntry, ...]


class LocalBackend(DropBoxBackend):
    async def _get_directory_tree(
        self,
        root_path: pathlib.Path,
        sub_path: tuple[str, ...],
        level: int = 0,
    ) -> tuple[DropBoxEntry, ...]:
        root_path = root_path.absolute()
        entries: list[DropBoxEntry] = []
        sub_path_str: str = "/".join(sub_path)
        current_dir = (root_path / sub_path_str).absolute() if sub_path_str else root_path.absolute()
        # noinspection PyUnresolvedReferences
        for entry in (await aiofiles.os.listdir(current_dir)):
            if (level < self.config.traversal_limit or not (
                    await aiofiles.ospath.isdir(current_dir))) and entry[0] != ".":
                if "/" in entry:
                    self.logger.warning(f"Skipped entry with a '/' in its name: {entry}")
                    continue

                entry_path = current_dir / entry
                entry_path_stat = entry_path.stat()

                rel_path = (f"/{sub_path_str}" if sub_path_str else "") + f"/{entry}"

                entries.append({
                    "name": entry,
                    "filePath": str(entry_path),  # Actual path on file system
                    "relativePath": rel_path,  # Path relative to root of drop box (/)
                    **({
                        "contents": await self._get_directory_tree(root_path, (*sub_path, entry), level=level + 1),
                    } if (await aiofiles.ospath.isdir(entry_path)) else {
                        "size": entry_path_stat.st_size,
                        "lastModified": entry_path_stat.st_mtime,
                        "lastMetadataChange": entry_path_stat.st_ctime,
                        "uri": self.config.service_url + f"/objects{rel_path}",
                    })
                })

        return tuple(sorted(entries, key=lambda e: e["name"]))

    async def get_directory_tree(self) -> tuple[DropBoxEntry, ...]:
        root_path: pathlib.Path = pathlib.Path(self.config.service_data)
        return await self._get_directory_tree(root_path, ())

    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        sd = self.config.service_data

        # TODO: This might not be secure (ok for now due to permissions check)
        upload_path = os.path.realpath(os.path.join(sd, os.path.dirname(path), secure_filename(os.path.basename(path))))
        if not os.path.realpath(os.path.join(sd, path)).startswith(os.path.realpath(sd)):
            # TODO: Mark against user
            return quart_bad_request_error("Cannot upload outside of the drop box")

        if os.path.exists(upload_path):
            return quart_bad_request_error("Cannot upload to an existing path")

        try:
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        except FileNotFoundError:  # blank dirname
            pass

        async with aiofiles.open(upload_path, "wb") as f:
            async for chunk in request.stream():
                await f.write(chunk)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def retrieve_from_path(self, path: str) -> Response:
        root_path: pathlib.Path = pathlib.Path(self.config.service_data).absolute()
        directory_items: tuple[DropBoxEntry, ...] = await self.get_directory_tree()

        # Manually crawl through the tree to only return items which are explicitly in the tree.

        # Otherwise, find the file if it exists and return it.
        # TODO: Deal with slashes in file names
        path_parts: list[str] = path.removeprefix(str(root_path)).strip("/").split("/")

        while True:
            part = path_parts[0]
            path_parts = path_parts[1:]

            if part not in {item["name"] for item in directory_items}:
                return quart_not_found_error("Nothing found at specified path")

            try:
                node = next(item for item in directory_items if item["name"] == part)

                if not path_parts:  # End of the path
                    if "contents" in node:
                        return quart_bad_request_error("Cannot retrieve a directory")

                    return FileResponse(node["filePath"], media_type="application/octet-stream", filename=node["name"])

                if "contents" not in node:
                    return quart_bad_request_error(f"{node['name']} is not a directory")

                directory_items = node["contents"]
                # Go around another iteration, nesting into this directory

            except StopIteration:
                return quart_not_found_error("Nothing found at specified path")
