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
    return Config(
        bento_debug=True,
        authz_enabled=False,
        cors_origins=("*",),
        service_data_source="local",
        service_data=local_dir,
        bento_authz_service_url="https://skip",
    )


@pytest.fixture()
def test_config():
    yield get_test_local_config()


@pytest.fixture()
def client_local(test_config: Config):
    os.environ["BENTO_DEBUG"] = str(test_config.bento_debug)
    os.environ["AUTHZ_ENABLED"] = str(test_config.authz_enabled)
    os.environ["CORS_ORIGINS"] = "*"
    os.environ["BENTO_AUTHZ_SERVICE_URL"] = test_config.bento_authz_service_url

    from bento_drop_box_service.app import application
    application.dependency_overrides[get_config] = get_test_local_config
    yield TestClient(application)
