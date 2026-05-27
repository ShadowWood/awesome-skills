# awesome-skills

A curated skill registry for the cyhost AI agent. Each skill lives under a category directory and provides structured metadata (SKILL.md), implementation scripts, and tests.

## Repository Structure

```
categories/
  <category>/
    <skill-name>/
      SKILL.md           # Required: skill manifest with YAML frontmatter
      README.md          # Required: human-readable install/usage/test instructions
      scripts/           # Implementation scripts (Python, shell, etc.)
      tests/             # Tests matching scripts/ one-to-one
      requirements.txt   # Python dependencies
      reference.md       # Optional: deep technical documentation
scripts/
  validate-skill.py      # Structural + frontmatter + script↔test mapping checker
```

## Standards

- Every script in `scripts/` must have a corresponding test in `tests/` with the same basename.
- Tests must cover at least one happy path and one failure path.
- Tests must not rely on the public internet or real credentials.
- SKILL.md must have valid YAML frontmatter (`name`, `description`).
- SKILL.md must be ≤ 500 lines.
- Use `python scripts/validate-skill.py categories/<category>/<skill-name>` to validate.
