<div align="center">

# 3MB-polyglot-png

**Pack up to 3 MB of arbitrary data into a tweetable PNG polyglot file.**

[![CI](https://github.com/lucasrafaldini/3MB-polyglot-png/actions/workflows/ci.yml/badge.svg)](https://github.com/lucasrafaldini/3MB-polyglot-png/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-friendly-ff8ae2.svg)](https://hacktoberfest.com/)

</div>

## What is this?

`3MB-polyglot-png` hides a file inside a valid PNG image. The result is a
**polyglot**: it opens as a normal picture in any image viewer, yet still
contains your original file byte-for-byte. Services such as Twitter/X strip
metadata from PNG uploads but do **not** strip trailing data from the DEFLATE
stream inside the `IDAT` chunk — as long as the image meets the requirements to
avoid being re-encoded. That trailing region is where your payload lives.

In short: you can turn a `.zip`, `.pdf`, `.mp3` (and many other formats) into an
image to carry its content along.

> ⚠️ **Use responsibly.** This is an educational tool about file formats and
> steganography. See [SECURITY.md](SECURITY.md) for scope and the
> [Code of Conduct](CODE_OF_CONDUCT.md) for community expectations. Only embed
> and share content you have the right to distribute.

## How it works

A PNG's pixel data lives in one or more `IDAT` chunks, which together form a
single DEFLATE (zlib) stream. DEFLATE decoders stop at the end of the valid
stream, so any bytes appended afterwards are ignored by image renderers but
remain intact in the file. This tool:

1. Reads the cover PNG and drops non-essential chunks (metadata, etc.).
2. Concatenates all `IDAT` bodies into one.
3. Appends your payload to that `IDAT` body and re-emits it as a single,
   CRC-correct `IDAT` chunk, followed by `IEND`.
4. For `.zip` payloads, rewrites the archive's central-directory offsets so the
   output is *also* a valid ZIP archive.

Extraction reverses step 3 by decompressing the `IDAT` stream and reading the
decoder's trailing `unused_data`.

## Installation

```bash
# From a clone
git clone https://github.com/lucasrafaldini/3MB-polyglot-png.git
cd 3MB-polyglot-png
pip install .

# Or, for development (editable install + dev tools)
pip install -e ".[dev]"
```

The tool has **no runtime dependencies** — only the Python standard library.

## Usage

### Command line

```bash
# Hide a file inside a cover image
polyglot-png pack cover.png secret.zip output.png

# Get it back out
polyglot-png unpack output.png recovered.zip --fix-zip

# Helpful flags
polyglot-png --verbose pack cover.png secret.pdf out.png
polyglot-png pack cover.png big.bin out.png --no-fix-zip
```

You can also run it without installing:

```bash
python -m polyglot_png pack cover.png secret.zip output.png
```

The legacy entry point still works for existing scripts:

```bash
python pack.py cover.png secret.zip output.png
```

### As a library

```python
from polyglot_png import pack, unpack

result = pack("cover.png", "secret.zip", "output.png")
print(result.payload_offset, result.total_size)

unpack("output.png", "recovered.zip", fix_zip=True)
```

## Cover image requirements

- The cover must compress well enough that the compressed `IDAT` plus your
  payload fit within the image's pixel budget (`width * height` bytes).
- If the image has no palette, it should have at least 257 unique colours,
  otherwise Twitter/X may optimise it to a palette and break the polyglot.
- Resolution can be up to 4096×4096. Images larger than ~680×680 are served
  downscaled by default (depending on display DPI), but the original is still
  downloadable.
- Strip unnecessary metadata chunks. These GIMP export settings work well:

![GIMP PNG export settings](https://user-images.githubusercontent.com/13520633/111412860-1990ad00-86d5-11eb-9c2f-3a88db84fdf4.png)

## Embedded file requirements

- Total output must be under ~3 MB (maybe up to 5 MB), otherwise Twitter/X may
  convert the PNG to JPEG and destroy the payload. The CLI warns you when the
  output exceeds the limit.
- `.zip` payloads are handled automatically so the output stays a valid archive.
- Many other formats (notably `.pdf` and `.mp3`) work with no special handling.

## Development

```bash
pip install -e ".[dev]"
pytest          # run the test suite
ruff check .    # lint
```

## Contributing & Hacktoberfest

Contributions are very welcome, and this project is **Hacktoberfest-friendly**!
See [CONTRIBUTING.md](CONTRIBUTING.md) to get started and browse the
[open issues](https://github.com/lucasrafaldini/3MB-polyglot-png/issues) —
several are labelled `good first issue` and `hacktoberfest`.

## License

Released under the [MIT License](LICENSE). © 2021–2026 Lucas Rafaldini.
