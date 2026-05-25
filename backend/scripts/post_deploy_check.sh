#!/usr/bin/env bash
set -euo pipefail

API_URL="${1:-http://127.0.0.1/health}"
REPORT_FILE="${2:-deploy_check_report_$(date +%Y%m%d_%H%M%S).md}"

{
  echo "# 部署验收报告"
  echo ""
  echo "- 时间: $(date '+%F %T')"
  echo "- 健康检查地址: ${API_URL}"
  echo ""
  echo "## 1) systemd 服务状态"
  systemctl is-active jobpilot-api >/dev/null && echo "- jobpilot-api: active" || echo "- jobpilot-api: inactive"
  systemctl is-active jobpilot-celery >/dev/null && echo "- jobpilot-celery: active" || echo "- jobpilot-celery: inactive"
  echo ""
  echo "## 2) 健康检查"
  if curl -fsS "${API_URL}" >/tmp/jobpilot_health.out 2>/tmp/jobpilot_health.err; then
    echo "- health: pass"
    echo ""
    echo '```json'
    cat /tmp/jobpilot_health.out
    echo ""
    echo '```'
  else
    echo "- health: fail"
    echo ""
    echo '```text'
    cat /tmp/jobpilot_health.err
    echo '```'
  fi
  echo ""
  echo "## 3) 最近服务日志（各20行）"
  echo ""
  echo "### jobpilot-api"
  echo '```text'
  journalctl -u jobpilot-api -n 20 --no-pager || true
  echo '```'
  echo ""
  echo "### jobpilot-celery"
  echo '```text'
  journalctl -u jobpilot-celery -n 20 --no-pager || true
  echo '```'
} >"${REPORT_FILE}"

echo "deploy check report generated: ${REPORT_FILE}"
