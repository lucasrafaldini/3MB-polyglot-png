"""Tests for the command-line interface."""

from __future__ import annotations

import pytest

from polyglot_png.cli import main

from .conftest import make_png


@pytest.fixture
def cover(tmp_path):
    path = tmp_path / "cover.png"
    path.write_bytes(make_png())
    return path


def test_cli_pack_and_unpack_round_trip(cover, tmp_path, capsys):
    secret = tmp_path / "secret.bin"
    secret.write_bytes(b"cli payload")
    out = tmp_path / "out.png"
    extracted = tmp_path / "extracted.bin"

    assert main(["pack", str(cover), str(secret), str(out)]) == 0
    assert main(["unpack", str(out), str(extracted)]) == 0

    assert extracted.read_bytes() == b"cli payload"
    captured = capsys.readouterr()
    assert "Packed" in captured.out
    assert "Extracted" in captured.out


def test_cli_reports_error_for_missing_file(tmp_path, capsys):
    out = tmp_path / "out.png"
    code = main(["pack", str(tmp_path / "nope.png"), str(tmp_path / "nope.bin"), str(out)])
    assert code == 1
    assert "error:" in capsys.readouterr().err
