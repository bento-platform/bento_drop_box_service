import asyncio
import os
import pathlib
import urllib.request
from functools import lru_cache

import pytest
from aiobotocore.session import get_session
from fastapi.testclient import TestClient
from moto.server import ThreadedMotoServer

from bento_drop_box_service.config import Config, get_config

local_dir = str(pathlib.Path(__file__).parent / "test_data")
bucket_name = "test"


@lru_cache
def get_test_local_config():
    os.environ["BENTO_DEBUG"] = "True"
    os.environ["BENTO_AUTHZ_ENABLED"] = "False"
    os.environ["CORS_ORIGINS"] = "*"
    os.environ["SERVICE_DATA"] = local_dir
    os.environ["BENTO_AUTHZ_SERVICE_URL"] = "https://skip"
    return Config()


@pytest.fixture()
def test_config():
    yield get_test_local_config()


@pytest.fixture()
def client_local(test_config: Config):
    from bento_drop_box_service.app import application

    application.dependency_overrides[get_config] = get_test_local_config
    yield TestClient(application)


@pytest.fixture(scope="session")
def s3_endpoint():
    # In-process fake S3 server, port 0 picks a free port.
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=0, verbose=False)
    server.start()
    host, port = server.get_host_and_port()
    yield f"http://{host}:{port}"
    server.stop()


async def _create_bucket():
    async with get_session().create_client("s3") as s3:
        await s3.create_bucket(Bucket=bucket_name)


@pytest.fixture()
def client_s3(test_config: Config, s3_endpoint: str, monkeypatch: pytest.MonkeyPatch):
    from bento_drop_box_service.app import application

    # The S3 backend reads credentials, region and endpoint from the standard AWS env vars.
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ENDPOINT_URL_S3", s3_endpoint)

    # Start each test from an empty bucket
    urllib.request.urlopen(urllib.request.Request(f"{s3_endpoint}/moto-api/reset", method="POST"))
    asyncio.run(_create_bucket())

    s3_config = Config(s3_bucket=bucket_name)
    application.dependency_overrides[get_config] = lambda: s3_config
    yield TestClient(application)
    application.dependency_overrides.pop(get_config, None)
