import boto3
import logging
from typing import Tuple

from botocore.exceptions import ClientError
from bento_lib.responses.quart_errors import quart_internal_server_error, quart_not_found_error
from quart import current_app
from werkzeug import Request, Response

from .base import DropBoxBackend
from ..minio import S3Tree


class MinioBackend(DropBoxBackend):
    def __init__(self, logger: logging.Logger, resource=None):
        super(MinioBackend, self).__init__(logger)

        if resource:
            self.minio = resource
        elif current_app.config["MINIO_RESOURCE"]:
            self.minio = current_app.config["MINIO_RESOURCE"]
        else:
            self.minio = boto3.resource(
                "s3",
                endpoint_url=current_app.config["MINIO_URL"],
                aws_access_key_id=current_app.config["MINIO_USERNAME"],
                aws_secret_access_key=current_app.config["MINIO_PASSWORD"]
            )

        self.bucket = self.minio.Bucket(current_app.config["MINIO_BUCKET"])

    async def get_directory_tree(self) -> Tuple[dict]:
        tree = S3Tree()

        for obj in self.bucket.objects.all():
            tree.add_path(obj)

        return tree.serialize()

    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        # TODO: Implement
        return quart_internal_server_error("Uploading to minio not implemented")

    async def retrieve_from_path(self, path: str):
        try:
            obj = self.bucket.Object(path)
            content = obj.get()
        except ClientError:
            return quart_not_found_error("Nothing found at specified path")

        filename = path.split('/')[-1]

        async def return_file():
            for chunk in content["Body"].iter_chunks():
                yield chunk

        return return_file(), 200, {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        }
