# Tests

Every executable in `../scripts/` **must** have a corresponding test module in this directory. The repo-level `validate-skill.py` enforces this mapping; CI runs the tests on every PR.

## Conventions

| Script type | Test file                       | Runner       |
| ----------- | ------------------------------- | ------------ |
| `*.py`      | `test_<name>.py`                | `pytest`     |
| `*.sh`      | `test_<name>.bats` or `test_<name>.py` (subprocess) | `bats` / `pytest` |
| `*.ts`      | `<name>.test.ts`                | `vitest`     |
| `*.js`      | `<name>.test.js`                | `vitest`/`jest` |

## Minimum coverage per script

1. One **happy path** test — primary success behavior.
2. One **failure path** test — bad input, missing file, upstream error.

## Hard rules

- No network. Mock all HTTP (`responses`, `pytest-httpx`, `nock`, ...).
- No real credentials. Stub external clients.
- Deterministic. Seed random sources.
- Runs with `pytest -q` (Python) or `npm test` (Node) from the skill root.
