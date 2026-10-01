"""Allow running the package with ``python -m polyglot_png``."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
