import aiofiles
import aiofiles.os
import aiofiles.ospath
import os
import pathlib

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse
from starlette.responses import Response
from werkzeug.utils import secure_filename

from .base import DropBoxEntry, DropBoxBackend


class LocalBackend(DropBoxBackend):
    async def _get_directory_tree(
        self,
        root_path: pathlib.Path,
        sub_path: tuple[str, ...],
        level: int = 0,
        ignore: list[str] | None = None,
        include: list[str] | None = None
    ) -> tuple[DropBoxEntry, ...]:
        traversal_limit = self.config.traversal_limit

        root_path = root_path.absolute()
        entries: list[DropBoxEntry] = []
        sub_path_str: str = "/".join(sub_path)
        current_dir = (root_path / sub_path_str).absolute() if sub_path_str else root_path.absolute()
        # noinspection PyUnresolvedReferences
        for entry in await aiofiles.os.listdir(current_dir):
            if (level < traversal_limit or not (await aiofiles.ospath.isdir(current_dir))) and entry[0] != ".":
                if "/" in entry:
                    self.logger.warning(f"Skipped entry with a '/' in its name: {entry}")
                    continue
                
                print(entry.endswith(".json"))

                entry_path = current_dir / entry
                entry_path_stat = entry_path.stat()

                rel_path = (f"/{sub_path_str}" if sub_path_str else "") + f"/{entry}"

                entries.append(
                    {
                        "name": entry,
                        "filePath": str(entry_path),  # Actual path on file system
                        "relativePath": rel_path,  # Path relative to root of drop box (/)
                        **(
                            {
                                "contents": await self._get_directory_tree(
                                    root_path, (*sub_path, entry), level=level + 1
                                ),
                            }
                            if (await aiofiles.ospath.isdir(entry_path))
                            else {
                                "size": entry_path_stat.st_size,
                                "lastModified": entry_path_stat.st_mtime,
                                "lastMetadataChange": entry_path_stat.st_ctime,
                                "uri": self.config.service_url_base_path + f"/objects{rel_path}",
                            }
                        ),
                    }
                )

        return tuple(sorted(entries, key=lambda e: e["name"]))

    async def get_directory_tree(
            self, 
            sub_path: str | None = None,
            ignore: list[str] | None = None,
            include: list[str] | None = None
        , ) -> tuple[DropBoxEntry, ...]:
        root_path: pathlib.Path = pathlib.Path(self.config.service_data)
        if sub_path:
            root_path = root_path.joinpath(sub_path)

        if not str(root_path.absolute()).startswith(self.config.service_data):
            # Only accept requests that are under the data volume
            self.logger.warning(f"attempted to get directory tree outside of drop box data volume: {root_path}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot inspect provided sub tree")
        return await self._get_directory_tree(root_path, (), include=include, ignore=ignore)

    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        sd = self.config.service_data

        # TODO: This might not be secure (ok for now due to permissions check)
        upload_path = os.path.realpath(os.path.join(sd, os.path.dirname(path), secure_filename(os.path.basename(path))))
        if not (rp := os.path.realpath(os.path.join(sd, path))).startswith(os.path.realpath(sd)):
            # TODO: Mark against user
            self.logger.warning(f"attempted upload to path outside of drop box: {rp}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot upload outside of the drop box")

        if os.path.exists(upload_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot upload to an existing path")

        try:
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        except FileNotFoundError:  # blank dirname
            pass

        async with aiofiles.open(upload_path, "wb") as f:
            async for chunk in request.stream():
                await f.write(chunk)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def get_node_at_path(self, path: str, verb: str = "retrieve") -> DropBoxEntry:
        root_path: pathlib.Path = pathlib.Path(self.config.service_data).absolute()
        directory_items: tuple[DropBoxEntry, ...] = await self.get_directory_tree()

        # Manually crawl through the tree to only return items which are explicitly in the tree.

        # TODO: Deal with slashes in file names
        path_parts: list[str] = path.removeprefix(str(root_path)).strip("/").split("/")

        while True:
            part = path_parts[0]
            path_parts = path_parts[1:]

            if part not in {item["name"] for item in directory_items}:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nothing found at specified path")

            try:
                node = next(item for item in directory_items if item["name"] == part)

                if not path_parts:  # End of the path
                    if "contents" in node:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot {verb} a directory"
                        )

                    return node

                if "contents" not in node:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=f"{node['name']} is not a directory"
                    )

                directory_items = node["contents"]
                # Go around another iteration, nesting into this directory

            except StopIteration:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nothing found at specified path")

    async def retrieve_from_path(self, path: str) -> Response:
        node = await self.get_node_at_path(path)
        return FileResponse(node["filePath"], media_type="application/octet-stream", filename=node["name"])

    async def delete_at_path(self, path: str) -> Response:
        node = await self.get_node_at_path(path, verb="delete")
        await aiofiles.os.remove(node["filePath"])
        return Response(status_code=status.HTTP_204_NO_CONTENT)
