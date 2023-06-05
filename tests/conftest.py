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
        cors_origins=("*",),
        service_data_source="local",
        service_data=local_dir,
    )


@pytest.fixture()
def client_local():
    from bento_drop_box_service.app import application
    application.dependency_overrides[get_config] = get_test_local_config
    yield TestClient(application)
