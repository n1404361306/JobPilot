"""
add file_resource and ocr_task

Revision ID: 0006_add_file_resource_ocr_task
Revises: 0005_add_business_tables
Create Date: 2026-06-15 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_add_file_resource_ocr_task"
down_revision = "0005_add_business_tables"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "file_resource",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_type", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("related_type", sa.String(length=64), nullable=True),
        sa.Column("related_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_file_resource_user_id", "file_resource", ["user_id"])
    
    op.create_table(
        "ocr_task",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_resource.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("confidence_avg", sa.Numeric(5, 2), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_ocr_task_user_id", "ocr_task", ["user_id"])
    op.create_index("ix_ocr_task_file_id", "ocr_task", ["file_id"])

def downgrade() -> None:
    op.drop_index("ix_ocr_task_file_id", table_name="ocr_task")
    op.drop_index("ix_ocr_task_user_id", table_name="ocr_task")
    op.drop_table("ocr_task")
    op.drop_index("ix_file_resource_user_id", table_name="file_resource")
    op.drop_table("file_resource")
