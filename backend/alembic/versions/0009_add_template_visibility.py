"""add resume template visibility

Revision ID: 0009_add_template_visibility
Revises: 0008_expand_job_template_reporting
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_add_template_visibility"
down_revision = "0008_expand_job_template_reporting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("biz_resume_template") as batch:
        batch.add_column(sa.Column("is_public", sa.Boolean(), nullable=True, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table("biz_resume_template") as batch:
        batch.drop_column("is_public")
