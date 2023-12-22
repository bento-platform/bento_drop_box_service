from bento_lib.config.pydantic import BentoBaseConfig
from fastapi import Depends
from functools import lru_cache
from typing import Annotated, Literal

from .constants import SERVICE_TYPE

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]


class Config(BentoBaseConfig):
    service_id: str = str(":".join(list(SERVICE_TYPE.values())[:2]))
    service_name: str = "Bento Drop Box Service"
    service_description: str = "Drop box service for a Bento platform node."
    service_url: str = "http://127.0.0.1:5000"  # base URL to construct object URIs from

    service_data: str = "data/"
    service_data_source: Literal["local"] = "local"
    traversal_limit: int = 16

    authz_enabled: bool = True


@lru_cache()
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
