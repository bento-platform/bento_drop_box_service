import boto3
import pathlib
import pytest

from fastapi.testclient import TestClient
from functools import lru_cache
from moto import mock_s3

from bento_drop_box_service.config import Config, get_config


local_dir = str(pathlib.Path(__file__).parent / "test_data")
bucket_name = "test"


def get_test_minio_config():
    with mock_s3():
        s3 = boto3.resource('s3')
        s3.create_bucket(Bucket=bucket_name)

        s3.Object(bucket_name, 'patate.txt').put()
        s3.Object(bucket_name, 'some_dir/patate.txt').put()
        s3.Object(bucket_name, 'some_dir/some_other_dir/patate.txt').put()

        yield Config(
            bento_debug=True,
            cors_origins=("*",),
            service_data_source="minio",
            minio_resource=s3,
            minio_bucket=bucket_name,
        )


@lru_cache
def get_test_local_config():
    return Config(
        bento_debug=True,
        cors_origins=("*",),
        service_data_source="local",
        service_data=local_dir,
    )


@pytest.fixture()
def client_minio():
    from bento_drop_box_service.app import application
    application.dependency_overrides[get_config] = get_test_minio_config
    yield TestClient(application)


@pytest.fixture()
def client_local():
    from bento_drop_box_service.app import application
    application.dependency_overrides[get_config] = get_test_local_config
    yield TestClient(application)
