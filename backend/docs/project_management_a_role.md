# 项目管理文档（A角色负责部分）

## 1. 成员分工
- A：后端基础架构、认证鉴权、管理员模块、云部署、项目管理与文档统筹。
- B：前端主应用与响应式页面实现。
- C：简历/模板/岗位/投递业务后端。
- D：AI/OCR/自动投递 Worker 与报告能力。

## 2. Git 规范
- 分支：`main`（稳定） + `feature/<module-name>`（开发）
- 提交格式：`type(scope): message`
- 合并策略：PR 审核通过后 squash merge
- 禁止：直接 push 主分支、无描述提交信息

## 3. 开发计划（A角色视角）
- 第1周：完成后端骨架、配置、DB会话、迁移、统一响应/异常/日志。
- 第2周：完成认证登录、JWT、RBAC、管理员用户管理与系统配置接口。
- 第3周：完成后台日志查询接口，协同 B/C/D 进行接口联调。
- 第4周：完成云服务器部署方案落地（Nginx/systemd/Celery）。
- 第5周：汇总运行截图、部署记录、代码统计，整理交付材料。

## 4. 部署记录模板
- 部署时间：
- 部署分支与提交：
- 数据库迁移版本：
- 服务重启结果：
- 健康检查结果：
- 回滚点：

## 5. 代码量统计方法
- 后端代码：`app` + `alembic` + `scripts`
- 统计命令建议：
  - `git log --author=\"<name>\" --pretty=tformat: --numstat`
  - `git shortlog -sn`
- 每周更新：新增行、删除行、净变更、模块分布

## 6. 风险与缓解
- 接口反复变动：冻结鉴权与用户核心字段，版本化接口约定。
- 环境不一致：统一 `.env.example` 并建立部署前检查清单。
- 联调阻塞：每周固定一次接口走查，按优先级处理跨模块问题。

## 7. 组长执行产物清单
- 周计划与里程碑追踪：见 `docs/team_management_templates.md`
- 联调风险台账与阻塞项跟踪：见 `docs/team_management_templates.md`
- A对B/C/D接口契约草稿：见 `docs/interface_contract_a_to_bcd.md`
- 部署验收清单：见 `docs/deployment_acceptance_checklist.md`
