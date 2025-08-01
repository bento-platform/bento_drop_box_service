from bento_lib.config.pydantic import BentoFastAPIBaseConfig
from fastapi import Depends
from functools import lru_cache
from pydantic import Field
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

    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_region_name: str = ""
    s3_validate_ssl: bool = False
    s3_use_https: bool = True
    s3_chunk_size: int = 64 * 1024
    use_s3_backend: bool = Field(default_factory=lambda c: c["s3_endpoint"] != "")


@lru_cache()
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
