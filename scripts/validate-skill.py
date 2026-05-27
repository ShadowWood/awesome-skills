#!/usr/bin/env python3
"""Validate that a skill directory follows the standards in CONTRIBUTING.md.

Checks performed:
  1. Required files exist (SKILL.md, README.md).
  2. SKILL.md has a valid YAML frontmatter with `name` and `description`.
     - `name` is kebab-case, ≤64 chars, matches the directory name.
     - `description` is ≤1024 chars and non-empty.
     - SKILL.md body is ≤500 lines.
  3. The skill sits under skills/<allowed-category>/<name>/.
  4. If scripts/ exists:
       - Each executable script has a matching test file in tests/.
       - Either requirements.txt (Python) or package.json (Node/TS) is present.
       - requirements.txt mentions pytest, or package.json defines `"test"`.

Usage:
  python scripts/validate-skill.py skills/<category>/<name>
  python scripts/validate-skill.py SKILL_TEMPLATE
  python scripts/validate-skill.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_CATEGORIES = {
    "git-and-github",
    "coding-and-ide",
    "browser-automation",
    "web-frontend",
    "devops-cloud",
    "productivity",
    "data-analytics",
    "pdf-documents",
    "communication",
    "search-research",
    "cli-utilities",
}

KEBAB_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

SCRIPT_TEST_MAP: dict[str, list[str]] = {
    ".py": ["tests/test_{stem}.py"],
    ".sh": ["tests/test_{stem}.bats", "tests/test_{stem}.py"],
    ".ts": ["tests/{stem}.test.ts", "tests/{stem}.test.js"],
    ".js": ["tests/{stem}.test.js"],
}


class ValidationError(Exception):
    """Raised when a skill fails validation."""


def parse_frontmatter(text: str) -> tuple[dict[str, str], int]:
    """Return (frontmatter dict, body line count)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValidationError("SKILL.md is missing a YAML frontmatter block")
    raw = match.group(1)
    data: dict[str, str] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line[0] not in (" ", "\t") and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value in (">", ">-", "|", "|-"):
                data[key] = ""
                current_key = key
            else:
                data[key] = value.strip("\"'")
                current_key = key
        elif current_key is not None and (line.startswith(" ") or line.startswith("\t")):
            data[current_key] = (data[current_key] + " " + line.strip()).strip()
    body = text[match.end():]
    return data, len(body.splitlines())


def check_skill_md(skill_dir: Path, expected_name: str | None) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValidationError("SKILL.md is missing")
    text = skill_md.read_text(encoding="utf-8")
    fm, body_lines = parse_frontmatter(text)

    name = fm.get("name", "").strip()
    description = fm.get("description", "").strip()

    if not name:
        raise ValidationError("SKILL.md frontmatter is missing `name`")
    if not KEBAB_RE.match(name):
        raise ValidationError(
            f"SKILL.md `name` must be kebab-case, ≤64 chars; got '{name}'"
        )
    if expected_name and name != expected_name:
        raise ValidationError(
            f"SKILL.md `name` ('{name}') does not match directory name ('{expected_name}')"
        )

    if not description:
        raise ValidationError("SKILL.md frontmatter is missing `description`")
    if len(description) > 1024:
        raise ValidationError(
            f"SKILL.md `description` is {len(description)} chars (max 1024)"
        )

    if body_lines > 500:
        raise ValidationError(
            f"SKILL.md body is {body_lines} lines (max 500). Move detail into reference.md."
        )


def check_required_files(skill_dir: Path) -> None:
    readme = skill_dir / "README.md"
    if not readme.exists():
        raise ValidationError("README.md is missing")


def find_executable_scripts(scripts_dir: Path) -> list[Path]:
    if not scripts_dir.is_dir():
        return []
    candidates: list[Path] = []
    for path in sorted(scripts_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"__init__.py", "conftest.py"}:
            continue
        if any(part.startswith(".") for part in path.relative_to(scripts_dir).parts):
            continue
        if path.suffix in SCRIPT_TEST_MAP:
            candidates.append(path)
    return candidates


def check_script_test_mapping(skill_dir: Path) -> None:
    scripts_dir = skill_dir / "scripts"
    tests_dir = skill_dir / "tests"
    scripts = find_executable_scripts(scripts_dir)
    if not scripts:
        return  # No scripts → tests are not required.

    if not tests_dir.is_dir():
        raise ValidationError(
            "scripts/ exists but tests/ directory is missing — every script needs tests"
        )

    missing: list[str] = []
    for script in scripts:
        rel = script.relative_to(scripts_dir).with_suffix("")
        stem = rel.as_posix().replace("/", "_")
        templates = SCRIPT_TEST_MAP[script.suffix]
        candidates = [skill_dir / tpl.format(stem=stem) for tpl in templates]
        if not any(candidate.exists() for candidate in candidates):
            expected = " | ".join(c.relative_to(skill_dir).as_posix() for c in candidates)
            missing.append(
                f"scripts/{script.relative_to(scripts_dir).as_posix()} → expected one of: {expected}"
            )
    if missing:
        raise ValidationError(
            "Each helper script must have a matching test file. Missing:\n  - "
            + "\n  - ".join(missing)
        )


def check_dependency_manifest(skill_dir: Path) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir() or not find_executable_scripts(scripts_dir):
        return

    req = skill_dir / "requirements.txt"
    pkg = skill_dir / "package.json"
    if not req.exists() and not pkg.exists():
        raise ValidationError(
            "scripts/ exists but neither requirements.txt nor package.json is present"
        )

    if req.exists():
        content = req.read_text(encoding="utf-8").lower()
        if "pytest" not in content:
            raise ValidationError(
                "requirements.txt must include pytest (used by the test suite)"
            )

    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"package.json is not valid JSON: {exc}") from exc
        if not data.get("scripts", {}).get("test"):
            raise ValidationError(
                "package.json must define a `scripts.test` entry"
            )


def check_location(skill_dir: Path) -> str | None:
    """Return the expected skill name based on directory layout, or None for templates."""
    skill_dir = skill_dir.resolve()
    try:
        rel = skill_dir.relative_to(REPO_ROOT)
    except ValueError:
        return None
    parts = rel.parts

    if parts[0] == "SKILL_TEMPLATE":
        return None  # Template lives outside skills/.
    if parts[0] != "skills":
        raise ValidationError(
            f"skill directory must live under skills/<category>/<name>, got {rel}"
        )
    if len(parts) != 3:
        raise ValidationError(
            f"expected skills/<category>/<name>, got {rel}"
        )
    category, name = parts[1], parts[2]
    if category not in ALLOWED_CATEGORIES:
        raise ValidationError(
            f"unknown category '{category}'. Allowed: {sorted(ALLOWED_CATEGORIES)}"
        )
    if not KEBAB_RE.match(name):
        raise ValidationError(f"skill directory name '{name}' must be kebab-case")
    return name


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []

    def run(check, *args):
        try:
            check(*args)
        except ValidationError as exc:
            errors.append(str(exc))

    expected_name: str | None = None
    try:
        expected_name = check_location(skill_dir)
    except ValidationError as exc:
        errors.append(str(exc))

    run(check_required_files, skill_dir)
    run(check_skill_md, skill_dir, expected_name)
    run(check_script_test_mapping, skill_dir)
    run(check_dependency_manifest, skill_dir)
    return errors


def iter_skill_dirs() -> list[Path]:
    paths: list[Path] = []
    skills_root = REPO_ROOT / "skills"
    if skills_root.exists():
        for category in sorted(skills_root.iterdir()):
            if not category.is_dir():
                continue
            for child in sorted(category.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    paths.append(child)
    template = REPO_ROOT / "SKILL_TEMPLATE"
    if template.exists():
        paths.append(template)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill_dir",
        nargs="?",
        type=Path,
        help="Path to the skill directory to validate.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate every skill in the repo (including SKILL_TEMPLATE).",
    )
    args = parser.parse_args(argv)

    if not args.all and args.skill_dir is None:
        parser.error("provide a skill_dir argument or --all")

    targets = iter_skill_dirs() if args.all else [args.skill_dir]
    overall_failed = False
    for target in targets:
        target = target.resolve()
        if not target.exists():
            print(f"FAIL  {target}: does not exist", file=sys.stderr)
            overall_failed = True
            continue
        errors = validate(target)
        rel = (
            target.relative_to(REPO_ROOT) if target.is_relative_to(REPO_ROOT) else target
        )
        if errors:
            overall_failed = True
            print(f"FAIL  {rel}")
            for err in errors:
                for line in err.splitlines():
                    print(f"      {line}")
        else:
            print(f"OK    {rel}")

    return 1 if overall_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
