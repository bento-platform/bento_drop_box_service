from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from .config import get_config
from .logger import get_logger

__all__ = [
    "authz_middleware",
]

# TODO: Find a way to DI this
config = get_config()

# Non-standard middleware setup so that we can import the instance and use it for dependencies too
authz_middleware = FastApiAuthMiddleware.build_from_pydantic_config(config, get_logger(config))
