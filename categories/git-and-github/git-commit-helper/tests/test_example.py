"""Tests for scripts/example.py.

Every helper script in `scripts/` must have a matching test module here that
exercises at least one happy path and one failure path. CI will fail otherwise.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "example.py"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_happy_path_counts_lines(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    result = run(["--input", str(sample)])

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {"status": "ok", "lines": 3}


def test_missing_file_exits_nonzero(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.txt"

    result = run(["--input", str(missing)])

    assert result.returncode == 1
    assert "input not found" in result.stderr


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_flag(flag: str) -> None:
    result = run([flag])
    assert result.returncode == 0
    assert "Count the lines" in result.stdout
