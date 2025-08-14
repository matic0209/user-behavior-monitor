#!/usr/bin/env bash
set -euo pipefail
BASE="/Users/jinbozhang/workspace/user-behavior-monitor"
cd "$BASE"

if [ -f monitor.pid ]; then
  PID=$(cat monitor.pid || true)
  if [ -n "${PID}" ] && ps -p "${PID}" > /dev/null 2>&1; then
    echo "[RUNNING] PID=${PID}"
    exit 0
  fi
fi

echo "[STOPPED]"
exit 1
