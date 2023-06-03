import boto3
from fastapi import Depends
from functools import lru_cache
from pydantic import BaseSettings
from typing import Annotated, Any, Literal

from bento_drop_box_service.constants import SERVICE_TYPE

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]


class Config(BaseSettings):
    bento_debug: bool = False

    service_id: str = str(":".join(list(SERVICE_TYPE.values())[:2]))
    service_data_source: Literal["minio", "local"] = "local"
    service_data: str = "data/"
    service_url: str = "http://127.0.0.1:5000"  # base URL to construct object URIs from

    minio_url: str | None = None
    minio_username: str | None = None
    minio_password: str | None = None
    minio_bucket: str | None = None

    # manual application-wide override for MinIO boto3 resource
    # noinspection PyUnresolvedReferences
    minio_resource: boto3.resources.base.ServiceResource | None = None

    traversal_limit: int = 16

    cors_origins: tuple[str, ...] = ()

    log_level: Literal["debug", "info", "warning", "error"] = "debug"

    class Config:
        # Make parent Config instances hashable + immutable
        allow_mutation = False
        frozen = True

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "cors_origins":
                return tuple(x.strip() for x in raw_val.split(";"))
            # noinspection PyUnresolvedReferences
            return cls.json_loads(raw_val)


@lru_cache()
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]