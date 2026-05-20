from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from fastapi import HTTPException, Request, Response, status
from os import stat_result
from pydantic import BaseModel, RootModel

from ..config import Config


__all__ = ["DropBoxEntryBase", "DropBoxEntryFile", "DropBoxEntryDirectory", "DropBoxEntry", "DropBoxBackend"]


class DropBoxEntryBase(BaseModel):
    name: str
    filePath: str
    relativePath: str

    def to_file(self, uri: str, stat: stat_result) -> DropBoxEntry:
        # noinspection PyArgumentList
        return DropBoxEntry(
            DropBoxEntryFile(
                name=self.name,
                filePath=self.filePath,
                relativePath=self.relativePath,
                uri=uri,
                size=stat.st_size,
                lastModified=stat.st_mtime,
                lastMetadataChange=stat.st_ctime,
            )
        )

    def to_directory(self, contents: list[DropBoxEntry]) -> DropBoxEntry:
        # noinspection PyArgumentList
        return DropBoxEntry(
            DropBoxEntryDirectory(
                name=self.name, filePath=self.filePath, relativePath=self.relativePath, contents=contents
            )
        )


class DropBoxEntryFile(DropBoxEntryBase):
    uri: str
    size: int
    lastModified: float
    lastMetadataChange: float


class DropBoxEntryDirectory(DropBoxEntryBase):
    contents: list[DropBoxEntry]


class DropBoxEntry(RootModel):
    root: DropBoxEntryFile | DropBoxEntryDirectory


# class DropBoxEntry(TypedDict):
#     name: str
#     filePath: str
#     relativePath: str
#     # file entries:
#     uri: NotRequired[str]
#     size: NotRequired[int]
#     lastModified: NotRequired[float]
#     lastMetadataChange: NotRequired[float]
#     # directory entries:
#     contents: NotRequired[list[DropBoxEntry]]


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

    @staticmethod
    def is_passing_filter(entry: str, included_extensions: list[str] | None, ignored_extensions: list[str] | None):
        if included_extensions:
            return any([entry.endswith(ext) for ext in included_extensions])
        elif ignored_extensions:
            return not any([entry.endswith(ext) for ext in ignored_extensions])
        else:
            return True

    @staticmethod
    def validate_filters(include: list[str] | None, ignore: list[str] | None):
        if ignore and include:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Include only a single type of filter query parameter"
            )
