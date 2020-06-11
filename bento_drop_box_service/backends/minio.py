import boto3
from typing import Tuple

from botocore.exceptions import ClientError
from bento_lib.responses.flask_errors import flask_internal_server_error, flask_not_found_error
from flask import current_app, send_file
from werkzeug import Request, Response

from .base import DropBoxBackend
from ..minio import S3Tree


class MinioBackend(DropBoxBackend):
    def __init__(self, resource=None):
        super(MinioBackend, self).__init__()

        if resource:
            self.minio = resource
        else:
            self.minio = boto3.resource(
                's3',
                endpoint_url=current_app.config['MINIO_URL'],
                aws_access_key_id=current_app.config['MINIO_USERNAME'],
                aws_secret_access_key=current_app.config['MINIO_PASSWORD']
            )

        self.bucket = self.minio.Bucket(current_app.config['MINIO_BUCKET'])

    def get_directory_tree(self) -> Tuple[dict]:
        tree = S3Tree()

        for obj in self.bucket.objects.all():
            tree.add_path(obj)

        return tree.serialize()

    def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        # TODO: Implement
        return flask_internal_server_error("Uploading to minio not implemented")

    def retrieve_from_path(self, path: str) -> Response:
        try:
            obj = self.bucket.Object(path)
            content = obj.get()
        except ClientError:
            return flask_not_found_error("Nothing found at specified path")

        filename = path.split('/')[-1]

        return send_file(
            content['Body'],
            mimetype="application/octet-stream",
            as_attachment=True,
            attachment_filename=filename
        )
