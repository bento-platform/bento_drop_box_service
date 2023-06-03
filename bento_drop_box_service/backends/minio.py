import boto3
import logging

from botocore.exceptions import ClientError
from fastapi import status
from fastapi.exceptions import HTTPException
from typing import Tuple
from werkzeug import Request, Response

from .base import DropBoxBackend
from ..config import Config
from ..minio import S3Tree


class MinioBackend(DropBoxBackend):
    def __init__(self, config: Config, logger: logging.Logger, resource=None):
        super().__init__(config, logger)

        if resource:
            self.minio = resource
        elif config.minio_resource:
            self.minio = config.minio_resource
        else:
            self.minio = boto3.resource(
                "s3",
                endpoint_url=config.minio_url,
                aws_access_key_id=config.minio_username,
                aws_secret_access_key=config.minio_password,
            )

        self.bucket = self.minio.Bucket(config.minio_bucket)

    async def get_directory_tree(self) -> Tuple[dict, ...]:
        tree = S3Tree()

        for obj in self.bucket.objects.all():
            tree.add_path(obj)

        return tree.serialize()

    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        # TODO: Implement
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Uploading to minio not implemented")

    async def retrieve_from_path(self, path: str):
        try:
            obj = self.bucket.Object(path)
            content = obj.get()
        except ClientError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nothing found at specified path")

        filename = path.split('/')[-1]

        async def return_file():
            for chunk in content["Body"].iter_chunks():
                yield chunk

        return return_file(), 200, {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        }
