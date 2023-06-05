import logging
from abc import ABC, abstractmethod
from fastapi import Request, Response
from typing import TypedDict

from ..config import Config


__all__ = ["DropBoxEntry", "DropBoxBackend"]


# TODO: py3.11: individual optional fields
class DropBoxEntry(TypedDict, total=False):
    name: str
    filePath: str
    relativePath: str
    uri: str
    size: int
    lastModified: float
    lastMetadataChange: float
    contents: tuple["DropBoxEntry", ...]


class DropBoxBackend(ABC):
    def __init__(self, config: Config, logger: logging.Logger):
        self._config = config
        self._logger = logger

    @property
    def config(self) -> Config:
        return self._config

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @abstractmethod
    async def get_directory_tree(self) -> tuple[DropBoxEntry, ...]:
        pass

    @abstractmethod
    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        pass

    @abstractmethod
    async def retrieve_from_path(self, path: str) -> Response:
        pass
