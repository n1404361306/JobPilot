"""expand job and template fields

Revision ID: 0008_expand_job_template_reporting
Revises: 0007_add_demo_closure_tables
Create Date: 2026-06-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_expand_job_template_reporting"
down_revision = "0007_add_demo_closure_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("biz_resume_template") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_system", sa.Boolean(), nullable=True, server_default=sa.true()))
        batch.add_column(sa.Column("copied_from_id", sa.Integer(), nullable=True))
        batch.create_index("ix_biz_resume_template_user_id", ["user_id"])

    with op.batch_alter_table("biz_job") as batch:
        batch.add_column(sa.Column("source_type", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("job_type", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("deadline", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("tags", sa.String(length=512), nullable=True))
        batch.add_column(sa.Column("is_favorite", sa.Boolean(), nullable=True, server_default=sa.false()))
        batch.add_column(sa.Column("import_batch_id", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("biz_job") as batch:
        batch.drop_column("import_batch_id")
        batch.drop_column("is_favorite")
        batch.drop_column("tags")
        batch.drop_column("deadline")
        batch.drop_column("job_type")
        batch.drop_column("source_type")

    with op.batch_alter_table("biz_resume_template") as batch:
        batch.drop_index("ix_biz_resume_template_user_id")
        batch.drop_column("copied_from_id")
        batch.drop_column("is_system")
        batch.drop_column("user_id")
