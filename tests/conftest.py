import os
import boto3
from flask import g
from moto import mock_s3
import pytest

from chord_drop_box_service.app import application
from chord_drop_box_service.backends.minio import MinioBackend
from chord_drop_box_service.backends.local import LocalBackend


@pytest.fixture(scope='session')
def client_minio():
    bucket_name = 'test'
    application.config['MINIO_BUCKET'] = bucket_name

    ctx = application.app_context()
    ctx.push()

    with mock_s3():
        s3 = boto3.resource('s3', region_name='ca-central-1')
        minio_backend = MinioBackend(resource=s3)
        g.backend = minio_backend

        s3.create_bucket(Bucket=bucket_name)

        s3.Object(bucket_name, 'patate.txt').put()
        s3.Object(bucket_name, 'some_dir/patate.txt').put()
        s3.Object(bucket_name, 'some_dir/some_other_dir/patate.txt').put()

        yield application.test_client()


@pytest.fixture(scope='function')
def client_local(fs):
    local_dir = '/data'
    application.config["SERVICE_DATA"] = local_dir

    fs.makedirs(local_dir, exist_ok=True)
    fs.create_file(os.path.join(local_dir, 'patate.txt'), contents='test')

    fs.makedirs(os.path.join(local_dir, 'some_dir'), exist_ok=True)
    fs.create_file(os.path.join(local_dir, 'some_dir', 'patate.txt'), contents='test')

    fs.makedirs(os.path.join(local_dir, 'some_dir', 'some_other_dir'), exist_ok=True)
    fs.create_file(os.path.join(local_dir, 'some_dir', 'some_other_dir', 'patate.txt'), contents='test')

    local_backend = LocalBackend()
    g.backend = local_backend

    yield application.test_client()
