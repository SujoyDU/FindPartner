"""Content-based (magic-byte) media validation.

Trusts neither the client-supplied ``Content-Type`` header nor the filename
extension. The first bytes of the upload are inspected to determine the real
media type, then checked against the configured allow-list.

Allowed types (see ``core.config.settings``):
    images -> JPEG, PNG, WebP
    videos -> MP4, WebM
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, BinaryIO

from fastapi import HTTPException, status

from core.config import settings

# Number of leading bytes needed to identify every supported container.
HEAD_SIZE = 16


def detect_real_type(head: bytes) -> Optional[str]:
    """Return the canonical MIME type for the given leading bytes, or ``None``."""
    if len(head) < 4:
        return None

    # JPEG: SOI + APP0
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"

    # PNG signature
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"

    # WebP: RIFF....WEBP
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"

    # WebM / Matroska EBML header
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm"

    # ISO-BMFF / MP4: bytes 4-8 are the 'ftyp' brand
    if head[4:8] == b"ftyp":
        return "video/mp4"

    return None


@dataclass(frozen=True)
class DetectedMedia:
    content_type: str
    category: str  # "image" | "video"


def validate_media(stream: BinaryIO) -> DetectedMedia:
    """Peek at the head of ``stream`` and validate it is allowed media.

    The stream is rewound to the start after inspection so the caller can read
    it fully. Raises ``HTTPException`` (415) on any violation.
    """
    head = stream.read(HEAD_SIZE)
    try:
        stream.seek(0)
    except (OSError, ValueError):
        pass  # non-seekable stream: best effort

    real_type = detect_real_type(head)
    if real_type is None or real_type not in settings.ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported media type. Only JPEG, PNG, WebP, MP4 and WebM are allowed.",
        )

    return DetectedMedia(
        content_type=real_type,
        category=real_type.split("/")[0],
    )
