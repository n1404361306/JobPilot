#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/jobpilot/backend"
VENV_DIR="/opt/jobpilot/.venv"

echo "[1/5] create app directory"
mkdir -p "${APP_DIR}"

echo "[2/5] sync backend files"
rsync -av --delete ./ "${APP_DIR}/"

echo "[3/5] create venv and install dependencies"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install -r "${APP_DIR}/requirements.txt"

echo "[4/5] run migration"
cd "${APP_DIR}"
alembic upgrade head

echo "[5/5] restart services"
systemctl daemon-reload
systemctl restart jobpilot-api
systemctl restart jobpilot-celery
systemctl enable jobpilot-api
systemctl enable jobpilot-celery

echo "deploy success"
