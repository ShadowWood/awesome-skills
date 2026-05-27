# Categories

Every accepted skill lives under `categories/<category-slug>/<skill-name>/`. This file is the canonical taxonomy. Adding a new category requires a PR that updates this file, the root [README.md](../README.md), and the validator's allow-list in [scripts/validate-skill.py](../scripts/validate-skill.py).

## Taxonomy

| Slug                  | Description                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------- |
| `git-and-github`      | Local git workflows, GitHub API automation, PR/issue/release handling.                       |
| `coding-and-ide`      | Code generation, refactoring, testing, docstrings, dependency upkeep.                        |
| `browser-automation`  | Headless browser control, web scraping, screenshotting.                                      |
| `web-frontend`        | Frontend scaffolding, component/API client generation, responsive checks.                    |
| `devops-cloud`        | Docker, deployments, cloud-resource management, log analysis.                                |
| `productivity`        | Personal task/standup/meeting tooling that does not fit a more specific bucket.              |
| `data-analytics`      | Tabular data wrangling, SQL building, basic analytics.                                       |
| `pdf-documents`       | PDF/Office extraction and conversion.                                                        |
| `communication`       | Email, IM (Slack, etc.), notifications.                                                      |
| `search-research`     | Web search, academic search, reference gathering.                                            |
| `cli-utilities`       | Shell command helpers and OS-level glue that doesn't fit elsewhere.                          |

## Naming rules

- Category slugs are lowercase, hyphen-separated, ASCII.
- Skill slugs follow the same rule and must be unique across the entire `categories/` tree.

## Adding to a category

```bash
./scripts/new-skill.sh <category-slug> <skill-name>
```

The scaffold script refuses unknown category slugs. After implementing the skill, run `python scripts/list-skills.py --update-readme` to refresh the per-category counts in the root README.
