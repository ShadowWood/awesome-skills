#!/usr/bin/env bash
# Scaffold a new skill from SKILL_TEMPLATE/.
# Usage: ./scripts/new-skill.sh <category> <skill-name>

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

ALLOWED_CATEGORIES=(
  git-and-github
  coding-and-ide
  browser-automation
  web-frontend
  devops-cloud
  productivity
  data-analytics
  pdf-documents
  communication
  search-research
  cli-utilities
)

usage() {
  cat <<EOF
Usage: $0 <category> <skill-name>

Categories:
  ${ALLOWED_CATEGORIES[*]}

Example:
  $0 git-and-github git-commit-helper
EOF
}

if [[ $# -ne 2 ]]; then
  usage >&2
  exit 64
fi

category="$1"
skill_name="$2"

# Validate category.
ok=0
for c in "${ALLOWED_CATEGORIES[@]}"; do
  if [[ "$c" == "$category" ]]; then
    ok=1
    break
  fi
done
if [[ $ok -eq 0 ]]; then
  echo "error: unknown category '$category'" >&2
  echo "       allowed: ${ALLOWED_CATEGORIES[*]}" >&2
  exit 65
fi

# Validate skill name (kebab-case, ≤64 chars).
if [[ ! "$skill_name" =~ ^[a-z][a-z0-9-]{0,63}$ ]]; then
  echo "error: skill name must be lowercase kebab-case, ≤64 chars, start with a letter" >&2
  exit 65
fi

dest="${REPO_ROOT}/categories/${category}/${skill_name}"
if [[ -e "$dest" ]]; then
  echo "error: ${dest} already exists" >&2
  exit 66
fi

template="${REPO_ROOT}/SKILL_TEMPLATE"
if [[ ! -d "$template" ]]; then
  echo "error: template not found at ${template}" >&2
  exit 70
fi

mkdir -p "$dest"
# Copy template contents (including dotfiles) without copying the directory itself.
# shellcheck disable=SC2046
cp -R "$template"/. "$dest"/

# Patch SKILL.md frontmatter `name:` line.
skill_md="${dest}/SKILL.md"
if [[ -f "$skill_md" ]]; then
  python3 - "$skill_md" "$skill_name" <<'PY'
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
slug = sys.argv[2]
text = path.read_text(encoding="utf-8")
text = re.sub(r"^name: .*$", f"name: {slug}", text, count=1, flags=re.MULTILINE)
path.write_text(text, encoding="utf-8")
PY
fi

# Patch package.json name if the user keeps it.
pkg="${dest}/package.json"
if [[ -f "$pkg" ]]; then
  python3 - "$pkg" "$skill_name" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
data["name"] = sys.argv[2]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
fi

cat <<EOF
Scaffolded ${dest}

Next steps:
  1. Edit SKILL.md (frontmatter + body).
  2. Replace scripts/example.py with real helpers.
  3. Replace tests/test_example.py with real happy + failure tests.
  4. Pick ONE runtime: delete requirements.txt OR package.json.
  5. Validate:
       python scripts/validate-skill.py ${dest#${REPO_ROOT}/}
       cd ${dest#${REPO_ROOT}/} && pytest -q   # or npm test
EOF
