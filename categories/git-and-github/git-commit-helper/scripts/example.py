#!/usr/bin/env python3
"""Example helper script for the skill template.

Reads a text file and reports basic statistics. Replace this with real logic.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def count_lines(path: Path) -> int:
    if not path.exists():
        raise FileNotFoundError(f"input not found: {path}")
    if not path.is_file():
        raise ValueError(f"not a regular file: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count the lines in a text file.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the text file to inspect.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        lines = count_lines(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "lines": lines}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
