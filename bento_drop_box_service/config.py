from functools import lru_cache
from typing import Annotated, Literal

from bento_lib.config.pydantic import BentoFastAPIBaseConfig
from fastapi import Depends
from pydantic import Field

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

    # S3 credentials, region and endpoint are resolved by botocore from the standard AWS environment variables
    # (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION,AWS_ENDPOINT_URL_S3, AWS_CA_BUNDLE, ...) or AWS_PROFILE.
    s3_bucket: str = ""
    # False disables TLS verification (dev only); prefer AWS_CA_BUNDLE for self-signed certs
    s3_validate_ssl: bool = True
    s3_chunk_size: int = 64 * 1024
    use_s3_backend: bool = Field(default_factory=lambda c: c["s3_bucket"] != "")


@lru_cache
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
