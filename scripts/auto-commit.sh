#!/usr/bin/env bash
# auto-commit.sh — 定时同步 OpenClaw 数据变动
# 用法：Linux cron 每 30 分钟调用一次
# 只在有 git 变动时才 commit + push；commit 前先 pull

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$REPO_DIR/logs/auto-commit.log"
GIT="git -C $REPO_DIR"

mkdir -p "$REPO_DIR/logs"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# 先拉取远程变动（rebase 避免产生无意义的 merge commit）
log "--- auto-commit 开始 ---"
if ! $GIT pull --rebase --autostash 2>> "$LOG_FILE"; then
  log "ERROR: git pull 失败，跳过本次 commit"
  exit 1
fi

# 检查是否有变动（包含未追踪文件）
if $GIT status --porcelain | grep -q .; then
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
  $GIT add -A --ignore-errors
  $GIT commit -m "chore(auto): 数据同步 ${TIMESTAMP}" >> "$LOG_FILE" 2>&1
  if $GIT push >> "$LOG_FILE" 2>&1; then
    log "✅ commit + push 完成"
  else
    log "ERROR: push 失败（网络或权限）"
    exit 1
  fi
else
  log "无变动，跳过"
fi
