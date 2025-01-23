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
    
    use_https: bool = True
    check_ssl_certificate: bool = False    
    service_access_key: str = "rXKVXeGgEQSA20ohl47y"
    service_secret_key: str = "FSnab2mkkeZB7CwG2ribIjwmIFOdbMa2qOITI1SR"
    service_endpoint: str = "minio.bentov2.local"
    service_bucket: str = "drop-box"
    
    use_s3_backend: bool = True if service_endpoint else False


@lru_cache()
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
