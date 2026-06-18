"""add demo closure tables

Revision ID: 0007_add_demo_closure_tables
Revises: 0006_add_file_resource_ocr_task
Create Date: 2026-06-16 15:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_add_demo_closure_tables"
down_revision = "0006_add_file_resource_ocr_task"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "biz_resume_version",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("biz_resume.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_name", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_resume_version_resume_id", "biz_resume_version", ["resume_id"])
    op.create_index("ix_biz_resume_version_user_id", "biz_resume_version", ["user_id"])

    op.create_table(
        "biz_application_status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("biz_application.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_application_status_history_application_id", "biz_application_status_history", ["application_id"])
    op.create_index("ix_biz_application_status_history_user_id", "biz_application_status_history", ["user_id"])

    op.create_table(
        "biz_match_report",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("biz_resume.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("biz_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("gaps", sa.Text(), nullable=True),
        sa.Column("suggestions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_match_report_user_id", "biz_match_report", ["user_id"])
    op.create_index("ix_biz_match_report_resume_id", "biz_match_report", ["resume_id"])
    op.create_index("ix_biz_match_report_job_id", "biz_match_report", ["job_id"])

    op.create_table(
        "biz_job_search_report",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False, server_default="weekly"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_job_search_report_user_id", "biz_job_search_report", ["user_id"])

    op.create_table(
        "biz_delivery_profile",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("real_name", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("school", sa.String(length=128), nullable=True),
        sa.Column("major", sa.String(length=128), nullable=True),
        sa.Column("common_answers", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_delivery_profile_user_id", "biz_delivery_profile", ["user_id"])

    op.create_table(
        "biz_delivery_task",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("biz_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("biz_resume.id", ondelete="SET NULL"), nullable=True),
        sa.Column("site_name", sa.String(length=128), nullable=True),
        sa.Column("target_url", sa.String(length=512), nullable=True),
        sa.Column("task_status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("preview_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_delivery_task_user_id", "biz_delivery_task", ["user_id"])
    op.create_index("ix_biz_delivery_task_job_id", "biz_delivery_task", ["job_id"])

    op.create_table(
        "biz_delivery_task_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("biz_delivery_task.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_delivery_task_log_task_id", "biz_delivery_task_log", ["task_id"])
    op.create_index("ix_biz_delivery_task_log_user_id", "biz_delivery_task_log", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_biz_delivery_task_log_user_id", table_name="biz_delivery_task_log")
    op.drop_index("ix_biz_delivery_task_log_task_id", table_name="biz_delivery_task_log")
    op.drop_table("biz_delivery_task_log")
    op.drop_index("ix_biz_delivery_task_job_id", table_name="biz_delivery_task")
    op.drop_index("ix_biz_delivery_task_user_id", table_name="biz_delivery_task")
    op.drop_table("biz_delivery_task")
    op.drop_index("ix_biz_delivery_profile_user_id", table_name="biz_delivery_profile")
    op.drop_table("biz_delivery_profile")
    op.drop_index("ix_biz_job_search_report_user_id", table_name="biz_job_search_report")
    op.drop_table("biz_job_search_report")
    op.drop_index("ix_biz_match_report_job_id", table_name="biz_match_report")
    op.drop_index("ix_biz_match_report_resume_id", table_name="biz_match_report")
    op.drop_index("ix_biz_match_report_user_id", table_name="biz_match_report")
    op.drop_table("biz_match_report")
    op.drop_index("ix_biz_application_status_history_user_id", table_name="biz_application_status_history")
    op.drop_index("ix_biz_application_status_history_application_id", table_name="biz_application_status_history")
    op.drop_table("biz_application_status_history")
    op.drop_index("ix_biz_resume_version_user_id", table_name="biz_resume_version")
    op.drop_index("ix_biz_resume_version_resume_id", table_name="biz_resume_version")
    op.drop_table("biz_resume_version")
