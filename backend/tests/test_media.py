# backend/tests/test_media.py
"""Tests for the media service (new schema) and streaming helpers.

Covers the security-sensitive ownership rules (BOLA / IDOR) with the updated
``Media``/``MediaShare`` models (UUID ``owner_id``, media lives on the storage
backend, share links in ``MediaShare``).
"""

import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.media.service import MediaService
from app.media.storage_service import LocalStorage
from app.media.validators import detect_real_type


# --------------------------------------------------------------------------- #
# Sample media builder (mimics a row owned by a specific user)
# --------------------------------------------------------------------------- #
def _media(owner_id, *, is_public=False, storage_key="key_1", media_type="image", mime="image/jpeg"):
    m = Mock()  # plain attribute mock; we assert on ownership fields
    m.id = uuid.uuid4()
    m.owner_id = owner_id
    m.is_public = is_public
    m.storage_key = storage_key
    m.media_type = media_type
    m.mime_type = mime
    m.file_name = "sample.jpg"
    m.file_size = 12
    m.created_at = datetime(2026, 1, 1, tzinfo=None)
    m.updated_at = datetime(2026, 1, 1, tzinfo=None)
    return m


@pytest.fixture
def service():
    return MediaService(db=Mock(spec=Session), storage=Mock())


# --------------------------------------------------------------------------- #
# Ownership / access control (BOLA / IDOR)
# --------------------------------------------------------------------------- #
def test_owner_can_fetch_own_media(service):
    mine = _media(uuid.uuid4())
    service.db.query.return_value.filter.return_value.first.return_value = mine
    assert service.get_media_by_id(mine.id, mine.owner_id) is mine


def test_non_owner_cannot_fetch_private_media(service):
    # The service filters by Media.owner_id == caller; a non-owner lookup yields
    # no row (the caller cannot even see that another user's item exists).
    service.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        service.get_media_by_id(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_unknown_media_returns_404(service):
    service.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        service.get_media_by_id(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_delete_media_non_owner_returns_404(service):
    # Ownership filter yields no row -> 404, and the file must NOT be touched.
    service.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        service.delete_media(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    service.storage.delete.assert_not_called()


def test_delete_media_owner_removes_file(service):
    mine = _media(uuid.uuid4(), storage_key="delete_me")
    service.db.query.return_value.filter.return_value.first.return_value = mine
    service.storage.delete.return_value = True
    assert service.delete_media(mine.id, mine.owner_id) is True
    service.storage.delete.assert_called_once_with("delete_me")


# --------------------------------------------------------------------------- #
# Sharing (visibility)
# --------------------------------------------------------------------------- #
def test_public_media_resolves_via_share_token(service):
    media = _media(uuid.uuid4(), is_public=True)
    share = Mock()
    share.media_id = media.id
    share.share_token = "abc123"

    # Make the shared DB lookup alternate: 1st call -> share (get_share_by_token),
    # 2nd call -> media (get_public_media, filtered by share.media_id).
    service.db.query.return_value.filter.return_value.first.side_effect = [share, media]
    assert service.get_public_media_by_share_token("abc123") is media


def test_invalid_share_token_returns_404(service):
    service.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        service.get_public_media_by_share_token("bad_token")
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_revoking_public_media_returns_404_on_token(service):
    # Token resolves to a share, but the media is no longer public.
    media = _media(uuid.uuid4(), is_public=False)
    share = Mock()
    share.media_id = media.id
    share.share_token = "tok"
    service.db.query.return_value.filter.return_value.first.side_effect = [share, media]
    with pytest.raises(HTTPException) as exc:
        service.get_public_media_by_share_token("tok")
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------------------------------- #
# Magic-byte type detection (upload validation)
# --------------------------------------------------------------------------- #
def test_detect_jpeg_magic_bytes():
    assert detect_real_type(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01") == "image/jpeg"


def test_detect_png_magic_bytes():
    assert detect_real_type(b"\x89PNG\r\n\x1a\n\x00\x00\x00") == "image/png"


def test_reject_unsupported_type():
    assert detect_real_type(b"PK\x03\x04") is None  # zip / not media


# --------------------------------------------------------------------------- #
# Streaming helpers (files live on storage, never in the DB)
# --------------------------------------------------------------------------- #
def test_open_stream_uses_storage_key(tmp_path):
    backend = LocalStorage(tmp_path)
    key = backend.save(_bytes(b"hello"), "x.jpg")
    svc = MediaService(db=Mock(spec=Session), storage=backend)
    media = _media(uuid.uuid4(), storage_key=key)
    with svc.open_stream(media) as fh:
        assert fh.read() == b"hello"


def test_size_helper(tmp_path):
    backend = LocalStorage(tmp_path)
    key = backend.save(_bytes(b"12345"), "x.jpg")
    svc = MediaService(db=Mock(spec=Session), storage=backend)
    assert svc.stream_size(_media(uuid.uuid4(), storage_key=key)) == 5


def _bytes(data: bytes):
    import io
    return io.BytesIO(data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
