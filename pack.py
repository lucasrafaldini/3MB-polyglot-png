#!/usr/bin/env python3
"""Backwards-compatible shim for the original ``python pack.py`` interface.

The project now lives in the :mod:`polyglot_png` package with a proper CLI::

    polyglot-png pack COVER PAYLOAD OUTPUT
    python -m polyglot_png pack COVER PAYLOAD OUTPUT

This shim keeps the historical ``python pack.py COVER PAYLOAD OUTPUT`` call
working so existing scripts and tutorials do not break.
"""

from __future__ import annotations

import os
import sys

# Make the package importable when running from a plain source checkout.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from polyglot_png.cli import main  # noqa: E402,I001

if __name__ == "__main__":
    args = sys.argv[1:]
    # Preserve the legacy positional-only interface: pack.py COVER PAYLOAD OUTPUT
    if args and args[0] not in {"pack", "unpack", "--version", "-h", "--help"}:
        print(
            "note: 'python pack.py COVER PAYLOAD OUTPUT' is deprecated; "
            "use 'polyglot-png pack COVER PAYLOAD OUTPUT'.",
            file=sys.stderr,
        )
        args = ["pack", *args]
    raise SystemExit(main(args))
