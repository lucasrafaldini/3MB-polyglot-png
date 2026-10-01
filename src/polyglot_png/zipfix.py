"""Helpers for keeping embedded ZIP archives valid after relocation.

When a ZIP archive is appended inside the ``IDAT`` chunk of a PNG, every
absolute offset stored in the archive's central directory shifts by the number
of bytes that precede the archive in the final file. These helpers rewrite
those offsets so the resulting polyglot is *also* a valid ZIP archive.

The functions operate in place on a :class:`bytearray` and support a signed
``delta`` so the same logic can shift offsets forward (when packing) or
backward (when extracting).
"""

from __future__ import annotations

from struct import unpack_from

__all__ = ["looks_like_zip", "shift_zip_offsets"]

#: End Of Central Directory record signature.
_EOCD_SIGNATURE = b"PK\x05\x06"
#: Central Directory file header signature.
_CENTRAL_DIR_SIGNATURE = b"PK\x01\x02"
#: Offset of the "number of central directory records" field within the EOCD.
_EOCD_ENTRY_COUNT_OFFSET = 10
#: Offset of the "central directory start offset" field within the EOCD.
_EOCD_CD_START_OFFSET = 16
#: Offset of the "relative offset of local header" field within a CD entry.
_CD_LOCAL_HEADER_OFFSET = 42


def looks_like_zip(data: bytes) -> bool:
    """Return ``True`` when *data* appears to contain a ZIP archive.

    The check is intentionally lenient: it only confirms that an End Of Central
    Directory record is present, which is enough to decide whether offset
    fix-ups are worth attempting.
    """

    return _EOCD_SIGNATURE in data


def shift_zip_offsets(data: bytearray, delta: int) -> None:
    """Shift every absolute offset in a ZIP's central directory by *delta*.

    Args:
        data: The ZIP archive bytes, modified in place.
        delta: Number of bytes to add to each stored offset. Use a positive
            value when embedding the archive at a later position and a negative
            value to reverse that shift during extraction.

    Raises:
        ValueError: If no End Of Central Directory record can be found, meaning
            *data* is not a ZIP archive we know how to fix up.
    """

    if delta == 0:
        return

    try:
        eocd_offset = data.rindex(_EOCD_SIGNATURE)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("No ZIP End Of Central Directory record found.") from exc

    entry_count = unpack_from("<H", data, eocd_offset + _EOCD_ENTRY_COUNT_OFFSET)[0]

    # Fix the pointer to the start of the central directory.
    cd_start_range = slice(
        eocd_offset + _EOCD_CD_START_OFFSET,
        eocd_offset + _EOCD_CD_START_OFFSET + 4,
    )
    cd_start = int.from_bytes(data[cd_start_range], "little")
    data[cd_start_range] = (cd_start + delta).to_bytes(4, "little")

    # Walk each central directory entry and fix its local-header pointer.
    # Search from the start of the buffer so this works whether the stored
    # offsets are being shifted forward (packing) or backward (extraction).
    search_from = 0
    for _ in range(entry_count):
        entry_offset = data.index(_CENTRAL_DIR_SIGNATURE, search_from)
        local_header_range = slice(
            entry_offset + _CD_LOCAL_HEADER_OFFSET,
            entry_offset + _CD_LOCAL_HEADER_OFFSET + 4,
        )
        local_header_offset = int.from_bytes(data[local_header_range], "little")
        data[local_header_range] = (local_header_offset + delta).to_bytes(4, "little")
        search_from = entry_offset + 1
