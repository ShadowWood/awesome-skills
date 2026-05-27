# git-commit-helper

Analyzes staged git changes and proposes a Conventional Commits–style commit message using local heuristics. Optionally integrates with an LLM (OpenAI) for more nuanced body text when the `--llm` flag is passed.

## What this skill does

When invoked inside a Git repository with staged changes, `git-commit-helper` inspects `git diff --cached`, classifies the diff into a conventional commit type (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, etc.), infers a scope from the changed file paths, generates a short subject line, and detects breaking changes. It outputs a JSON object on stdout and exits 0 on success.

## Install

```bash
# Clone or navigate to the awesome-skills repository
cd awesome-skills

# Install Python dependencies
pip install -r categories/git-and-github/git-commit-helper/requirements.txt
```

The skill is available to Claude Code agents as part of the `awesome-skills` collection.

## Environment

| Env var           | Required | Purpose                                                    |
| ----------------- | -------- | ---------------------------------------------------------- |
| `OPENAI_API_KEY`  | No       | Only required when using the `--llm` flag for LLM-powered body generation. |

## Usage

```bash
# Stage your changes first
git add <files>

# Run the helper
python scripts/git_commit_helper.py

# With LLM body generation
OPENAI_API_KEY=sk-... python scripts/git_commit_helper.py --llm

# Analyze an external diff file (for testing)
python scripts/git_commit_helper.py --diff /path/to/diff.diff
```

## Output

On success, the script prints a JSON object to stdout:

```json
{
  "type": "feat",
  "scope": "auth",
  "subject": "add login function",
  "breaking": false,
  "body": "",
  "raw_diff": "diff --git a/src/auth.py b/src/auth.py\n..."
}
```

On failure, a human-readable error is printed to stderr and exit code is non-zero.

## Run the tests

```bash
cd categories/git-and-github/git-commit-helper
pip install -r requirements.txt
pytest -q
```

## How it works

The helper uses several heuristics to generate commit messages:

1. **Type inference**: File paths are mapped to conventional commit types (e.g. `tests/` → `test`, `docs/` → `docs`). For generic source files, the diff content is analyzed for added function/class definitions to determine whether the change is a `feat` or `refactor`.
2. **Scope inference**: Extracted from the top-level directory of changed files.
3. **Subject generation**: Extracts function names from additions/removals, or falls back to a descriptive message based on the commit type.
4. **Breaking change detection**: Scans for removed function/class/variable definitions and API route removals.
5. **Working tree safety**: Refuses to operate if unstaged modifications exist in the same files as staged changes — preventing partial commits from producing misleading messages.

## Limits

- Per-file diffs are truncated to ~4 KB to keep heuristic analysis manageable.
- The `--llm` feature requires `httpx` (install separately if needed) and a valid `OPENAI_API_KEY`.

## License

Inherits the repo-level [MIT license](../../../LICENSE).
