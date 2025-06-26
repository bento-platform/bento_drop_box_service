import aioboto3
import logging

from fastapi import status
from fastapi.requests import Request
from starlette.responses import Response, StreamingResponse
from werkzeug.utils import secure_filename
from bento_lib.logging import log_level_from_str

from .base import DropBoxEntry, DropBoxBackend
from ..config import Config


class S3Backend(DropBoxBackend):
    def __init__(self, config: Config, logger: logging.Logger):
        super().__init__(config, logger)

        # Sync log levels for boto-related loggers with configured log level:
        logging.getLogger("boto3").setLevel(log_level_from_str(config.log_level))
        logging.getLogger("botocore").setLevel(log_level_from_str(config.log_level))
        logging.getLogger("aiobotocore").setLevel(log_level_from_str(config.log_level))

        protocol = "https" if config.s3_use_https else "http"
        endpoint_url = f"{protocol}://{config.s3_endpoint}"

        self.session = aioboto3.Session()
        self.s3_kwargs = {
            "endpoint_url": endpoint_url,
            "aws_access_key_id": config.s3_access_key,
            "aws_secret_access_key": config.s3_secret_key,
            "region_name": config.s3_region_name,
            "verify": config.s3_validate_ssl,
        }
        self.bucket_name = config.s3_bucket

    async def _create_s3_client(self):
        return self.session.client("s3", **self.s3_kwargs)

    @staticmethod
    def create_directory_tree(files: list[DropBoxEntry]):
        """
        Function to create the directory tree from a list of files
        For each file present in the list :
         - Check if the directories contained in the filePath exist in the tree
           (if not, create a node in the tree for the directory)
         - When all the directories in the filePath are present in the tree, add the file to the right place in the tree
        """

        tree: list[DropBoxEntry] = []

        for file in files:
            directories = file["filePath"].split("/")
            current_level = tree
            for i, directory_name in enumerate(directories[:-1]):
                exist_in_tree: bool = False

                for tree_node in current_level:
                    if tree_node["name"] == directory_name:
                        current_level = tree_node["contents"]
                        exist_in_tree = True
                        break

                if not exist_in_tree:
                    # If the directory is not in the tree, create it
                    directory_path = "/".join(directories[: i + 1])
                    new_tree_node = DropBoxEntry(
                        name=directory_name, filePath=directory_path, relativePath=directory_path, contents=[]
                    )
                    current_level.append(new_tree_node)
                    current_level = new_tree_node["contents"]

            # Add file to the tree, at the right place (current level)
            current_level.append(
                DropBoxEntry(
                    name=file["name"],
                    filePath=file["filePath"],
                    relativePath="/" + file["relativePath"],
                    size=file.get("size"),
                    lastModified=file["lastModified"],
                    lastMetadataChange=file["lastMetadataChange"],
                    uri=file["uri"],
                )
            )

        return tree

    async def get_directory_tree(
        self,
        sub_path: str | None = None,
        ignore: list[str] | None = None,
        include: list[str] | None = None,
    ) -> tuple[DropBoxEntry, ...]:
        self.validate_filters(include, ignore)

        prefix = sub_path if sub_path else ""
        traversal_limit = self.config.traversal_limit

        files_list: list[DropBoxEntry] = []
        async with await self._create_s3_client() as s3_client:
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            async for page in page_iterator:
                if "Contents" not in page:
                    # Page has no objects, nothing to do.
                    # Can occur if no objects are found for the given sub_path.
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    if key.count("/") > traversal_limit:
                        self.logger.warning(f"Object key {key} violates traversal limit {traversal_limit}")
                        continue

                    if self.is_passing_filter(key, include, ignore):
                        last_modified = obj["LastModified"].timestamp()
                        entry: DropBoxEntry = {
                            "name": key.split("/")[-1],
                            "filePath": key,
                            "relativePath": key,
                            "size": obj["Size"],
                            "lastModified": last_modified,
                            "lastMetadataChange": last_modified,
                            "uri": f"{self.config.service_url_base_path}/objects/{key}",
                        }
                        files_list.append(entry)

        return tuple(self.create_directory_tree(files_list))

    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        path = secure_filename(path)
        async with await self._create_s3_client() as s3_client:
            await s3_client.put_object(Bucket=self.bucket_name, Key=path, Body=await request.body())

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def _retrive_headers(self, path: str) -> dict[str, str]:
        async with await self._create_s3_client() as s3:
            head = await s3.head_object(Bucket=self.bucket_name, Key=path)

        return {
            "Content-Disposition": f'attachment; filename="{path.split("/")[-1]}"',
            "Content-Length": str(head["ContentLength"]),
            "Content-Type": head["ContentType"],
            "ETag": head["ETag"],
            "Last-Modified": str(head["LastModified"]),
        }

    async def retrieve_from_path(self, path: str) -> Response:
        chunk_size = self.config.s3_chunk_size
        headers = await self._retrive_headers(path)

        async def stream_object():
            async with await self._create_s3_client() as s3:
                obj = await s3.get_object(Bucket=self.bucket_name, Key=path)
                self.logger.debug(f"Streaming {path}")
                stream = obj["Body"]
                while chunk := await stream.read(chunk_size):
                    yield chunk

        return StreamingResponse(content=stream_object(), headers=headers)

    async def delete_at_path(self, path: str) -> Response:
        async with await self._create_s3_client() as s3_client:
            await s3_client.delete_object(Bucket=self.bucket_name, Key=path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
