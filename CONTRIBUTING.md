# Contributing a Skill

This document is the **single source of truth** for how a skill must be structured, scripted, tested, and documented before it can land in this repository. Agents reading an open issue: follow this end to end.

> TL;DR for agents
>
> 1. `./scripts/new-skill.sh <category> <skill-name>`
> 2. Edit `SKILL.md`, add scripts under `scripts/`, **add matching tests under `tests/`**.
> 3. `python ../../scripts/validate-skill.py .` and `pytest -q` (or `npm test`).
> 4. Open a PR with `Closes #<issue-number>`.

---

## 1. Directory layout

Every skill is a directory under `skills/<category>/<skill-name>/`. The required layout:

```
skills/<category>/<skill-name>/
├── SKILL.md              # REQUIRED — main agent-facing instructions
├── README.md             # REQUIRED — human-facing summary, install & usage
├── reference.md          # OPTIONAL — deep reference docs (progressive disclosure)
├── examples.md           # OPTIONAL — extended usage examples
├── scripts/              # OPTIONAL — helper executables
│   └── *.py | *.sh | *.ts | *.js
├── tests/                # REQUIRED IF scripts/ EXISTS
│   ├── __init__.py       # for Python skills
│   └── test_*.py | *.test.{js,ts} | test_*.bats
├── requirements.txt      # REQUIRED for Python skills (must include pytest)
└── package.json          # REQUIRED for Node/TS skills (must include test runner)
```

### Rules

- **`skill-name` must be kebab-case**, max 64 characters, matching the `name` field in `SKILL.md` frontmatter.
- **Pick exactly one runtime** per skill: Python *or* Node/TS. Do not mix `requirements.txt` and `package.json` in one skill unless the scripts genuinely require both (rare; document why in README).
- Pure-markdown skills (no `scripts/` directory) **may omit** `tests/`, `requirements.txt`, and `package.json`.

---

## 2. `SKILL.md` — the agent contract

`SKILL.md` is what cyhost actually loads at runtime. Keep it lean.

### Frontmatter (YAML)

```yaml
---
name: <kebab-case-slug>          # required, ≤64 chars, matches directory name
description: >-                  # required, ≤1024 chars
  <One sentence WHAT the skill does>. Use when <one sentence WHEN to trigger>.
---
```

### Body rules

- **Third person.** Write as if briefing a colleague about a tool. ✅ "Generates commit messages…" ❌ "I can generate commit messages…"
- **≤500 lines.** Move long reference material to `reference.md` and link to it.
- **Be specific in `description`.** Include trigger terms the user is likely to say. The agent uses this string to decide whether to load the skill.
- **Progressive disclosure.** SKILL.md is the lobby; deep content lives in sibling files (one level deep — do not nest `reference.md` inside subdirectories).

### Minimum required sections

```markdown
# <Skill Title>

## What it does
One paragraph.

## When to use
Bullets of trigger scenarios.

## How to use
Step-by-step instructions for the agent. Reference `scripts/*` here.

## Examples
At least one concrete input → output example.
```

See [SKILL_TEMPLATE/SKILL.md](SKILL_TEMPLATE/SKILL.md) for a working skeleton.

---

## 3. Helper scripts (`scripts/`)

### Language

- **Default to Python 3.10+**. Use Node/TS only if the ecosystem demands it (e.g. Playwright, web tooling).
- Shell scripts only for trivial glue (≤30 lines). Prefer Python for anything with branching logic.

### Required hygiene

- Shebang line: `#!/usr/bin/env python3` or `#!/usr/bin/env bash`.
- Set `set -euo pipefail` in every bash script.
- Use `argparse` (Python) or `commander` (Node) for arguments. Every script must respond to `--help`.
- Exit with non-zero status on error. Print actionable messages to stderr.
- Never hard-code secrets. Read them from env vars and document the names in `README.md`.

### File naming

- `snake_case` for Python files, `kebab-case` for shell scripts.
- One responsibility per script. If a script grows past ~300 lines, split it.

---

## 4. Tests (`tests/`) — **mandatory for any skill with `scripts/`**

This is a hard rule. CI will reject a PR whose `scripts/` directory contains an executable without a matching test.

### Mapping (enforced by `scripts/validate-skill.py`)

| Script                  | Required test file                                  |
| ----------------------- | --------------------------------------------------- |
| `scripts/foo.py`        | `tests/test_foo.py` (pytest)                        |
| `scripts/foo.sh`        | `tests/test_foo.bats` *or* `tests/test_foo.py`      |
| `scripts/foo.ts`        | `tests/foo.test.ts` (vitest or jest)                |
| `scripts/foo.js`        | `tests/foo.test.js`                                 |

### Minimum coverage per script

Each test file must contain **at least**:

1. **One happy-path test** asserting the script's primary success behavior.
2. **One failure-path test** asserting graceful handling of bad input, missing files, or upstream errors.

### Hard rules

- Tests **must not** hit the public internet. Mock HTTP (e.g. `responses`, `pytest-httpx`, `nock`) or use local fixtures.
- Tests **must not** require credentials. If a script wraps an external API, the test stubs the client.
- Tests **must** run with the project's default command from inside the skill directory:
  - Python: `pytest -q`
  - Node/TS: `npm test`
- Tests **must** be deterministic. Seed any randomness.

### Why we are strict

Skills run with real user credentials and shell access. An untested helper is a security and reliability liability. No tests, no merge.

---

## 5. Dependencies

### Python (`requirements.txt`)

- Pin a minimum version: `pytest>=8.0`.
- Include only direct dependencies. Avoid pulling massive frameworks if a small one will do.
- Always include the test runner (`pytest`) and any mocking library the tests need.

### Node/TS (`package.json`)

- Define `"scripts": { "test": "vitest run" }` (or `jest`).
- Pin testing-related devDependencies.
- Keep `"dependencies"` minimal; prefer Node's standard library where possible.

---

## 6. README.md (per skill)

Human-readable. Should answer:

1. What is this skill for?
2. How does someone install it?
3. Which environment variables / credentials does it need?
4. How do I run its tests?

Keep this under ~150 lines. Detailed docs belong in `reference.md`.

---

## 7. Local validation workflow

From the repo root:

```bash
# 1. Structural and frontmatter check (and script↔test mapping)
python scripts/validate-skill.py skills/<category>/<skill-name>

# 2. Run the skill's own tests
cd skills/<category>/<skill-name>
pytest -q          # for Python skills
# or
npm install && npm test   # for Node skills
```

CI runs both steps on every PR. A failure in either blocks the merge.

---

## 8. Pull request flow

1. **One PR per skill.** Do not bundle multiple skills.
2. PR title: `feat(<category>): add <skill-name>`.
3. PR body must include `Closes #<issue-number>` so the originating issue closes automatically.
4. Fill out [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) — it is the merge checklist.
5. CI must be green. No exceptions.
6. After merge, run `python scripts/list-skills.py --update-readme` (a maintainer will do this) so the root README reflects the new count.

---

## 9. Things we reject on sight

- Skills without tests when `scripts/` exists.
- Skills whose `description` is vague ("helps with stuff").
- Skills that hard-code API keys or secrets.
- Skills with test suites that require the network.
- Skills that duplicate functionality of an already-merged skill (improve the existing one instead).
- Skills with `SKILL.md` > 500 lines.

---

## 10. Need help?

Open a discussion or comment on the relevant issue. Ping a maintainer if a PR has been waiting on review for more than 7 days.
