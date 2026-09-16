"""Storage abstraction.

Defines a backend-agnostic ``StorageBackend`` protocol plus the default
local-filesystem implementation. A factory (``create_storage``) selects the
concrete backend from ``core.config.settings`` so the application can migrate
to S3 (or any object store) without touching call sites.

Security properties:
    * Stored keys are random (uuid4) + a sanitized suffix, so client-supplied
      filenames can never influence the on-disk path.
    * ``get_file_path`` re-resolves and verifies the path stays inside the
      storage root (defence-in-depth against a poisoned DB row).
    * ``save`` streams in fixed-size chunks (no full-file buffering into memory)
      and can enforce a hard size cap, deleting partial files on failure.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Protocol, Union

from fastapi import HTTPException, status

from core.config import settings

# Chunk size used when streaming uploads (1 MiB).
_CHUNK_SIZE = 1024 * 1024


class StorageBackend(Protocol):
    """Minimal interface every storage backend must satisfy.

    ``key`` is an opaque, server-chosen identifier (not a client filename).
    """

    def save(self, stream: BinaryIO, filename: Optional[str], max_size: Optional[int] = None) -> str: ...

    def delete(self, key: str) -> bool: ...

    def get_file_path(self, key: str) -> Path: ...

    def file_exists(self, key: str) -> bool: ...

    def open(self, key: str) -> BinaryIO: ...

    def size(self, key: str) -> int: ...


def sanitize_filename(filename: Optional[str]) -> str:
    """Reduce an arbitrary filename to a safe, collision-free suffix."""
    if not filename:
        return "unnamed"
    filename = filename.replace("/", "").replace("\\", "").replace("\x00", "")
    safe_chars = re.sub(r"[^\w.\-]", "", filename)
    return safe_chars[:64] or "unnamed_file"


class LocalStorage(StorageBackend):
    """Local-disk storage backend (default, zero external dependencies)."""

    def __init__(self, storage_path: Optional[Union[str, Path]] = None):
        self.storage_path = Path(storage_path or settings.STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _assert_within_root(self, candidate: Path) -> Path:
        root = self.storage_path.resolve()
        resolved = candidate.resolve()
        if root != resolved and root not in resolved.parents:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage key escapes the configured storage root",
            )
        return resolved

    def save(self, stream: BinaryIO, filename: Optional[str], max_size: Optional[int] = None) -> str:
        """Stream ``stream`` to disk in chunks, enforcing an optional size cap."""
        key = f"{uuid.uuid4().hex}_{sanitize_filename(filename)}"
        dest = self.get_file_path(key)
        try:
            written = 0
            with open(dest, "wb") as buffer:
                while True:
                    chunk = stream.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    written += len(chunk)
                    if max_size is not None and written > max_size:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File size exceeds the allowed limit.",
                        )
                    buffer.write(chunk)
            return key
        except HTTPException:
            dest.unlink(missing_ok=True)
            raise
        except OSError as exc:
            dest.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file.",
            ) from exc

    def get_file_path(self, key: str) -> Path:
        return self._assert_within_root(self.storage_path / key)

    def delete(self, key: str) -> bool:
        path = self.get_file_path(key)
        if path.exists():
            try:
                path.unlink()
                return True
            except OSError:
                return False
        return False

    def file_exists(self, key: str) -> bool:
        return self.get_file_path(key).exists()

    def open(self, key: str) -> BinaryIO:
        """Return a read-mode file object for streaming the stored object.

        The resolved path is re-verified to stay inside the storage root, and a
        missing object raises HTTP 410 (the row may exist but the file be gone).
        """
        path = self.get_file_path(key)
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Media file is no longer available.",
            )
        try:
            return path.open("rb")
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read media file.",
            ) from exc

    def size(self, key: str) -> int:
        return self.get_file_path(key).stat().st_size


def create_storage() -> StorageBackend:
    """Select the configured storage backend (``local`` by default)."""
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "local":
        return LocalStorage()
    raise ValueError(f"Unknown STORAGE_BACKEND: {settings.STORAGE_BACKEND!r}")


# Backwards-compatible alias for code/tests that imported the old class name.
StorageService = LocalStorage
