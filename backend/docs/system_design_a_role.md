# 系统设计文档（A角色负责部分）

## 1. 技术选型
- 语言与框架：`Python 3.11` + `FastAPI`
- 数据访问：`SQLAlchemy 2.0` + `Alembic`
- 认证与安全：`JWT` + `passlib[bcrypt]`
- 存储与缓存：`MySQL` + `Redis`
- 服务运行：`Gunicorn` + `Uvicorn`
- 反向代理与守护：`Nginx` + `systemd`
- 异步任务：`Celery Worker`

## 2. 总体架构
- 网关层：`Nginx` 统一入口，反向代理到 FastAPI。
- 应用层：`app/main.py` 组合中间件、异常处理、业务路由。
- 业务层：鉴权、管理员、日志查询等服务。
- 数据层：`SQLAlchemy` 模型 + `Alembic` 迁移。
- 任务层：`Celery` 执行异步任务（预留 AI/OCR/自动投递任务）。

## 3. 后端模块划分
- `app/core`：配置、日志、异常、统一响应、安全能力。
- `app/db`：数据库基类、会话管理。
- `app/models`：`sys_user/sys_role/sys_permission` 及系统配置、日志模型。
- `app/deps`：鉴权依赖、角色权限校验。
- `app/api/routes`：`auth/users/admin` 路由。
- `app/worker`：Celery Worker 入口。
- `scripts`：部署脚本、测试账号初始化脚本。

## 4. 认证与鉴权设计
- 登录发放 `access_token + refresh_token`。
- 支持 `refresh_token` 换新令牌（`POST /api/auth/refresh`）。
- 访问受保护接口时使用 `Authorization: Bearer <token>`。
- `get_current_user` 完成身份解析与用户状态检查。
- `require_roles` 基于 `sys_user_role + sys_role` 实现角色校验。
- `require_permissions` 基于 `sys_role_permission + sys_permission` 实现权限码校验。
- RBAC 关联表：`sys_user_role`、`sys_role_permission`。

## 5. 云服务器部署方案
- 部署目录：`/opt/jobpilot/backend`
- Python 虚拟环境：`/opt/jobpilot/.venv`
- 服务端口：应用 `8000`，公网入口 `80`
- 启动方式：`systemd` 启动 API 与 Celery
- 代理层：`deploy/nginx/jobpilot.conf`

## 6. 日志监控与排障
- 应用日志：标准输出，`systemd journal` 采集。
- 请求日志：中间件记录 `request_id/method/path/status/latency`。
- 业务日志接口：`/api/admin/ai-logs`、`/api/admin/ocr-logs`、`/api/admin/system-logs`。
- 排障建议：优先通过 `journalctl -u jobpilot-api -f` 和 `journalctl -u jobpilot-celery -f` 定位。
- 一键恢复建议：执行 `scripts/recover_services.sh`，并复查 `/health`。

## 7. 安装与卸载方法
### 安装
1. 配置 `.env`（可由 `.env.example` 复制）。
2. 执行 `scripts/deploy.sh`。
3. 运行 `python scripts/init_test_account.py` 初始化测试账号。
4. 验证 `GET /health` 返回正常。

### 卸载
1. `systemctl stop jobpilot-api jobpilot-celery`
2. `systemctl disable jobpilot-api jobpilot-celery`
3. 清理 `/opt/jobpilot/backend` 与 `/opt/jobpilot/.venv`
4. 删除 Nginx 站点配置并重载：`nginx -s reload`
