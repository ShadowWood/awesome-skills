<!--
PR title format: feat(<category>): add <skill-name>
One PR per skill. Use `Closes #<issue-number>` to auto-close the originating issue.
-->

## Summary

- Skill: `<category>/<skill-name>`
- Closes #

Briefly describe the skill and any non-obvious design choices.

## Checklist

- [ ] Skill lives under `categories/<category>/<skill-name>/`
- [ ] `SKILL.md` has valid frontmatter (`name`, `description`) and is ≤ 500 lines
- [ ] `README.md` explains install, env vars, and how to run tests
- [ ] Every script in `scripts/` has a matching test in `tests/`
- [ ] Tests cover at least one happy path **and** one failure path per script
- [ ] No tests rely on the public internet or real credentials
- [ ] `requirements.txt` (Python) **or** `package.json` (Node/TS) is present and correct
- [ ] `python scripts/validate-skill.py categories/<category>/<skill-name>` passes locally
- [ ] `pytest -q` (or `npm test`) passes locally

## Security notes

- [ ] No secrets, API keys, or tokens are committed
- [ ] All external API calls are documented in `README.md`
