from fastapi import Depends
from functools import lru_cache
from typing import Annotated

from ..config import ConfigDependency
from ..logger import LoggerDependency

from .base import DropBoxBackend
from .local import LocalBackend


__all__ = [
    "get_backend",
    "BackendDependency",
]


@lru_cache()
def get_backend(config: ConfigDependency, logger: LoggerDependency) -> DropBoxBackend:
    return LocalBackend(config, logger)


BackendDependency = Annotated[DropBoxBackend, Depends(get_backend)]
