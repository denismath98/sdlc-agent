#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${REPO_PATH:-/repo}"

if [ ! -d "$REPO_PATH" ]; then
  echo "ERROR: REPO_PATH '$REPO_PATH' does not exist."
  exit 2
fi

cd "$REPO_PATH"

if [ ! -e ".git" ]; then
  echo "ERROR: '$REPO_PATH' is not a git repository (.git not found)."
  exit 2
fi

git config --global --add safe.directory "$REPO_PATH"

exec python -m app.main "$@"