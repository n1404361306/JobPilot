# JobPilot

JobPilot 是一个面向求职场景的全栈智能辅助系统，帮助用户完成简历管理、岗位收集、匹配分析、AI 优化、模拟面试与投递跟踪等完整求职流程。

## 功能概览

| 模块 | 说明 |
|------|------|
| 简历管理 | 文字/文件生成简历、模板编辑、版本管理、预览导出（PDF/DOCX） |
| 岗位管理 | 文本/批量文本/URL/文件/截图导入，AI + 规则解析岗位字段 |
| 匹配分析 | 基于简历与 JD 计算匹配度，输出优势、差距与优化建议 |
| 简历优化 | 针对目标岗位生成优化建议与适配改写方案 |
| 模拟面试 | AI 生成面试题，并对用户回答进行评分与反馈 |
| 投递看板 | 可视化跟踪投递状态（待投递、面试中、Offer 等） |
| 数据统计 | 岗位、投递、匹配分等数据概览与图表展示 |
| AI 总结 | 基于真实求职数据生成阶段性复盘总结，支持删除历史记录 |
| 管理后台 | 用户管理、Prompt 模板、AI/OCR 日志、系统配置（管理员） |

## 技术栈

### 前端

- Vue 3 + TypeScript + Vite
- Element Plus、Pinia、Vue Router、Axios
- ECharts（数据统计）

### 后端

- FastAPI + SQLAlchemy + Alembic
- JWT 认证、Pydantic 数据校验
- OpenAI SDK（兼容 DeepSeek / Qwen / LongCat 等 OpenAI 格式 API）
- OCR：Tesseract / RapidOCR / PaddleOCR
- 文档解析：PyMuPDF、python-docx

### 数据与基础设施

- 数据库：SQLite（本地开发）/ MySQL（部署）
- 缓存与任务：Redis、Celery（已配置，部分流程同步执行）

## 项目结构

```text
JobPilot/
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── api/              # HTTP 封装与接口模块
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 通用组件
│   │   ├── router/           # 路由
│   │   ├── stores/           # Pinia 状态
│   │   └── utils/            # 工具函数
│   └── vite.config.ts        # 开发代理 /api -> :8000
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/routes/       # 路由（auth、business、ai、admin、ocr）
│   │   ├── modules/          # AI、OCR、简历解析等业务模块
│   │   ├── models/           # SQLAlchemy 模型
│   │   └── schemas/          # Pydantic Schema
│   ├── alembic/              # 数据库迁移
│   ├── scripts/              # 初始化与部署脚本
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- （可选）MySQL 8、Redis
- （可选）服务端 OCR 引擎：Tesseract / RapidOCR / PaddleOCR（截图和扫描件识别场景）

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd JobPilot
```

### 2. 启动后端

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head
python scripts/init_test_account.py    # 初始化管理员账号
python scripts/seed_prompt_templates.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端默认地址：`http://127.0.0.1:8000`
健康检查：`GET /health`
API 前缀：`/api`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://127.0.0.1:5173`
开发模式下 `/api` 请求会自动代理到后端 `8000` 端口。

### 4. 登录系统

初始化管理员账号后可使用以下默认账号登录：

| 字段 | 值 |
|------|----|
| 用户名 | `admin` |
| 密码 | `Admin@123456` |

也可通过注册页创建普通用户账号。

## 环境变量

后端配置文件位于 `backend/.env`，可从 `backend/.env.example` 复制。关键项如下：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./jobpilot_dev.db` |
| `SECRET_KEY` | JWT 签名密钥 | 需自行修改 |
| `AI_PRIMARY_KEY` | 主 LLM API Key | 空 |
| `AI_PRIMARY_BASE_URL` | 主 LLM 接口地址 | — |
| `AI_PRIMARY_MODEL` | 主 LLM 模型名 | — |
| `AI_TIMEOUT_SECONDS` | AI 请求超时（秒） | `60` |
| `OCR_ENGINE` | OCR 引擎 | `rapidocr` |

本地快速跑通推荐使用 SQLite，无需安装 MySQL。部署到服务器时，将 `DATABASE_URL` 改为 MySQL 连接串并配置 `MYSQL_*` 变量。

## 常用命令

### 前端

```bash
npm run dev       # 开发服务器
npm run build     # 生产构建
npm run preview   # 预览构建结果
npm run test      # 运行单元测试
```

### 后端

```bash
alembic upgrade head                              # 执行数据库迁移
alembic revision --autogenerate -m "message"    # 生成迁移文件
pytest                                            # 运行测试
uvicorn app.main:app --reload                     # 开发模式启动
```

## 核心 API 分组

| 前缀 | 说明 |
|------|------|
| `/api/auth` | 注册、登录、登出、刷新 Token |
| `/api/resumes` | 简历 CRUD、版本管理 |
| `/api/jobs` | 岗位 CRUD、多种导入方式 |
| `/api/applications` | 投递记录与看板 |
| `/api/matching` | 简历-岗位匹配分析 |
| `/api/ai` | 简历生成/解析/优化、模拟面试、AI 总结 |
| `/api/reports` | 总结列表与删除 |
| `/api/statistics` | 数据统计 |
| `/api/admin` | 管理后台接口 |

完整接口可在后端启动后访问 Swagger 文档：`http://127.0.0.1:8000/docs`

## 批量岗位导入说明

「批量文本」导入支持以下分隔方式：

1. **自动识别**：美团等平台「岗位名 + 日常实习 + 城市」格式的连续列表
2. **空行分隔**：多个岗位块之间用空行分开
3. **显式分隔符**：`---`、`===`、`###`，或自定义分隔字符串

导入后可在右侧表单继续编辑，并在批量结果表格中逐条查看。

## 用户自定义简历模板

模板库支持用户上传 `.html`、`.htm`、`.txt` 模板。上传时可选择：

- **仅自己使用**：默认私有，仅上传者可见和使用
- **公开给其他用户**：其他登录用户可在模板库和模板选择弹窗中查看、选择和复制，但不能修改原模板

模板使用 `{{name}}`、`{{summary}}`、`{{projects}}` 等占位符读取简历表单数据；上传接口为 `POST /api/resume-templates/upload`，选择接口为 `POST /api/resumes/{resume_id}/template`。

详细格式、占位符和接口说明见：`docs/resume_template_requirements.md`；前端页面可访问 `/docs/resume_template_requirements.html`。

## 生产部署

1. 后端使用 Gunicorn + Uvicorn Worker 启动，并配置 MySQL、Redis
2. 前端执行 `npm run build`，将 `dist/` 静态资源交由 Nginx 托管
3. Nginx 反向代理 `/api` 到后端服务
4. 执行 `alembic upgrade head` 完成数据库迁移
5. 配置 LLM API Key 与 `SECRET_KEY`

更多部署细节见：

- `backend/README.md`
- `backend/docs/deployment_acceptance_checklist.md`

## 开发说明

- 后端 API 统一返回 `{ code, message, data }` 结构，`code === 0` 表示成功
- 前端 Axios 默认超时 20 秒；AI 相关接口（优化、面试、总结、批量导入）单独设置为 120 秒
- Prompt 模板可在管理后台维护，也支持通过 `scripts/seed_prompt_templates.py` 初始化
- 上传文件默认保存在 `backend/uploads/`

## 许可证

本项目用于求职流程管理与智能辅助场景，具体授权方式请根据交付要求补充。
