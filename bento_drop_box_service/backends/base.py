import logging
from abc import ABC, abstractmethod
from typing import Tuple
from werkzeug import Request, Response


__all__ = ["DropBoxBackend"]


class DropBoxBackend(ABC):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @abstractmethod
    async def get_directory_tree(self) -> Tuple[dict]:
        pass

    @abstractmethod
    async def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        pass

    @abstractmethod
    async def retrieve_from_path(self, path: str) -> Response:
        pass

    async def close(self):
        pass
