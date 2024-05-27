import os
import pathlib
import pytest

from fastapi.testclient import TestClient
from functools import lru_cache

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
