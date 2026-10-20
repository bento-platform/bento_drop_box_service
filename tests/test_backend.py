import logging

import pytest

from bento_drop_box_service.backends.dependency import get_backend
from bento_drop_box_service.backends.s3 import S3Backend
from bento_drop_box_service.config import Config

from .conftest import bucket_name


def test_backend_logger(test_config: Config):
    test_logger = logging.getLogger(__name__)
    b = get_backend(test_config, test_logger)
    assert b.logger == test_logger


@pytest.mark.parametrize("validate_ssl", [True, False])
def test_s3_backend_init(test_config: Config, validate_ssl: bool):
    s3_config = Config(s3_bucket=bucket_name, s3_validate_ssl=validate_ssl)
    assert s3_config.use_s3_backend

    b = get_backend(s3_config, logging.getLogger(__name__))
    assert isinstance(b, S3Backend)
    assert b.bucket_name == bucket_name
    assert b.s3_kwargs == {"verify": validate_ssl}
