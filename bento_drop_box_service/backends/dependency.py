from fastapi import Depends
from functools import lru_cache
from typing import Annotated

from ..config import ConfigDependency
from ..logger import LoggerDependency

from .base import DropBoxBackend
from .local import LocalBackend
from .s3 import S3Backend


__all__ = [
    "get_backend",
    "BackendDependency",
]


@lru_cache()
def get_backend(config: ConfigDependency, logger: LoggerDependency) -> DropBoxBackend:
    if config.use_s3_backend:
        return S3Backend(config, logger)
    return LocalBackend(config, logger)


BackendDependency = Annotated[DropBoxBackend, Depends(get_backend)]
