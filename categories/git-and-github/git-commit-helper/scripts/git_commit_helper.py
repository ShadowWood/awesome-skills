#!/usr/bin/env python3
"""
git-commit-helper — analyze staged git changes and propose a
Conventional Commits–style commit message.

Usage:
    python scripts/git_commit_helper.py [--llm] [--breaking] [--diff DIFF_FILE]

Output (stdout, exit 0):
    {
        "type": "feat|fix|docs|refactor|test|chore|...",
        "scope": "component-name",
        "subject": "short imperative description",
        "breaking": false,
        "body": "",
        "raw_diff": "full diff text"
    }

On error (stderr, exit non-zero):
    Error: <human-readable message>
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git subprocess and return stdout (decoded, stripped)."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return result.stdout
    except FileNotFoundError:
        print("Error: 'git' is not available on PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(
            f"Error: git command failed: git {' '.join(args)}\n"
            f"  {exc.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)


def truncate_diff(diff_text: str, max_bytes: int = 4096) -> str:
    """Truncate *per-file* sections to *max_bytes* characters."""
    sections = re.split(r"(?=diff --git )", diff_text)
    truncated = []
    for sec in sections:
        if not sec.strip():
            continue
        if len(sec) > max_bytes:
            sec = sec[:max_bytes] + "\n# … truncated …"
        truncated.append(sec)
    return "".join(truncated)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_git_repository(cwd: str | None = None) -> None:
    """Exit if cwd is not inside a git repository."""
    try:
        run_git(["rev-parse", "--git-dir"], cwd=cwd)
    except SystemExit:
        print("Error: not inside a Git repository.", file=sys.stderr)
        sys.exit(1)


def get_staged_diff(cwd: str | None = None) -> str:
    """Return the full staged diff, or '' if nothing is staged."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def get_staged_stat(cwd: str | None = None) -> str:
    """Return git diff --cached --stat output."""
    return run_git(["diff", "--cached", "--stat"], cwd=cwd)


def get_unstaged_modified(cwd: str | None = None) -> set[str]:
    """Return set of file paths with unstaged modifications."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return set(result.stdout.strip().splitlines())
    except subprocess.CalledProcessError:
        return set()


def get_staged_files(cwd: str | None = None) -> set[str]:
    """Return set of file paths that are currently staged."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return set(result.stdout.strip().splitlines())
    except subprocess.CalledProcessError:
        return set()


def check_dirty_working_tree(cwd: str | None = None) -> None:
    """Refuse if the working tree has unstaged changes in the same staged paths."""
    unstaged = get_unstaged_modified(cwd=cwd)
    staged = get_staged_files(cwd=cwd)
    overlap = unstaged & staged
    if overlap:
        paths = ", ".join(sorted(overlap))
        print(
            f"Error: working tree has unstaged modifications in staged file(s): {paths}\n"
            f"  Commit or stash those changes first, or use 'git add' to stage them.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

# Mapping of file-path patterns to conventional commit types.
# More specific prefixes take priority.
PATH_TYPE_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^tests/|test_.*\.py$|.*_test\.py$|.*\.spec\.\w+$"), "test"),
    (re.compile(r"^docs/|\.md$|\.rst$|CHANGELOG|README"), "docs"),
    (re.compile(r"^\.github/|^ci/|\.circleci/"), "ci"),
    (re.compile(r"^scripts/|^Makefile|^setup\.\w+"), "chore"),
    (re.compile(r"^requirements|^Pipfile|^pyproject\.toml"), "chore"),
    (re.compile(r"^package\.json|^package-lock|^yarn\.lock"), "chore"),
    (re.compile(r"^Dockerfile|^docker-compose|\.dockerignore"), "build"),
    (re.compile(r"\.css$|\.scss$|\.less$"), "style"),
    (re.compile(r"\.py$|\.js$|\.ts$|\.tsx$|\.jsx$|\.go$|\.rs$|\.java$"), None),
    # catch-all for source-like files
]


def infer_type_from_paths(files: list[str], diff_text: str = "") -> str:
    """Return a conventional commit type based on changed file paths and diff.

    Uses file paths first; if ambiguous (e.g. generic .py files), falls back
    to diff content analysis.
    """
    types_seen: list[str] = []
    for f in files:
        for pattern, ptype in PATH_TYPE_RULES:
            if pattern.search(f):
                if ptype is not None:
                    types_seen.append(ptype)
                break

    # Priority: feat > fix > test > docs > refactor > chore > …
    priority = ["feat", "fix", "test", "docs", "refactor", "chore", "ci", "build", "style"]
    for p in priority:
        if p in types_seen:
            return p

    # No type found from paths — fall back to diff content analysis.
    added_funcs = re.findall(
        r"^\+\s*(?:def |class |function |export (?:default )?(?:function|class) |const \w+ =)",
        diff_text,
        re.MULTILINE,
    )
    removed_count = len(re.findall(r"^-\s*", diff_text, re.MULTILINE))
    added_count = len(re.findall(r"^\+\s*", diff_text, re.MULTILINE))

    if added_funcs:
        return "feat"
    if added_count > 0 and removed_count > 0:
        return "refactor"
    if added_count > 0:
        return "feat"

    return "chore"


def infer_scope(files: list[str]) -> str:
    """Infer a scope name from the file paths changed."""
    # Try to extract the top-level package/directory name.
    parts_list = [f.split("/") for f in files if "/" in f]
    if parts_list:
        # Use the most common first segment as scope
        top_levels = [p[0] for p in parts_list]
        from collections import Counter
        most_common = Counter(top_levels).most_common(1)[0][0]
        return most_common.lower()
    # Single file — use the filename without extension
    if len(files) == 1:
        name = os.path.splitext(os.path.basename(files[0]))[0]
        return name.lower()
    return ""  # No scope


def infer_subject(diff_text: str, files: list[str], commit_type: str) -> str:
    """Generate a short imperative subject line from the diff and files."""
    # Try to extract meaningful context from additions
    added_funcs = re.findall(r"^\+\s*(?:def |class |function |export (?:default )?(?:function|class) )(\w+)", diff_text, re.MULTILINE)
    removed_funcs = re.findall(r"^-\s*(?:def |class |function |export (?:default )?(?:function|class) )(\w+)", diff_text, re.MULTILINE)

    if added_funcs and commit_type == "feat":
        return f"add {added_funcs[0]}"
    if removed_funcs:
        return f"remove {removed_funcs[0]}"
    if added_funcs:
        return f"add {added_funcs[0]}"

    # Look for FIXME/TODO patterns in the diff
    fix_refs = re.findall(r"\b(FIX|BUG|HACK|TODO|FIXME)\b", diff_text, re.IGNORECASE)
    if fix_refs:
        return "fix known issues"

    # Count lines added/removed
    added_lines = len(re.findall(r"^\+(?!\+\+)", diff_text, re.MULTILINE))
    removed_lines = len(re.findall(r"^-(?!--)", diff_text, re.MULTILINE))

    if commit_type == "feat":
        subject = "add new feature"
    elif commit_type == "fix":
        subject = "fix bug"
    elif commit_type == "test":
        subject = "add tests"
    elif commit_type == "docs":
        subject = "update documentation"
    elif commit_type == "refactor":
        subject = "refactor code"
    elif commit_type == "style":
        subject = "update styling"
    elif commit_type == "build":
        subject = "update build configuration"
    elif commit_type == "ci":
        subject = "update CI configuration"
    else:
        subject = "make minor changes"

    # Add some specificity based on file count or line counts
    if len(files) == 1:
        base = os.path.basename(files[0])
        name = os.path.splitext(base)[0]
        if added_lines > 0 and commit_type != "docs":
            subject = f"update {name}"
        else:
            subject = f"modify {name}"

    return subject


def detect_breaking_changes(diff_text: str) -> bool:
    """Return True if the diff contains a breaking change."""
    # Detect removed function/class/variable definitions (exported symbols)
    removed_defs = re.findall(
        r"^-\s*(?:export\s+)?(?:def |class |function |const |let |var |fn |pub )",
        diff_text,
        re.MULTILINE,
    )
    # Detect removed function signatures (for typed languages)
    removed_signatures = re.findall(
        r"^-\s*(?:pub\s+)?fn\s+\w+|^-\s*func\s+\w+|^-\s*def\s+\w+\(|^-\s*class\s+\w+",
        diff_text,
        re.MULTILINE,
    )
    # Detect API/endpoint removals
    removed_routes = re.findall(
        r"^-\s*(?:@app\.(?:route|get|post|put|delete)|router\.(?:get|post|put|delete)|app\.(?:get|post|put|delete))",
        diff_text,
        re.MULTILINE,
    )

    total_removed_defs = len(removed_defs) + len(removed_signatures) + len(removed_routes)
    return total_removed_defs > 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze staged git changes and propose a Conventional Commits commit message.",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use an LLM (OpenAI) to generate the commit body",
    )
    parser.add_argument(
        "--breaking",
        action="store_true",
        help="Force the commit to be marked as a breaking change",
    )
    parser.add_argument(
        "--diff",
        metavar="DIFF",
        default=None,
        help="Path to a diff file to analyze instead of git diff --cached",
    )
    return parser.parse_args(argv)


def load_diff_from_file(path: str) -> str:
    """Read a diff from an external file (for testing/debugging)."""
    if not os.path.isfile(path):
        print(f"Error: diff file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return f.read()


def call_llm(diff_text: str, commit_json: dict) -> str:
    """Use OpenAI to refine the commit body."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return ""  # No key available — use heuristic body

    # Short diff guard (avoid sending tiny content)
    if len(diff_text) < 20:
        return ""

    try:
        import httpx
    except ImportError:
        return ""  # httpx not installed — skip LLM

    prompt = textwrap.dedent(f"""\
    You are a git commit message generator. Given the diff below,
    produce a concise body paragraph (2-4 sentences) following
    Conventional Commits conventions.

    Already determined:
      type={commit_json["type"]}
      scope={commit_json["scope"]}
      subject={commit_json["subject"]}
      breaking={commit_json["breaking"]}

    Diff:
    ```
    {diff_text[:6000]}
    ```
    """)

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You generate Conventional Commits body paragraphs. Output only the body text, nothing else."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        body = data["choices"][0]["message"]["content"].strip()
        return body
    except Exception:
        return ""


def generate_commit_message(
    diff_stat: str,
    diff_text: str,
    cwd: str | None = None,
    use_llm: bool = False,
    force_breaking: bool = False,
) -> dict:
    """
    Generate a commit message dict from the staged diff.

    Args:
        diff_stat: git diff --cached --stat output (for file lists).
        diff_text: git diff --cached full output (truncated per file).
        cwd: working directory for git commands.
        use_llm: whether to try LLM body generation.
        force_breaking: if True, override heuristic detection and mark as breaking.

    Returns:
        dict with keys: type, scope, subject, breaking, body, raw_diff.
    """
    files = [line.split(None, 1)[0] for line in diff_stat.strip().splitlines()
             if line.strip() and "changed" not in line
             and not line.startswith(" ") and "|" in line]
    if not files:
        files = list(get_staged_files(cwd=cwd))
    if not files:
        # Fall back to parsing file paths from the diff text itself
        files = list(dict.fromkeys(
            re.findall(r"^diff --git a/(?:.*?) b/(.*)$", diff_text, re.MULTILINE)
        ))

    commit_type = infer_type_from_paths(files, diff_text=diff_text)
    scope = infer_scope(files)
    subject = infer_subject(diff_text, files, commit_type)
    breaking = force_breaking or detect_breaking_changes(diff_text)

    commit_json = {
        "type": commit_type,
        "scope": scope,
        "subject": subject,
        "breaking": breaking,
        "body": "",
        "raw_diff": diff_text,
    }

    if use_llm:
        body = call_llm(diff_text, commit_json)
        if body:
            commit_json["body"] = body

    return commit_json


def format_commit_message(commit: dict) -> str:
    """Format the commit dict into a Conventional Commits string."""
    scope_part = f"({commit['scope']})" if commit["scope"] else ""
    breaking_marker = "!" if commit["breaking"] else ""
    header = f"{commit['type']}{scope_part}{breaking_marker}: {commit['subject']}"
    parts = [header]

    if commit["breaking"]:
        parts.append("")
        parts.append("BREAKING CHANGE:")

    if commit["body"]:
        if not commit["breaking"]:
            parts.append("")
        parts.append(commit["body"])

    return "\n".join(parts)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.diff:
        diff_text = load_diff_from_file(args.diff)
        diff_stat = ""  # No stat when loading external diff
        cwd = None
        check_git_repository(cwd=cwd)
    else:
        cwd = os.getcwd()
        check_git_repository(cwd=cwd)

        diff_text = get_staged_diff(cwd=cwd)
        if not diff_text.strip():
            print("Error: no staged changes found. Use 'git add' to stage files first.", file=sys.stderr)
            sys.exit(1)

        check_dirty_working_tree(cwd=cwd)
        diff_stat = get_staged_stat(cwd=cwd)

    diff_text = truncate_diff(diff_text)

    commit = generate_commit_message(
        diff_stat=diff_stat,
        diff_text=diff_text,
        cwd=cwd,
        use_llm=args.llm,
        force_breaking=args.breaking,
    )

    print(json.dumps(commit, indent=2))


if __name__ == "__main__":
    main()
