"""Tests for the pack/unpack round trip and error handling."""

from __future__ import annotations

import io
import zipfile

import pytest

from polyglot_png import PolyglotError, pack, unpack
from polyglot_png.packer import PNG_MAGIC

from .conftest import make_png, make_zip


def test_pack_produces_valid_png(cover_png, tmp_path):
    payload = tmp_path / "secret.bin"
    payload.write_bytes(b"top secret payload")
    out = tmp_path / "out.png"

    result = pack(cover_png, payload, out)

    data = out.read_bytes()
    assert data.startswith(PNG_MAGIC)
    assert data.rstrip().endswith(b"IEND" + b"\xae\x42\x60\x82")
    assert result.payload_size == len(b"top secret payload")
    assert result.total_size == out.stat().st_size


def test_round_trip_plain_payload(cover_png, tmp_path):
    secret = b"the quick brown fox" * 10
    payload = tmp_path / "secret.bin"
    payload.write_bytes(secret)
    out = tmp_path / "out.png"
    extracted = tmp_path / "extracted.bin"

    pack(cover_png, payload, out)
    result = unpack(out, extracted)

    assert extracted.read_bytes() == secret
    assert result.payload_size == len(secret)


def test_round_trip_zip_payload_is_valid_archive(cover_png, tmp_path):
    zip_bytes = make_zip(name="hello.txt", content=b"hello world")
    payload = tmp_path / "secret.zip"
    payload.write_bytes(zip_bytes)
    out = tmp_path / "out.png"

    pack(cover_png, payload, out)

    # The whole polyglot PNG should itself be a readable ZIP archive.
    polyglot_bytes = out.read_bytes()
    with zipfile.ZipFile(io.BytesIO(polyglot_bytes)) as archive:
        assert archive.read("hello.txt") == b"hello world"


def test_unpack_restores_original_zip_with_fix(cover_png, tmp_path):
    zip_bytes = make_zip()
    payload = tmp_path / "secret.zip"
    payload.write_bytes(zip_bytes)
    out = tmp_path / "out.png"
    extracted = tmp_path / "extracted.zip"

    pack(cover_png, payload, out)
    unpack(out, extracted, fix_zip=True)

    assert extracted.read_bytes() == zip_bytes


def test_pack_drops_ancillary_chunks(tmp_path):
    cover = tmp_path / "cover.png"
    cover.write_bytes(make_png(ancillary=True))
    payload = tmp_path / "secret.bin"
    payload.write_bytes(b"data")
    out = tmp_path / "out.png"

    pack(cover, payload, out)

    assert b"tEXt" not in out.read_bytes()


def test_pack_rejects_non_png(tmp_path):
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"not a png")
    payload = tmp_path / "secret.bin"
    payload.write_bytes(b"data")
    out = tmp_path / "out.png"

    with pytest.raises(PolyglotError, match="not a valid PNG"):
        pack(cover, payload, out)


def test_pack_rejects_oversized_payload(tmp_path):
    cover = tmp_path / "cover.png"
    cover.write_bytes(make_png(width=16, height=16))  # budget = 256 bytes
    payload = tmp_path / "secret.bin"
    payload.write_bytes(b"x" * 1000)
    out = tmp_path / "out.png"

    with pytest.raises(PolyglotError, match="too big"):
        pack(cover, payload, out)


def test_unpack_rejects_png_without_payload(cover_png, tmp_path):
    extracted = tmp_path / "extracted.bin"
    with pytest.raises(PolyglotError, match="No trailing payload"):
        unpack(cover_png, extracted)
