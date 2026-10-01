"""Core packing and extraction logic for PNG polyglot files.

The technique works because an uncompressed PNG ``IDAT`` chunk is a DEFLATE
stream, and DEFLATE decoders stop at the end of the valid stream. Any bytes
appended after that stream are ignored by image viewers but remain byte-for-byte
intact, and survive services (such as Twitter/X) that strip metadata but do not
re-encode conforming images. That trailing region is where we hide the payload.
"""

from __future__ import annotations

import logging
import zlib
from dataclasses import dataclass
from pathlib import Path
from struct import unpack_from
from typing import Union

from .zipfix import looks_like_zip, shift_zip_offsets

logger = logging.getLogger(__name__)

#: The 8-byte signature that begins every PNG file.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: Chunk types that carry image data we must preserve.
_ESSENTIAL_CHUNKS = frozenset({b"IHDR", b"PLTE", b"IDAT", b"IEND"})

#: Service limit: files larger than this tend to be transcoded to JPEG.
DEFAULT_MAX_OUTPUT_BYTES = 3 * 1024 * 1024

PathLike = Union[str, Path]


class PolyglotError(Exception):
    """Raised when an input file cannot be processed into/out of a polyglot."""


@dataclass(frozen=True)
class PackResult:
    """Summary of a successful :func:`pack` operation."""

    output_path: Path
    image_width: int
    image_height: int
    payload_offset: int
    payload_size: int
    total_size: int


@dataclass(frozen=True)
class UnpackResult:
    """Summary of a successful :func:`unpack` operation."""

    output_path: Path
    payload_offset: int
    payload_size: int


def _read_chunk(stream) -> tuple[int, bytes, bytes, bytes]:
    """Read one PNG chunk, returning ``(length, type, body, raw_crc)``.

    Raises:
        PolyglotError: If the stream ends in the middle of a chunk.
    """

    length_bytes = stream.read(4)
    if len(length_bytes) < 4:
        raise PolyglotError("Unexpected end of PNG stream while reading chunk length.")
    length = int.from_bytes(length_bytes, "big")
    chunk_type = stream.read(4)
    body = stream.read(length)
    raw_crc = stream.read(4)
    if len(chunk_type) < 4 or len(body) < length or len(raw_crc) < 4:
        raise PolyglotError(f"Truncated PNG chunk of type {chunk_type!r}.")
    return length, chunk_type, body, raw_crc


def pack(
    cover: PathLike,
    payload: PathLike,
    output: PathLike,
    *,
    fix_zip: Union[bool, None] = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> PackResult:
    """Embed *payload* inside the ``IDAT`` chunk of *cover* and write *output*.

    Args:
        cover: Path to the cover PNG image.
        payload: Path to the file to hide inside the image.
        output: Path of the polyglot PNG to create.
        fix_zip: Whether to rewrite ZIP central-directory offsets so the output
            is also a valid archive. ``None`` (the default) auto-detects based
            on the payload contents; ``True``/``False`` force the behaviour.
        max_output_bytes: Soft ceiling for the output size. Exceeding it emits a
            warning because many services transcode larger PNGs to JPEG, which
            destroys the payload. Pass ``0`` to disable the check.

    Returns:
        A :class:`PackResult` describing the generated file.

    Raises:
        PolyglotError: If the cover is not a valid PNG or the payload does not
            fit within the image's pixel budget.
    """

    cover_path, payload_path, output_path = Path(cover), Path(payload), Path(output)
    payload_bytes = payload_path.read_bytes()

    with cover_path.open("rb") as png_in, output_path.open("wb") as png_out:
        header = png_in.read(len(PNG_MAGIC))
        if header != PNG_MAGIC:
            raise PolyglotError(f"{cover_path} is not a valid PNG file.")
        png_out.write(header)
        logger.info("PNG header is valid.")

        width = height = 0
        idat_body = b""
        result: Union[PackResult, None] = None

        while True:
            length, chunk_type, body, raw_crc = _read_chunk(png_in)

            if chunk_type not in _ESSENTIAL_CHUNKS:
                logger.warning("Dropping non-essential chunk: %s", chunk_type.decode("latin-1"))
                continue

            if chunk_type == b"IHDR":
                width, height = unpack_from(">II", body)
                logger.info("Image size: %dx%dpx", width, height)

            if chunk_type == b"IDAT":
                # Concatenate every IDAT chunk; we re-emit them as one below.
                idat_body += body
                continue

            if chunk_type == b"IEND":
                # The payload begins right after the image's compressed data.
                payload_offset = png_out.tell() + 8 + len(idat_body)
                logger.info("Embedded file starts at offset 0x%x", payload_offset)

                combined = idat_body + payload_bytes
                if len(combined) > width * height:
                    raise PolyglotError(
                        "Payload too big for cover image: needs "
                        f"{len(combined)} bytes but image budget is {width * height} "
                        f"({width}x{height}px). Use a larger cover image."
                    )

                should_fix = looks_like_zip(payload_bytes) if fix_zip is None else fix_zip
                if should_fix:
                    logger.info("Fixing up ZIP offsets...")
                    combined = bytearray(combined)
                    shift_zip_offsets(combined, payload_offset)
                    combined = bytes(combined)

                _write_chunk(png_out, b"IDAT", combined)

                # Final size is filled in after the stream is closed below.
                result = PackResult(
                    output_path=output_path,
                    image_width=width,
                    image_height=height,
                    payload_offset=payload_offset,
                    payload_size=len(payload_bytes),
                    total_size=0,
                )

            # Re-emit IHDR, PLTE and IEND verbatim.
            png_out.write(length.to_bytes(4, "big"))
            png_out.write(chunk_type)
            png_out.write(body)
            png_out.write(raw_crc)

            if chunk_type == b"IEND":
                break

    assert result is not None  # IEND always sets it or we raised earlier.
    final_size = output_path.stat().st_size
    result = PackResult(
        output_path=result.output_path,
        image_width=result.image_width,
        image_height=result.image_height,
        payload_offset=result.payload_offset,
        payload_size=result.payload_size,
        total_size=final_size,
    )

    if max_output_bytes and final_size > max_output_bytes:
        logger.warning(
            "Output is %d bytes, above the %d-byte limit; some services may "
            "transcode it to JPEG and destroy the payload.",
            final_size,
            max_output_bytes,
        )
    return result


def unpack(polyglot: PathLike, output: PathLike, *, fix_zip: bool = False) -> UnpackResult:
    """Extract the payload hidden inside a polyglot PNG.

    The payload is recovered by decompressing the ``IDAT`` DEFLATE stream and
    reading the decoder's trailing ``unused_data``.

    Args:
        polyglot: Path to the polyglot PNG produced by :func:`pack`.
        output: Path to write the extracted payload to.
        fix_zip: When ``True`` and the payload is a ZIP archive, reverse the
            offset fix-up applied during packing so the original archive is
            restored.

    Returns:
        An :class:`UnpackResult` describing the extracted payload.

    Raises:
        PolyglotError: If the file is not a PNG or contains no trailing payload.
    """

    polyglot_path, output_path = Path(polyglot), Path(output)

    with polyglot_path.open("rb") as png_in:
        header = png_in.read(len(PNG_MAGIC))
        if header != PNG_MAGIC:
            raise PolyglotError(f"{polyglot_path} is not a valid PNG file.")

        idat_body = b""
        idat_chunk_offset = -1
        while True:
            chunk_offset = png_in.tell()
            _, chunk_type, body, _ = _read_chunk(png_in)
            if chunk_type == b"IDAT":
                if idat_chunk_offset < 0:
                    idat_chunk_offset = chunk_offset
                idat_body += body
            elif chunk_type == b"IEND":
                break

    if not idat_body:
        raise PolyglotError("No IDAT chunk found; nothing to extract.")

    decompressor = zlib.decompressobj()
    decompressor.decompress(idat_body)
    decompressor.flush()
    payload = decompressor.unused_data
    if not payload:
        raise PolyglotError("No trailing payload found inside the IDAT stream.")

    image_data_len = len(idat_body) - len(payload)
    payload_offset = idat_chunk_offset + 8 + image_data_len

    if fix_zip and looks_like_zip(payload):
        logger.info("Reversing ZIP offset fix-up...")
        payload = bytearray(payload)
        shift_zip_offsets(payload, -payload_offset)
        payload = bytes(payload)

    output_path.write_bytes(payload)
    return UnpackResult(
        output_path=output_path,
        payload_offset=payload_offset,
        payload_size=len(payload),
    )


def _write_chunk(stream, chunk_type: bytes, body: bytes) -> None:
    """Write a single PNG chunk (length, type, body, CRC) to *stream*."""

    stream.write(len(body).to_bytes(4, "big"))
    stream.write(chunk_type)
    stream.write(body)
    stream.write(zlib.crc32(chunk_type + body).to_bytes(4, "big"))
