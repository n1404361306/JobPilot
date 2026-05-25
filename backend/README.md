# JobPilot Backend (A角色交付)

## Quick Start
1. `cp .env.example .env`
2. `pip install -r requirements.txt`
3. `alembic upgrade head`
4. `python scripts/init_test_account.py`
5. `uvicorn app.main:app --reload`

## A角色负责接口
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `PUT /api/auth/password`
- `GET /api/users/me`
- `PUT /api/users/me`
- `GET /api/admin/users`
- `PUT /api/admin/users/{id}/status`
- `GET /api/admin/ai-logs`
- `GET /api/admin/ocr-logs`
- `GET /api/admin/system-logs`
- `GET /api/admin/system-configs`
- `PUT /api/admin/system-configs/{key}`

## 部署验收
- 执行：`bash scripts/post_deploy_check.sh http://127.0.0.1/health`
- 参考：`docs/deployment_acceptance_checklist.md`
- 故障恢复：`bash scripts/recover_services.sh`
