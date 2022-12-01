import boto3
import pytest_asyncio
import pathlib
from moto import mock_s3


local_dir = str(pathlib.Path(__file__).parent / "test_data")
bucket_name = "test"


@pytest_asyncio.fixture()
async def client_minio():
    from bento_drop_box_service.app import application

    with mock_s3():
        s3 = boto3.resource('s3')
        s3.create_bucket(Bucket=bucket_name)

        s3.Object(bucket_name, 'patate.txt').put()
        s3.Object(bucket_name, 'some_dir/patate.txt').put()
        s3.Object(bucket_name, 'some_dir/some_other_dir/patate.txt').put()

        application.config["MINIO_RESOURCE"] = s3
        application.config["MINIO_BUCKET"] = bucket_name
        application.config["SERVICE_DATA_SOURCE"] = "minio"
        yield application.test_client()


@pytest_asyncio.fixture()
async def client_local():
    from bento_drop_box_service.app import application
    application.config["SERVICE_DATA_SOURCE"] = "local"
    application.config["SERVICE_DATA"] = local_dir
    yield application.test_client()
