from __future__ import annotations

from os import stat_result

from pydantic import BaseModel, RootModel

__all__ = [
    "DropBoxEntryBase",
    "DropBoxEntryFile",
    "DropBoxEntryDirectory",
    "DropBoxEntry",
    "DropBoxEntriesResponse",
]


class DropBoxEntryBase(BaseModel):
    name: str
    filePath: str
    relativePath: str

    def to_file(self, uri: str, stat: stat_result) -> DropBoxEntry:
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


class DropBoxEntriesResponse(RootModel):
    root: tuple[DropBoxEntry, ...]
