import os
from typing import Optional
from flask import current_app, g
from .backends.base import DropBoxBackend
from .backends.local import LocalBackend
from .backends.minio import MinioBackend


__all__ = [
    "get_backend",
    "close_backend",
]


def _get_backend() -> Optional[DropBoxBackend]:
    # Make data directory/ies if needed
    if current_app.config['SERVICE_DATA_SOURCE'] == 'local':
        os.makedirs(current_app.config["SERVICE_DATA"], exist_ok=True)
        return LocalBackend()

    elif current_app.config['SERVICE_DATA_SOURCE'] == 'minio':
        return MinioBackend()

    return None


def get_backend() -> Optional[DropBoxBackend]:
    if "backend" not in g:
        g.backend = _get_backend()
    return g.backend


def close_backend(_e=None):
    backend = g.pop("backend", None)
    if backend is not None:
        backend.close()
