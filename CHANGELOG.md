# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-01

### Added

- Proper Python package layout under `src/polyglot_png/`.
- A real command-line interface (`polyglot-png`) with `pack` and `unpack`
  subcommands, `--verbose`, `--fix-zip`/`--no-fix-zip`, and `--version`.
- `unpack` command to extract hidden payloads from polyglot PNGs.
- Automatic and reversible ZIP central-directory offset fix-ups.
- `pyproject.toml` with packaging metadata, console-script entry point, and
  tooling config (pytest, ruff).
- Test suite covering the pack/unpack round trip, ZIP handling, ancillary chunk
  dropping, and error cases.
- Community health files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, issue/PR templates, and a CI workflow.

### Changed

- Rewrote the core logic as a documented, typed, reusable library.
- Replaced `print` + unconfigured logging with a single, configurable logging
  setup.
- README expanded with installation, usage, and how-it-works sections.

### Fixed

- Removed the stray `unittest` import.
- The packer no longer mixes instance attributes with `sys.argv` indexing; all
  inputs flow through explicit arguments.
- Truncated or invalid PNGs now raise a clear `PolyglotError` instead of
  failing with an opaque assertion or exception.

### Deprecated

- `python pack.py COVER PAYLOAD OUTPUT` still works but prints a notice; prefer
  `polyglot-png pack ...`.
