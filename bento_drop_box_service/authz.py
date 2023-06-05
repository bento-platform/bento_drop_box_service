from bento_lib.auth.fastapi_middleware import FastApiAuthMiddleware
from .config import get_config

__all__ = [
    "authz_middleware",
]

config = get_config()


# Non-standard middleware setup so that we can import the instance and use it for dependencies too
authz_middleware = FastApiAuthMiddleware(
    config.bento_authz_service_url,
    config.openid_config_url,
    debug_mode=config.bento_debug,
    enabled=config.authz_enabled,
)
