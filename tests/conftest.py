"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import struct
import zlib

import pytest

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _chunk(chunk_type: bytes, body: bytes) -> bytes:
    return (
        len(body).to_bytes(4, "big")
        + chunk_type
        + body
        + zlib.crc32(chunk_type + body).to_bytes(4, "big")
    )


def make_png(width: int = 64, height: int = 64, *, ancillary: bool = False) -> bytes:
    """Build a minimal valid 8-bit grayscale PNG in memory.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        ancillary: When ``True``, include a non-essential ``tEXt`` chunk that
            the packer is expected to drop.
    """

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (None)
        raw.extend((x + y) % 256 for x in range(width))
    idat = zlib.compress(bytes(raw), 9)

    data = bytearray(PNG_MAGIC)
    data += _chunk(b"IHDR", ihdr)
    if ancillary:
        data += _chunk(b"tEXt", b"Comment\x00dropme")
    data += _chunk(b"IDAT", idat)
    data += _chunk(b"IEND", b"")
    return bytes(data)


def make_zip(*, name: str = "hello.txt", content: bytes = b"hello world") -> bytes:
    """Build a small ZIP archive in memory."""

    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, content)
    return buffer.getvalue()


@pytest.fixture
def cover_png(tmp_path):
    path = tmp_path / "cover.png"
    path.write_bytes(make_png())
    return path
