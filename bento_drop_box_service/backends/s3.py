import aioboto3
import aiofiles
import logging
from ..config import Config

from .base import DropBoxEntry, DropBoxBackend

from fastapi import status
from fastapi.requests import Request
from starlette.responses import Response
from werkzeug.utils import secure_filename


class S3Backend(DropBoxBackend):
    def __init__(self, config: Config, logger: logging.Logger):
        super().__init__(config, logger)

        protocol = "https" if config.use_https else "http"
        endpoint_url = f"{protocol}://{config.service_s3_endpoint}"

        self.session = aioboto3.Session()
        self.endpoint_url = endpoint_url
        self.aws_access_key_id = config.service_s3_access_key
        self.aws_secret_access_key = config.service_s3_secret_key
        self.verify = config.check_ssl_certificate
        self.bucket_name = config.service_s3_bucket

    async def _create_s3_client(self):
        return self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            verify=self.verify
        )

    # Function to create the directory tree
    def create_directory_tree(self, files):
        tree: list[DropBoxEntry] = []
        for file in files:
            parts = file["filePath"].split('/')
            current_level = tree
            for i, part in enumerate(parts[:-1]):
                found = False
                for item in current_level:
                    if item["name"] == part:
                        current_level = item["contents"]
                        found = True
                        break
                if not found:
                    directory_path = '/'.join(parts[:i + 1])
                    new_dir = DropBoxEntry(
                        name=part,
                        filePath=directory_path,
                        relativePath=directory_path,
                        contents=[]
                    )
                    current_level.append(new_dir)
                    current_level = new_dir["contents"]
            new_file = DropBoxEntry(
                name=file["name"],
                filePath=file["filePath"],
                relativePath=file["relativePath"],
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
            async with aiofiles.tempfile.NamedTemporaryFile('wb') as temp_file:
                async for chunk in request.stream():
                    await temp_file.write(chunk)
                await temp_file.seek(0)
                async with aiofiles.open(temp_file.name, 'rb') as file:
                    await s3_client.put_object(Bucket=self.bucket_name, Key=path, Body=await file.read())

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def retrieve_from_path(self, path: str) -> Response:
        async with await self._create_s3_client() as s3_client:
            response = await s3_client.get_object(Bucket=self.bucket_name, Key=path)
            file_content = await response['Body'].read()
        return Response(content=file_content, media_type='application/octet-stream')

    async def delete_at_path(self, path: str) -> Response:
        async with await self._create_s3_client() as s3_client:
            await s3_client.delete_object(Bucket=self.bucket_name, Key=path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
