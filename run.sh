#!/usr/bin/env bash
# Unified simulation launcher script for Linux and macOS

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Resolve preferred Python executable
if [ -f "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON_EXE="$REPO_ROOT/.venv/bin/python"
elif [ -f "$REPO_ROOT/sim_vision/python/.venv/bin/python" ]; then
    PYTHON_EXE="$REPO_ROOT/sim_vision/python/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_EXE="python3"
else
    PYTHON_EXE="python"
fi

echo -e "\033[0;36m[Launcher] Running Robo-helper simulation via ${PYTHON_EXE} run_simulation.py...\033[0m"
exec "$PYTHON_EXE" run_simulation.py "$@"
