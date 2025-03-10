import aioboto3
import logging

import aioboto3.resources
from fastapi import status
from fastapi.requests import Request
from starlette.responses import Response, StreamingResponse
from werkzeug.utils import secure_filename

from .base import DropBoxEntry, DropBoxBackend
from ..config import Config


class S3Backend(DropBoxBackend):
    def __init__(self, config: Config, logger: logging.Logger):
        super().__init__(config, logger)

        protocol = "https" if config.s3_use_https else "http"
        endpoint_url = f"{protocol}://{config.s3_endpoint}"

        self.session = aioboto3.Session()
        self.s3_kwargs = {
            "endpoint_url": endpoint_url,
            "aws_access_key_id": config.s3_access_key,
            "aws_secret_access_key": config.s3_secret_key,
            "region_name": config.s3_region_name,
            "verify": config.s3_validate_ssl
        }
        self.bucket_name = config.s3_bucket
        self.s3_client = self.session.client("s3", **self.s3_kwargs)

    async def _create_s3_client(self):
        return self.session.client(
            's3',
            **self.s3_kwargs
        )

    # Function to create the directory tree from a list of files
    # For each file present in the list :
    # - Check if the directories contained in the filePath exist in the tree
    #   (if not, create a node in the tree for the directory)
    # - When all the directories in the filePath are present in the tree, add the file to the right place in the tree
    def create_directory_tree(self, files: list[DropBoxEntry]):
        tree: list[DropBoxEntry] = []
        for file in files:
            directories = file["filePath"].split('/')
            current_level = tree
            for i, directory_name in enumerate(directories[:-1]):
                exist_in_tree = False
                for tree_node in current_level:
                    if tree_node["name"] == directory_name:
                        current_level = tree_node["contents"]
                        exist_in_tree = True
                        break
                if not exist_in_tree:
                    # If the directory is not in the tree, create it
                    directory_path = '/'.join(directories[:i + 1])
                    new_tree_node = DropBoxEntry(
                        name=directory_name,
                        filePath=directory_path,
                        relativePath=directory_path,
                        contents=[]
                    )
                    current_level.append(new_tree_node)
                    current_level = new_tree_node["contents"]
            # Add file to the tree, at the right place (current level)
            new_file = DropBoxEntry(
                name=file["name"],
                filePath=file["filePath"],
                relativePath='/' + file["relativePath"],
                size=file.get("size"),
                lastModified=file["lastModified"],
                lastMetadataChange=file["lastMetadataChange"],
                uri=file["uri"]
            )
            current_level.append(new_file)
        return tree

    async def get_directory_tree(self) -> tuple[DropBoxEntry, ...]:
        async with await self._create_s3_client() as s3_client:
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.bucket_name)

            files_list: list[DropBoxEntry] = []
            async for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.count('/') < self.config.traversal_limit:
                            entry = {
                                "name": key.split('/')[-1],
                                "filePath": key,
                                "relativePath": key,
                                "size": obj['Size'],
                                "lastModified": obj['LastModified'].timestamp(),
                                "lastMetadataChange": obj['LastModified'].timestamp(),
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
        file_name = path.split("/")[-1]
        async with await self._create_s3_client() as s3:
            head = await s3.head_object(Bucket=self.bucket_name, Key=path)
            content_length = head["ContentLength"]
            etag = head["ETag"]
            content_type = head["ContentType"]
            last_modified = head["LastModified"]
        return {
            "CONTENT-DISPOSITION": file_name,
            "Content-Length": str(content_length),
            "Content-Type": content_type,
            "ETag": etag,
            "Last-Modified": str(last_modified)
        }

    async def retrieve_from_path(self, path: str) -> Response:
        chunk_size = 8 * 1000 * 1000    # 8MB
        headers = await self._retrive_headers(path)

        async def stream_object():
            async with await self._create_s3_client() as s3:
                obj = await s3.get_object(Bucket=self.bucket_name, Key=path)
                self.logger.debug(f"Streaming {path}")
                stream = obj["Body"]
                while chunk := await stream.read(chunk_size):
                    yield chunk

        return StreamingResponse(
            content=stream_object(),
            headers=headers,
        )

    async def delete_at_path(self, path: str) -> Response:
        async with await self._create_s3_client() as s3_client:
            await s3_client.delete_object(Bucket=self.bucket_name, Key=path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
