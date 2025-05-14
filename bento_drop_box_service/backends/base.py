import logging
from abc import ABC, abstractmethod
from fastapi import HTTPException, Request, Response, status
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
    async def get_directory_tree(
        self,
        sub_path: str | None = None,
        ignore: list[str] | None = None,
        include: list[str] | None = None,
    ) -> tuple[DropBoxEntry, ...]:  # pragma: no cover
        pass

    @abstractmethod
    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:  # pragma: no cover
        pass

    @abstractmethod
    async def retrieve_from_path(self, path: str) -> Response:  # pragma: no cover
        pass

    @abstractmethod
    async def delete_at_path(self, path: str) -> None:  # pragma: no cover
        pass

    def is_passing_filter(
        self, entry: str, included_extensions: list[str] | None, ignored_extensions: list[str] | None
    ):
        if included_extensions:
            return any([entry.endswith(f".{ext}") for ext in included_extensions])
        elif ignored_extensions:
            return not any([entry.endswith(f".{ext}") for ext in ignored_extensions])
        else:
            return True
        
    def validate_filters(self, include: list[str] | None, ignore: list[str] | None):
        if ignore and include:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Include only a single type of filter query parameter"
            )
