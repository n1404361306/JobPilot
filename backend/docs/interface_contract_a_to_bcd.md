# A对B/C/D接口契约草稿

## 统一约定
- Base URL: `/api`
- 鉴权：`Authorization: Bearer <access_token>`
- 成功返回：`{ "code": 0, "message": "ok", "data": ... }`
- 失败返回：`{ "code": <业务码>, "message": "<错误说明>", "data": null }`

## A -> B（前端）
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

## A -> C（核心业务后端）
- C侧业务接口必须接入 `get_current_user` 鉴权依赖。
- 角色判定建议复用 `require_roles`；权限粒度判定复用 `require_permissions`。
- 需共享的公共模型字段（冻结）：
  - user: `id, username, email, is_active, is_superuser`
  - role: `id, code, name`
  - permission: `id, code, name`
- C侧已交付业务接口：
  - `GET /api/resumes`
  - `POST /api/resumes`
  - `GET /api/resumes/{resume_id}`
  - `PUT /api/resumes/{resume_id}`
  - `DELETE /api/resumes/{resume_id}`
  - `GET /api/resume-templates`
  - `GET /api/resume-templates/manage`（需 `business:templates:write`）
  - `POST /api/resume-templates`（需 `business:templates:write`）
  - `PUT /api/resume-templates/{template_id}`（需 `business:templates:write`）
  - `DELETE /api/resume-templates/{template_id}`（需 `business:templates:write`）
  - `GET /api/jobs`
  - `POST /api/jobs`
  - `GET /api/jobs/{job_id}`
  - `PUT /api/jobs/{job_id}`
  - `DELETE /api/jobs/{job_id}`
  - `GET /api/applications`
  - `POST /api/applications`
  - `GET /api/applications/{application_id}`
  - `PUT /api/applications/{application_id}`
  - `DELETE /api/applications/{application_id}`

## A -> D（AI/OCR/Worker）
- Worker 服务统一使用 `Celery + Redis`。
- 日志需写入 `ai_log/ocr_log/system_log` 供管理后台查询。
- 关键失败必须写 `system_log` 并标注错误级别与上下文摘要。
