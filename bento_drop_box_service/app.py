from bento_lib.apps.fastapi import BentoFastAPI
from bento_lib.service_info.types import BentoExtraServiceInfo

from . import __version__
from .authz import authz_middleware
from .config import get_config
from .constants import BENTO_SERVICE_KIND, SERVICE_TYPE
from .logger import get_logger
from .routes import drop_box_router

__all__ = [
    "application",
]


BENTO_SERVICE_INFO: BentoExtraServiceInfo = {
    "serviceKind": BENTO_SERVICE_KIND,
    "gitRepository": "https://github.com/bento-platform/bento_drop_box_service",
}

# TODO: Find a way to DI this
config_for_setup = get_config()
logger = get_logger(config_for_setup)

application = BentoFastAPI(authz_middleware, config_for_setup, logger, BENTO_SERVICE_INFO, SERVICE_TYPE, __version__)
application.include_router(drop_box_router)

# Backend init logs
logger.info(f"Using {'S3' if config_for_setup.use_s3_backend else 'local'} storage backend")

if config_for_setup.use_s3_backend:
    logger.info(f"S3 endpoint: {config_for_setup.s3_endpoint}")
