# 本地git管理
建议创建自己的分支进行编程 测试通过后合并到main分支上

## 常用命令：

1、进入工作目录
cd /root/JobPilot
2、切换分支
   确认在正确分支上再写代码
git branch
git checkout main
git checkout -b feature/ai-ocr-delivery（-b在不存在分支的情况下创建）
3、开发完成后提交...
git add .
git commit -m "feat(ai): add AIClient skeleton"
4、分支代码合并回 main
git checkout main
git merge --no-ff feature/ai-ocr-delivery
5、看当前状态
git status
6、看改了哪些文件
git diff
7、提交
git add .
git commit -m "feat(ai): xxx"
8、切换分支
git checkout feature/ai-ocr-delivery
9、看提交历史
git log --oneline --graph --all
10、撤销未提交的修改（慎用）
git checkout -- 某文件

# 项目虚拟环境说明

后端使用miniconda虚拟环境JobPilotBack 支持Python3.11
使用方法：
conda activate JobPilotBack
需要安装的依赖可以补充到requirements.txt文件中
                                 5.29 zyq

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
