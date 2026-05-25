# 云服务器部署验收清单（A角色）

## 一、上线前检查
- [ ] `.env` 已按生产环境填写，`SECRET_KEY` 已替换。
- [ ] `alembic upgrade head` 可执行成功。
- [ ] `admin` 测试账号可初始化。
- [ ] Nginx 与 systemd 配置文件路径正确。

## 二、上线执行步骤
1. 执行 `scripts/deploy.sh`
2. 执行 `python scripts/init_test_account.py`
3. 执行 `scripts/post_deploy_check.sh http://127.0.0.1/health`

## 三、上线验收项
- [ ] `jobpilot-api` 服务状态为 `active`
- [ ] `jobpilot-celery` 服务状态为 `active`
- [ ] 健康检查 `/health` 返回 `{"status":"ok"}`
- [ ] 日志中无连续报错（最近20行）
- [ ] 管理员登录接口可用
- [ ] `GET /api/admin/system-configs` 可返回数据

## 四、异常恢复演练
- [ ] 手动重启 `jobpilot-api` 后服务恢复
- [ ] 手动重启 `jobpilot-celery` 后任务可消费
- [ ] Nginx 重载后转发正常
- [ ] 记录一次回滚流程演练（保留命令和结果）

## 五、产物留存
- [ ] 部署验收报告（`deploy_check_report_*.md`）
- [ ] 运行截图（服务状态、健康检查、后台页面）
- [ ] 本次上线的提交号与迁移版本号
