"""add business tables for resumes jobs applications

Revision ID: 0005_add_business_tables
Revises: 0004_expand_ai_call_log
Create Date: 2026-06-14 21:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_business_tables"
down_revision = "0004_expand_ai_call_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "biz_resume",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_url", sa.String(length=512), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_resume_user_id", "biz_resume", ["user_id"])

    op.create_table(
        "biz_resume_template",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "biz_job",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("company", sa.String(length=128), nullable=False),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.Column("salary_range", sa.String(length=128), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_job_user_id", "biz_job", ["user_id"])

    op.create_table(
        "biz_application",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("biz_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("biz_resume.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("channel", sa.String(length=64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_application_user_id", "biz_application", ["user_id"])
    op.create_index("ix_biz_application_job_id", "biz_application", ["job_id"])

    op.execute(
        """
        INSERT INTO sys_permission(code, name) VALUES
        ('business:templates:write', '管理简历模板')
        """
    )
    op.execute(
        """
        INSERT INTO sys_role_permission(role_id, permission_id)
        SELECT r.id, p.id
        FROM sys_role r
        JOIN sys_permission p ON p.code = 'business:templates:write'
        WHERE r.code = 'admin'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_biz_application_job_id", table_name="biz_application")
    op.drop_index("ix_biz_application_user_id", table_name="biz_application")
    op.drop_table("biz_application")
    op.drop_index("ix_biz_job_user_id", table_name="biz_job")
    op.drop_table("biz_job")
    op.drop_table("biz_resume_template")
    op.drop_index("ix_biz_resume_user_id", table_name="biz_resume")
    op.drop_table("biz_resume")
    op.execute(
        """
        DELETE FROM sys_role_permission
        WHERE permission_id IN (
            SELECT id FROM sys_permission WHERE code = 'business:templates:write'
        )
        """
    )
    op.execute("DELETE FROM sys_permission WHERE code = 'business:templates:write'")
