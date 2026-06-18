# 在 Python shell 或临时脚本里
from app.worker.celery_app import echo
result = echo.delay("hello")
print(result.get(timeout=10))  # 应输出 hello