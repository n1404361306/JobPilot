"""add c domain detail tables

Revision ID: 0010_add_c_domain_detail_tables
Revises: 0009_add_template_visibility
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_add_c_domain_detail_tables"
down_revision = "0009_add_template_visibility"
branch_labels = None
depends_on = None


def _experience_table(table_name: str, *extra_columns: sa.Column) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("resume_version_id", sa.Integer(), sa.ForeignKey("biz_resume_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        *extra_columns,
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(f"ix_{table_name}_resume_version_id", table_name, ["resume_version_id"])
    op.create_index(f"ix_{table_name}_user_id", table_name, ["user_id"])


def upgrade() -> None:
    _experience_table(
        "biz_education_experience",
        sa.Column("school", sa.String(length=128), nullable=False),
        sa.Column("major", sa.String(length=128), nullable=True),
        sa.Column("degree", sa.String(length=64), nullable=True),
        sa.Column("start_date", sa.String(length=32), nullable=True),
        sa.Column("end_date", sa.String(length=32), nullable=True),
    )
    _experience_table(
        "biz_project_experience",
        sa.Column("project_name", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("technologies", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=32), nullable=True),
        sa.Column("end_date", sa.String(length=32), nullable=True),
    )
    _experience_table(
        "biz_internship_experience",
        sa.Column("company", sa.String(length=128), nullable=False),
        sa.Column("position", sa.String(length=128), nullable=True),
        sa.Column("start_date", sa.String(length=32), nullable=True),
        sa.Column("end_date", sa.String(length=32), nullable=True),
    )
    _experience_table(
        "biz_research_experience",
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("start_date", sa.String(length=32), nullable=True),
        sa.Column("end_date", sa.String(length=32), nullable=True),
    )
    _experience_table(
        "biz_skill",
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("proficiency", sa.String(length=64), nullable=True),
    )
    _experience_table(
        "biz_award",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("issuer", sa.String(length=128), nullable=True),
        sa.Column("award_date", sa.String(length=32), nullable=True),
    )

    op.create_table(
        "biz_resume_render_record",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_version_id", sa.Integer(), sa.ForeignKey("biz_resume_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("biz_resume_template.id", ondelete="SET NULL"), nullable=True),
        sa.Column("output_type", sa.String(length=32), nullable=False, server_default="html"),
        sa.Column("output_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_resume_render_record_user_id", "biz_resume_render_record", ["user_id"])
    op.create_index("ix_biz_resume_render_record_resume_version_id", "biz_resume_render_record", ["resume_version_id"])

    op.create_table(
        "biz_company",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_company_user_id", "biz_company", ["user_id"])
    op.create_index("ix_biz_company_name", "biz_company", ["name"])

    op.create_table(
        "biz_job_requirement",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("biz_job.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("keywords", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_job_requirement_job_id", "biz_job_requirement", ["job_id"])
    op.create_index("ix_biz_job_requirement_user_id", "biz_job_requirement", ["user_id"])

    op.create_table(
        "biz_job_tag",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_job_tag_user_id", "biz_job_tag", ["user_id"])
    op.create_index("ix_biz_job_tag_name", "biz_job_tag", ["name"])

    op.create_table(
        "biz_job_tag_relation",
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("biz_job.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("biz_job_tag.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "biz_job_import_task",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_biz_job_import_task_user_id", "biz_job_import_task", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_biz_job_import_task_user_id", table_name="biz_job_import_task")
    op.drop_table("biz_job_import_task")
    op.drop_table("biz_job_tag_relation")
    op.drop_index("ix_biz_job_tag_name", table_name="biz_job_tag")
    op.drop_index("ix_biz_job_tag_user_id", table_name="biz_job_tag")
    op.drop_table("biz_job_tag")
    op.drop_index("ix_biz_job_requirement_user_id", table_name="biz_job_requirement")
    op.drop_index("ix_biz_job_requirement_job_id", table_name="biz_job_requirement")
    op.drop_table("biz_job_requirement")
    op.drop_index("ix_biz_company_name", table_name="biz_company")
    op.drop_index("ix_biz_company_user_id", table_name="biz_company")
    op.drop_table("biz_company")
    op.drop_index("ix_biz_resume_render_record_resume_version_id", table_name="biz_resume_render_record")
    op.drop_index("ix_biz_resume_render_record_user_id", table_name="biz_resume_render_record")
    op.drop_table("biz_resume_render_record")
    for table_name in (
        "biz_award",
        "biz_skill",
        "biz_research_experience",
        "biz_internship_experience",
        "biz_project_experience",
        "biz_education_experience",
    ):
        op.drop_index(f"ix_{table_name}_user_id", table_name=table_name)
        op.drop_index(f"ix_{table_name}_resume_version_id", table_name=table_name)
        op.drop_table(table_name)
