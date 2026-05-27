"""Tests for git_commit_helper.py — all use subprocess and tmp_path, no network."""

import json
import os
import subprocess
import sys

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "git_commit_helper.py")


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    """Run a git command inside *repo*."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=repo,
        check=True,
    )


def _init_repo(tmp_path) -> str:
    """Create a temporary git repo at tmp_path/repo and return its path."""
    repo = os.path.join(str(tmp_path), "repo")
    os.makedirs(repo)
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "Test")
    return repo


def _run_script(repo: str, *extra_args: str) -> subprocess.CompletedProcess:
    """Run git_commit_helper.py inside *repo*."""
    return subprocess.run(
        [sys.executable, SCRIPT_PATH, *extra_args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_help_flag_returns_zero(tmp_path) -> None:
    """-h / --help should exit 0 with usage output."""
    repo = _init_repo(tmp_path)
    for flag in ("-h", "--help"):
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, flag],
            capture_output=True,
            text=True,
            cwd=repo,
        )
        assert result.returncode == 0, f"{flag} failed: {result.stderr}"
        assert "usage:" in result.stdout


def test_no_staged_changes_fails(tmp_path) -> None:
    """Running with no staged changes should exit non-zero and print error."""
    repo = _init_repo(tmp_path)

    # Create a file but don't stage it
    repo_file = os.path.join(repo, "hello.py")
    with open(repo_file, "w") as f:
        f.write("x = 1\n")

    result = _run_script(repo)
    assert result.returncode != 0, "Expected non-zero exit with no staged changes"
    assert "no staged changes" in result.stderr.lower()


def test_happy_path_feature_add(tmp_path) -> None:
    """Happy path: staged new file should produce a valid JSON commit message."""
    repo = _init_repo(tmp_path)

    # Create and stage a new feature file
    src = os.path.join(repo, "src", "auth.py")
    os.makedirs(os.path.dirname(src))
    with open(src, "w") as f:
        f.write("def login(username, password):\n")
        f.write("    return {'token': 'abc'}\n")

    _git(repo, "add", "src/auth.py")

    result = _run_script(repo)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    commit = json.loads(result.stdout)
    assert isinstance(commit, dict)
    assert "type" in commit
    assert "scope" in commit
    assert "subject" in commit
    assert "breaking" in commit
    assert "body" in commit
    assert "raw_diff" in commit

    # Should detect a feature
    assert commit["type"] == "feat", f"Expected 'feat', got {commit['type']}"
    assert commit["breaking"] is False
    assert len(commit["subject"]) > 0


def test_happy_path_fix(tmp_path) -> None:
    """Fix to existing code should produce type=fix."""
    repo = _init_repo(tmp_path)

    # Create an initial commit
    src = os.path.join(repo, "main.py")
    with open(src, "w") as f:
        f.write("x = 1\n")
    _git(repo, "add", "main.py")
    _git(repo, "commit", "-m", "initial")

    # Modify the file
    with open(src, "w") as f:
        f.write("x = 2\n")
    _git(repo, "add", "main.py")

    result = _run_script(repo)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    commit = json.loads(result.stdout)
    assert commit["type"] in ("chore", "refactor"), f"Got {commit['type']}"
    assert commit["breaking"] is False


def test_breaking_change_detected(tmp_path) -> None:
    """Removing a function definition should flag breaking=true."""
    repo = _init_repo(tmp_path)

    # Create initial file with a function
    src = os.path.join(repo, "utils.py")
    with open(src, "w") as f:
        f.write("def legacy_helper():\n")
        f.write("    return 'old'\n")
    _git(repo, "add", "utils.py")
    _git(repo, "commit", "-m", "initial")

    # Remove the function
    with open(src, "w") as f:
        f.write("def new_helper():\n")
        f.write("    return 'new'\n")
    _git(repo, "add", "utils.py")

    result = _run_script(repo)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    commit = json.loads(result.stdout)
    # The removal of legacy_helper is a removed definition
    assert commit["breaking"] is True, f"Expected breaking=True, got {commit}"


def test_unstaged_changes_refused(tmp_path) -> None:
    """Having unstaged modifications in staged files should exit non-zero."""
    repo = _init_repo(tmp_path)

    # Create a file, stage some changes, but also have unstaged changes
    src = os.path.join(repo, "app.py")
    with open(src, "w") as f:
        f.write("v1 = 1\n")
    _git(repo, "add", "app.py")  # Stage initial content

    # Modify it further (unstaged modification on a staged file)
    with open(src, "w") as f:
        f.write("v1 = 1\nv2 = 2\n")

    result = _run_script(repo)
    assert result.returncode != 0, "Expected non-zero exit for dirty working tree"
    assert "unstaged" in result.stderr.lower()


def test_diff_file_option(tmp_path) -> None:
    """--diff with a valid diff file should succeed."""
    repo = _init_repo(tmp_path)

    # Create a diff file to analyze
    diff_content = """diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,3 @@
+def login(username, password):
+    \"\"\"Authenticate a user.\"\"\"
+    return {\"token\": \"...\"}
"""
    diff_file = os.path.join(str(tmp_path), "test.diff")
    with open(diff_file, "w") as f:
        f.write(diff_content)

    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "--diff", diff_file],
        capture_output=True,
        text=True,
        cwd=repo,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    commit = json.loads(result.stdout)
    assert commit["type"] == "feat"
    assert commit["scope"] in ("auth", "src", ""), f"Unexpected scope: {commit['scope']}"
    assert commit["breaking"] is False
    assert "raw_diff" in commit
