#!/usr/bin/env python3
"""List skills currently registered in the repository.

Outputs a markdown table grouped by category. With --update-readme, replaces
the auto-generated section inside the root README.md (delimited by HTML
comments).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATEGORIES_ROOT = REPO_ROOT / "categories"
README = REPO_ROOT / "README.md"

CATEGORY_LABELS = {
    "git-and-github": "Git & GitHub",
    "coding-and-ide": "Coding & IDE",
    "browser-automation": "Browser & Automation",
    "web-frontend": "Web & Frontend",
    "devops-cloud": "DevOps & Cloud",
    "productivity": "Productivity",
    "data-analytics": "Data & Analytics",
    "pdf-documents": "PDF & Documents",
    "communication": "Communication",
    "search-research": "Search & Research",
    "cli-utilities": "CLI Utilities",
}

START_MARK = "<!-- skills:auto:start -->"
END_MARK = "<!-- skills:auto:end -->"


def collect() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {cat: [] for cat in CATEGORY_LABELS}
    if not CATEGORIES_ROOT.exists():
        return result
    for category_dir in sorted(CATEGORIES_ROOT.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        cat = category_dir.name
        if cat not in result:
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            if (skill_dir / "SKILL.md").exists():
                result[cat].append(skill_dir.name)
    return result


def render_table(data: dict[str, list[str]]) -> str:
    rows = ["| Category | Skills | Count |", "| --- | --- | ---: |"]
    for cat, label in CATEGORY_LABELS.items():
        skills = data.get(cat, [])
        names = ", ".join(f"`{n}`" for n in skills) if skills else "_none yet_"
        link = f"[{label}](categories/{cat}/)"
        rows.append(f"| {link} | {names} | {len(skills)} |")
    return "\n".join(rows)


def update_readme(table: str) -> bool:
    if not README.exists():
        print(f"error: {README} not found", file=sys.stderr)
        return False
    text = README.read_text(encoding="utf-8")
    block = f"{START_MARK}\n{table}\n{END_MARK}"
    if START_MARK in text and END_MARK in text:
        pattern = re.compile(
            re.escape(START_MARK) + r".*?" + re.escape(END_MARK),
            re.DOTALL,
        )
        new_text = pattern.sub(block, text, count=1)
    else:
        new_text = text.rstrip() + "\n\n## Skill index (auto-generated)\n\n" + block + "\n"
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-readme",
        action="store_true",
        help="Replace the auto-generated skill table inside the root README.md.",
    )
    args = parser.parse_args(argv)

    data = collect()
    table = render_table(data)
    if args.update_readme:
        changed = update_readme(table)
        print("README updated" if changed else "README already up to date")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
