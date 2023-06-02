from fastapi import Depends
from functools import lru_cache
from typing import Annotated

from ..config import ConfigDependency
from ..logger import LoggerDependency

from .base import DropBoxBackend
from .local import LocalBackend
from .minio import MinioBackend


__all__ = [
    "get_backend",
    "BackendDependency",
]


@lru_cache()
def get_backend(config: ConfigDependency, logger: LoggerDependency) -> DropBoxBackend:
    return LocalBackend(config, logger) if config.service_data_source == "local" else MinioBackend(config, logger)


BackendDependency = Annotated[DropBoxBackend, Depends(get_backend)]
