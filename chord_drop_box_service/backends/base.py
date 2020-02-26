from abc import ABC, abstractmethod
from typing import Tuple
from werkzeug import Request, Response


__all__ = ["DropBoxBackend"]


class DropBoxBackend(ABC):
    @abstractmethod
    def get_directory_tree(self) -> Tuple[dict]:
        pass

    @abstractmethod
    def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        pass

    @abstractmethod
    def retrieve_from_path(self, path: str) -> Response:
        pass

    def close(self):
        pass
