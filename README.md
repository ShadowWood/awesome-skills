<div align="center">

# Awesome cyhost Skills

**A curated, opinionated collection of skills for [cyhost](https://github.com/cysic-labs) — the OpenClaw-based local AI agent from Cysic.**

</div>

---

## What is this?

`cyhost` is a locally-running AI agent built on top of the OpenClaw runtime. **Skills** extend its capabilities so it can drive Git, browsers, IDEs, cloud services, productivity tools, and more — all from natural-language instructions.

This repository is **not** a dump of every skill anyone ever wrote. It is:

1. A **standards document** describing exactly how a skill must be structured, scripted, tested, and documented to ship here.
2. A **task registry** (GitHub Issues) where each open issue corresponds to one skill we want built.
3. The **canonical home** for skills accepted into the cyhost ecosystem.

Agents (and humans) read the open issues, implement the requested skill in this repo following the standards, and open a PR.

## Quick start

### For users who want to install a skill

Copy the skill folder into one of these locations:

| Scope     | Path                         |
| --------- | ---------------------------- |
| Global    | `~/.openclaw/skills/`        |
| Workspace | `<your-project>/skills/`     |

Priority on lookup: **Workspace > Global**.

### For agents/humans who want to contribute a skill

1. Pick an open issue tagged `skill` from this repo.
2. Read [CONTRIBUTING.md](CONTRIBUTING.md) end to end. It is the source of truth.
3. Scaffold:
   ```bash
   ./scripts/new-skill.sh <category> <skill-name>
   ```
4. Implement the skill, write tests, validate locally:
   ```bash
   python scripts/validate-skill.py skills/<category>/<skill-name>
   cd skills/<category>/<skill-name> && pytest -q   # or npm test
   ```
5. Open a PR that closes the corresponding issue.

## Repository layout

```
awesome-skills/
├── README.md                 # You are here
├── CONTRIBUTING.md           # Skill standards (REQUIRED reading)
├── LICENSE                   # MIT
├── .gitignore
├── SKILL_TEMPLATE/           # Scaffold for new skills
├── skills/                   # All accepted skills, grouped by category
├── categories/               # Per-category indexes
├── scripts/                  # Repo-level tooling (validate, scaffold, index)
└── .github/                  # Issue & PR templates, CI
```

## Categories

Initial taxonomy (counts will fill in as skills land):

| Category                                       | Skills |
| ---------------------------------------------- | -----: |
| [Git & GitHub](skills/git-and-github/)         |      0 |
| [Coding & IDE](skills/coding-and-ide/)         |      0 |
| [Browser & Automation](skills/browser-automation/) | 0 |
| [Web & Frontend](skills/web-frontend/)         |      0 |
| [DevOps & Cloud](skills/devops-cloud/)         |      0 |
| [Productivity](skills/productivity/)           |      0 |
| [Data & Analytics](skills/data-analytics/)     |      0 |
| [PDF & Documents](skills/pdf-documents/)       |      0 |
| [Communication](skills/communication/)         |      0 |
| [Search & Research](skills/search-research/)   |      0 |
| [CLI Utilities](skills/cli-utilities/)         |      0 |

Run `python scripts/list-skills.py --update-readme` to refresh these counts after a new skill is merged.

## Security notice

Skills can execute shell commands, talk to external APIs, and read local files. Every skill in this repo:

- Must include tests for any helper script (see [CONTRIBUTING.md](CONTRIBUTING.md)).
- Must declare its external dependencies in `requirements.txt` or `package.json`.
- Is reviewed via PR before being merged.

That said, **review any skill before you run it on real data or credentials**. Never expose secrets to a skill you have not audited.

## License

[MIT](LICENSE).

## Acknowledgements

Structure and several conventions are inspired by [VoltAgent/awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills) and the [Claude Code / Cursor skill format](https://docs.cursor.com/).
