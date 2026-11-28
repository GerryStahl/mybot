#!/usr/bin/env bash
# End-of-day routine for MYbot: clean up, lint, test, check docs, commit, push.
# Usage: scripts/end_of_day.sh [-m "commit message"] [-n]   (-n = dry run, no commit/push)
# Stops at the first failing step, so nothing broken gets pushed.
set -euo pipefail

cd "$(dirname "$0")/.."
MESSAGE="End-of-day update $(date +%Y-%m-%d)"
DRY_RUN=0
while getopts "m:n" opt; do
  case $opt in
    m) MESSAGE=$OPTARG ;;
    n) DRY_RUN=1 ;;
    *) echo "Usage: $0 [-m message] [-n]"; exit 2 ;;
  esac
done

PY=.venv/bin
[ -x "$PY/ruff" ] || { echo "Missing .venv. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"; exit 1; }

echo "== 1/5 Clean up"
find . -path ./.venv -prune -o -path ./.git -prune -o -name __pycache__ -type d -exec rm -rf {} +
rm -rf .pytest_cache .ruff_cache
find . -path ./.venv -prune -o -name .DS_Store -type f -delete
$PY/ruff check --fix src tests
$PY/ruff format src tests

echo "== 2/5 Tests"
$PY/pytest -q

echo "== 3/5 Documentation check"
if [ -n "$(git status --porcelain -- src scripts Modelfile requirements.txt)" ] \
   && [ -z "$(git status --porcelain -- README.md)" ]; then
  echo "WARNING: code changed but README.md did not. Does the documentation need updating?"
fi

echo "== 4/5 Changes to commit"
git add -A
git status --short
if git diff --cached --quiet; then
  echo "Nothing to commit."
  exit 0
fi

if [ "$DRY_RUN" = 1 ]; then
  git reset -q
  echo "Dry run: nothing committed."
  exit 0
fi

echo "== 5/5 Commit and push"
git commit -q -m "$MESSAGE" ${COMMIT_TRAILER:+-m "$COMMIT_TRAILER"}
git push
git --no-pager log --oneline -1
