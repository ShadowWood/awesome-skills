---
name: git-commit-helper
description: >-
  Analyzes staged git diffs and proposes a Conventional Commits–style commit
  message using local heuristics. Optionally uses an LLM (OpenAI) for more
  nuanced messages when the `--llm` flag is passed and `OPENAI_API_KEY` is set.
  The agent should trigger this skill when the user says "write a commit
  message", "commit this", "help me commit", or any time the agent is about to
  create a git commit and wants a well-formatted message.
---

## What it does

`git-commit-helper` inspects the current Git repository's staged changes
(`git diff --cached`), classifies them into a conventional commit type
(`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, etc.), infers a scope
from the changed file paths, generates a short subject line, and optionally
detects breaking changes (e.g., removed function or class definitions).

It outputs a JSON object on stdout with the structured commit proposal and
exits 0 on success. On failure (no staged changes, dirty working tree, or
missing `git`), it prints a human-readable error on stderr and exits non-zero.

When the `--llm` flag is provided and the `OPENAI_API_KEY` environment
variable is set, the helper also invokes an LLM to produce a more nuanced
body paragraph. Without the flag or the key, it uses purely local heuristics.

## When to use

- The user says **"write a commit message"**, **"commit this"**, or **"help me commit"**.
- The agent has just made changes and needs to craft a Conventional Commits–compliant message.
- The agent wants to detect whether staged changes include a breaking change automatically.
- The user explicitly requests a commit message for their staged changes.

## How to use

1. **Confirm prerequisites**:
   - Python 3.10+ is available on `PATH`.
   - `git` is available on `PATH` and the current working directory is inside a Git repository.
   - (Optional) `OPENAI_API_KEY` environment variable is set if using the `--llm` flag.

2. **Stage changes** (the user should have already run `git add`):
   ```bash
   git add <files>
   ```

3. **Run the helper**:
   ```bash
   python scripts/git_commit_helper.py
   ```

4. **Interpret the output**:
   - On success: a JSON object is printed to stdout with keys `type`, `scope`, `subject`, `breaking`, `body`, and `raw_diff`.
   - On failure: a human-readable error message is printed to stderr and the exit code is non-zero.

### Options

| Flag          | Description                                            |
|---------------|--------------------------------------------------------|
| `--help`, `-h` | Show usage information and exit.                      |
| `--llm`       | Use an LLM (OpenAI) to generate the commit body.      |
| `--diff`      | Path to a diff file to analyze (instead of `git diff --cached`). Useful for debugging or non-git contexts. |

## Examples

### Example 1: Happy path — staged feature addition

**Input (staged diff):**
```diff
diff --git a/src/auth.py b/src/auth.py
new file mode 100644
+def login(username, password):
+    """Authenticate a user."""
+    return {"token": "…"}
```

**Command:**
```bash
git add src/auth.py
python scripts/git_commit_helper.py
```

**Output:**
```json
{
  "type": "feat",
  "scope": "auth",
  "subject": "add login function",
  "breaking": false,
  "body": "",
  "raw_diff": "diff --git a/src/auth.py b/src/auth.py\nnew file mode 100644\n+def login(username, password):\n+    return {\"token\": \"…\"}"
}
```

### Example 2: No staged changes

**Command:**
```bash
python scripts/git_commit_helper.py
```

**Output (stderr):**
```
Error: no staged changes found. Use 'git add' to stage files first.
```

**Exit code:** 1

### Example 3: Breaking change detected

**Input (staged diff):**
```diff
diff --git a/src/utils.py b/src/utils.py
--- a/src/utils.py
+++ b/src/utils.py
-def legacy_helper():
-    pass
```

**Command:**
```bash
python scripts/git_commit_helper.py
```

**Output:**
```json
{
  "type": "refactor",
  "scope": "utils",
  "subject": "remove legacy_helper",
  "breaking": true,
  "body": "",
  "raw_diff": "diff --git a/src/utils.py b/src/utils.py\n--- a/src/utils.py\n+++ b/src/utils.py\n-def legacy_helper():\n-    pass"
}
```

### Example 4: Help flag

**Command:**
```bash
python scripts/git_commit_helper.py --help
```

**Output (stdout):**
```
usage: git_commit_helper.py [-h] [--llm] [--diff DIFF]

Analyze staged git changes and propose a Conventional Commits commit message.

options:
  -h, --help   show this help message and exit
  --llm        Use an LLM (OpenAI) to generate the commit body
  --diff DIFF  Path to a diff file to analyze instead of git diff --cached
```

**Exit code:** 0

## Configuration

| Env var           | Required | Purpose                                                |
|-------------------|----------|--------------------------------------------------------|
| `OPENAI_API_KEY`  | No       | Used only when the `--llm` flag is passed.             |

## Additional resources

- Deep reference: [reference.md](reference.md)
- Human-facing summary and install: [README.md](README.md)
