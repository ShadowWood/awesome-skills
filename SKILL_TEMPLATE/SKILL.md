---
name: skill-template
description: >-
  Replace this with one sentence describing WHAT the skill does, then one
  sentence describing WHEN the agent should trigger it. Include concrete
  trigger terms users will say.
---

# Skill Template

> Delete this blockquote when you fork. It is a checklist for the author.
>
> - [ ] Rename the directory to your skill's kebab-case name.
> - [ ] Update `name` and `description` in frontmatter (description ≤1024 chars).
> - [ ] Fill every section below.
> - [ ] Replace `scripts/example.py` with your real helper(s).
> - [ ] Replace `tests/test_example.py` with real happy-path + failure-path tests.
> - [ ] Update `requirements.txt` (or switch to `package.json`).
> - [ ] Update the per-skill `README.md`.
> - [ ] Run `python ../../scripts/validate-skill.py .` and `pytest -q`.

## What it does

One paragraph. Be specific. Avoid marketing language.

## When to use

Concrete trigger scenarios:

- When the user says "<example phrase>".
- When the agent is asked to <specific task>.
- When working with files matching `<pattern>`.

## How to use

Step-by-step instructions written for the agent.

1. Confirm prerequisites:
   - Python 3.10+
   - Environment variables: `EXAMPLE_API_KEY`
2. Run the main helper:
   ```bash
   python scripts/example.py --input <path>
   ```
3. Interpret the output (JSON on stdout, non-zero exit on failure).

## Examples

### Example 1: Happy path

**Input:**
```
example input
```

**Command:**
```bash
python scripts/example.py --input example.txt
```

**Output:**
```json
{"status": "ok", "lines": 3}
```

## Configuration

| Env var           | Required | Purpose                          |
| ----------------- | -------- | -------------------------------- |
| `EXAMPLE_API_KEY` | No       | Used only when `--remote` is set |

## Additional resources

- Deep reference: [reference.md](reference.md)
- Human-facing summary and install: [README.md](README.md)
