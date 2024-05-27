from bento_lib.config.pydantic import BentoFastAPIBaseConfig
from fastapi import Depends
from functools import lru_cache
from typing import Annotated, Literal

from .constants import SERVICE_TYPE

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]


class Config(BentoFastAPIBaseConfig):
    service_id: str = str(":".join(list(SERVICE_TYPE.values())[:2]))
    service_name: str = "Bento Drop Box Service"
    service_description: str = "Drop box service for a Bento platform node."

    service_data: str = "data/"
    service_data_source: Literal["local"] = "local"
    traversal_limit: int = 16


@lru_cache()
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
