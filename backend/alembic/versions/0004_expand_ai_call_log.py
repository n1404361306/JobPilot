"""
expand ai_log to ai_call_log

Revision ID: 0004_expand_ai_call_log
Revises: 0003_add_prompt_template
Create Date: 2026-06-14 21:04
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_expand_ai_call_log"
down_revision = "0003_add_prompt_template"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1.重命名表
    op.rename_table("ai_log", "ai_call_log")

    # 2.删除旧字段:prompt_summary
    op.drop_column("ai_call_log", "prompt_summary")

    #3.新增字段
    op.add_column("ai_call_log", sa.Column("user_id", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ai_call_log", sa.Column("prompt_type", sa.String(length=64), nullable=False, server_default="unknown"))
    op.add_column("ai_call_log", sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ai_call_log", sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ai_call_log", sa.Column("cost_estimate", sa.Numeric(10, 4), nullable=False, server_default="0"))
    op.add_column("ai_call_log", sa.Column("status", sa.String(length=32), nullable=False, server_default="success"))
    op.add_column("ai_call_log", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("ai_call_log", sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"))

    op.create_index("ix_ai_call_log_user_id", "ai_call_log", ["user_id"])
    op.create_index("ix_ai_call_log_prompt_type", "ai_call_log", ["prompt_type"])

def downgrade() -> None:
    op.drop_index("ix_ai_call_log_user_id", "ai_call_log")
    op.drop_index("ix_ai_call_log_prompt_type", "ai_call_log")
    
    op.drop_column("ai_call_log", "user_id")
    op.drop_column("ai_call_log", "prompt_type")
    op.drop_column("ai_call_log", "input_tokens")
    op.drop_column("ai_call_log", "output_tokens")
    op.drop_column("ai_call_log", "cost_estimate")
    op.drop_column("ai_call_log", "status")
    op.drop_column("ai_call_log", "error_message")
    op.drop_column("ai_call_log", "duration_ms")
    
    op.add_column("ai_call_log", sa.Column("prompt_summary", sa.Text(), nullable=False, server_default=""))
    op.rename_table("ai_call_log", "ai_log")
