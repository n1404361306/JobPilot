# JobPilot Backend

JobPilot 后端基于 FastAPI、SQLAlchemy 和 Alembic，提供认证授权、简历管理、岗位管理、AI 能力、OCR、投递跟踪、统计分析和管理后台接口。

## 快速启动

```bash
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head
python scripts/init_test_account.py
python scripts/seed_prompt_templates.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

默认服务地址：`http://127.0.0.1:8000`

接口文档：`http://127.0.0.1:8000/docs`

## 本地数据库

本地开发可直接使用 `.env.example` 中的 SQLite 配置，数据库文件默认生成在 `backend/jobpilot_dev.db`。

部署到服务器时，建议将 `DATABASE_URL` 改为 MySQL 连接串，并按实际环境配置 `MYSQL_*`、`SECRET_KEY`、LLM API Key 和 OCR 相关参数。

## 主要接口

- `/api/auth`：注册、登录、登出、刷新 Token
- `/api/users`：个人资料
- `/api/resumes`：简历 CRUD、版本管理、模板选择
- `/api/resume-templates`：简历模板查询、上传、管理
- `/api/jobs`：岗位 CRUD 和多来源导入
- `/api/applications`：投递记录与状态流转
- `/api/matching`：简历与岗位匹配分析
- `/api/ai`：简历生成、解析、优化和模拟面试
- `/api/statistics`：统计分析
- `/api/admin`：用户、日志、配置和 Prompt 管理

## 常用命令

```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
pytest
uvicorn app.main:app --reload
```

## 部署检查

```bash
bash scripts/post_deploy_check.sh http://127.0.0.1/health
```

更多部署验收项见：`docs/deployment_acceptance_checklist.md`
