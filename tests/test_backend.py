import logging

from bento_drop_box_service.backends.dependency import get_backend
from bento_drop_box_service.config import Config


def test_backend_logger(test_config: Config):
    test_logger = logging.getLogger(__name__)
    b = get_backend(test_config, test_logger)
    assert b.logger == test_logger
