"""
LLM client chat with usage的返回结构
"""

from pydantic import BaseModel
import datetime

class AIUsage(BaseModel):
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    timestamp: datetime.datetime = datetime.datetime.now()

class AIChatResult(BaseModel):
    content: str
    usage: AIUsage
    provider: str
    model: str