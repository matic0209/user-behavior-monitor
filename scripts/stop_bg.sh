#!/usr/bin/env bash
set -euo pipefail
BASE="/Users/jinbozhang/workspace/user-behavior-monitor"
cd "$BASE"

if [ -f monitor.pid ]; then
  PID=$(cat monitor.pid || true)
  if [ -n "${PID}" ] && ps -p "${PID}" > /dev/null 2>&1; then
    echo "[INFO] 停止进程 ${PID}"
    kill "${PID}" || true
    sleep 1
    if ps -p "${PID}" > /dev/null 2>&1; then
      echo "[WARN] 进程仍在，尝试强制终止"
      kill -9 "${PID}" || true
    fi
  else
    echo "[INFO] 未发现存活的进程"
  fi
  rm -f monitor.pid
else
  echo "[INFO] 未找到 monitor.pid，可忽略"
fi

# 兜底：清理可能残留的单实例 PID 文件
python - <<'PY'
from pathlib import Path
import tempfile
p = Path(tempfile.gettempdir()) / 'user_behavior_monitor.pid'
if p.exists():
    try:
        p.unlink()
        print('[INFO] 已清理单实例PID文件')
    except Exception as e:
        print('[WARN] 清理单实例PID文件失败:', e)
PY

echo "[OK] 已停止"
