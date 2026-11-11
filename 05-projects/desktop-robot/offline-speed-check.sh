#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" == "--inside" ]]; then
    shift
    ip link set lo up
    exec runuser -u orangepi -- "$PWD/.venv/bin/python" "$PWD/speed_acceptance.py" "$@"
fi
# Namespace changes only the test process tree; Ethernet SSH stays available.
exec sudo unshare --net -- bash "$PWD/offline-speed-check.sh" --inside "$@"
