#!/usr/bin/env bash
set -euo pipefail
BASE="/Users/jinbozhang/workspace/user-behavior-monitor"
cd "$BASE"

# 确保日志目录
mkdir -p logs

# 检查并提示虚拟环境
if [ ! -x .venv/bin/python ]; then
  echo "[ERROR] 未找到虚拟环境 .venv，请先创建并安装依赖" >&2
  exit 1
fi

# 如果已有旧PID，先尝试清理
if [ -f monitor.pid ]; then
  OLD_PID=$(cat monitor.pid || true)
  if [ -n "${OLD_PID}" ] && ps -p "${OLD_PID}" > /dev/null 2>&1; then
    echo "[INFO] 发现旧进程 ${OLD_PID}，先终止它"
    kill "${OLD_PID}" || true
    sleep 1
  fi
  rm -f monitor.pid
fi

# 后台启动
nohup .venv/bin/python user_behavior_monitor.py >> logs/daemon.log 2>&1 &
NEW_PID=$!

echo ${NEW_PID} > monitor.pid
sleep 1
if ps -p "${NEW_PID}" > /dev/null 2>&1; then
  echo "[OK] 后台已启动，PID=${NEW_PID}"
  echo "日志: $BASE/logs/daemon.log"
else
  echo "[ERROR] 启动失败，详见日志: $BASE/logs/daemon.log" >&2
  exit 1
fi
