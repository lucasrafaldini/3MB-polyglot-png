"""Command-line interface for :mod:`polyglot_png`."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional, Sequence

from . import __version__
from .packer import DEFAULT_MAX_OUTPUT_BYTES, PolyglotError, pack, unpack


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polyglot-png",
        description="Hide a file inside a tweetable PNG polyglot, and get it back out.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable informational logging.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    pack_cmd = subparsers.add_parser("pack", help="Embed a file into a cover PNG.")
    pack_cmd.add_argument("cover", help="Path to the cover PNG image.")
    pack_cmd.add_argument("payload", help="Path to the file to hide.")
    pack_cmd.add_argument("output", help="Path of the polyglot PNG to create.")
    zip_group = pack_cmd.add_mutually_exclusive_group()
    zip_group.add_argument(
        "--fix-zip",
        dest="fix_zip",
        action="store_true",
        default=None,
        help="Force rewriting of ZIP offsets (default: auto-detect).",
    )
    zip_group.add_argument(
        "--no-fix-zip",
        dest="fix_zip",
        action="store_false",
        help="Never rewrite ZIP offsets.",
    )
    pack_cmd.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
        help="Warn if the output exceeds this size (0 disables the check).",
    )

    unpack_cmd = subparsers.add_parser("unpack", help="Extract a hidden file from a polyglot PNG.")
    unpack_cmd.add_argument("polyglot", help="Path to the polyglot PNG.")
    unpack_cmd.add_argument("output", help="Path to write the extracted payload to.")
    unpack_cmd.add_argument(
        "--fix-zip",
        dest="fix_zip",
        action="store_true",
        help="Reverse ZIP offset fix-up to restore the original archive.",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the ``polyglot-png`` console script."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    try:
        if args.command == "pack":
            result = pack(
                args.cover,
                args.payload,
                args.output,
                fix_zip=args.fix_zip,
                max_output_bytes=args.max_output_bytes,
            )
            print(
                f"Packed {result.payload_size} bytes into {result.output_path} "
                f"({result.image_width}x{result.image_height}px, "
                f"payload at offset 0x{result.payload_offset:x}, "
                f"total {result.total_size} bytes)."
            )
        elif args.command == "unpack":
            result = unpack(args.polyglot, args.output, fix_zip=args.fix_zip)
            print(
                f"Extracted {result.payload_size} bytes to {result.output_path} "
                f"(from offset 0x{result.payload_offset:x})."
            )
    except (PolyglotError, FileNotFoundError, IsADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
