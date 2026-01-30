#!/usr/bin/env bash
set -euo pipefail

# Where the target repo is mounted
REPO_PATH="${REPO_PATH:-/repo}"

if [ ! -d "$REPO_PATH" ]; then
  echo "ERROR: REPO_PATH '$REPO_PATH' does not exist. Mount a repo to /repo (or set REPO_PATH)."
  exit 2
fi

cd "$REPO_PATH"

# If repo has no git metadata (someone mounted a folder), fail early
if [ ! -d ".git" ]; then
  echo "ERROR: '$REPO_PATH' is not a git repository (.git not found)."
  exit 2
fi

CMD="${1:-help}"

case "$CMD" in
  code-agent)
    shift
    python /app/run_code_agent.py "$@"
    ;;
  reviewer)
    shift
    python /app/agents/review_agent/reviewer.py "$@"
    ;;
  ci)
    # optional local CI: black + pytest (non-fatal)
    set +e
    black --check . | tee black.log
    BLACK_RC=$?
    python -m pytest -q | tee pytest.log
    PYTEST_RC=$?
    echo "BLACK_RC=$BLACK_RC"
    echo "PYTEST_RC=$PYTEST_RC"
    # never fail container for demo
    exit 0
    ;;
  help|*)
    echo "Usage:"
    echo "  docker run ... sdlc-agent code-agent --issue <N>"
    echo "  docker run ... sdlc-agent code-agent --pr <N>"
    echo "  docker run ... sdlc-agent reviewer --pr <N>"
    echo "  docker run ... sdlc-agent ci"
    ;;
esac