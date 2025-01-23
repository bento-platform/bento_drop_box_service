import boto3
import logging
from ..config import Config

from .base import DropBoxEntry, DropBoxBackend

from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import FileResponse
from starlette.responses import Response

class S3Backend(DropBoxBackend):
    def __init__(self, config: Config, logger: logging.Logger):
        super().__init__(config, logger)
        
        protocol = "https" if config.use_https else "http"
        endpoint_url = f"{protocol}://{config.service_endpoint}"       
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=config.service_access_key,
            aws_secret_access_key=config.service_secret_key,
            aws_session_token=None,
            config=boto3.session.Config(signature_version='s3v4'),
            verify=config.check_ssl_certificate  
        )
        self.bucket_name = config.service_bucket
            
    async def get_directory_tree(self) -> tuple[DropBoxEntry, ...]:
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
        if 'Contents' not in response:
            return ()

        entries = []
        for obj in response['Contents']:
            entry = DropBoxEntry(
                name=obj['Key'],
                size=obj['Size'],
                last_modified=obj['LastModified']
            )
            entries.append(entry)

        return tuple(entries)


    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:  # pragma: no cover
        file_obj = await request.body()
        self.s3_client.upload_fileobj(
            file_obj,
            self.bucket_name,
            path
        )
        return Response(status_code=201)

    async def retrieve_from_path(self, path: str) -> Response:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
        file_content = response['Body'].read()
        return Response(content=file_content, media_type='application/octet-stream')


    async def delete_at_path(self, path: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)