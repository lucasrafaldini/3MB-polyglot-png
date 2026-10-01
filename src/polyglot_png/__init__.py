"""Pack up to 3 MB of arbitrary data into a tweetable PNG polyglot file."""

from __future__ import annotations

from .packer import (
    DEFAULT_MAX_OUTPUT_BYTES,
    PNG_MAGIC,
    PackResult,
    PolyglotError,
    UnpackResult,
    pack,
    unpack,
)

__version__ = "1.0.0"

__all__ = [
    "pack",
    "unpack",
    "PackResult",
    "UnpackResult",
    "PolyglotError",
    "PNG_MAGIC",
    "DEFAULT_MAX_OUTPUT_BYTES",
    "__version__",
]
