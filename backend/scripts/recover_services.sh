#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] restart api service"
systemctl restart jobpilot-api
systemctl is-active --quiet jobpilot-api
echo "jobpilot-api active"

echo "[2/4] restart celery service"
systemctl restart jobpilot-celery
systemctl is-active --quiet jobpilot-celery
echo "jobpilot-celery active"

echo "[3/4] reload nginx"
nginx -t
systemctl reload nginx
echo "nginx reloaded"

echo "[4/4] health check"
curl -fsS http://127.0.0.1/health
echo
echo "recovery flow done"
