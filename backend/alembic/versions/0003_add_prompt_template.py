"""add prompt_template table
Revision ID: 0003_add_prompt_template
Revises: 0002_add_rbac_relations
Create Date: 2026-06-10 11:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_prompt_template"
down_revision = "0002_add_rbac_relations"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "prompt_template",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("template_code", sa.String(128), nullable=False),
        sa.Column("template_name",sa.String(128),nullable=False),
        sa.Column("template_content",sa.Text(),nullable=False),
        sa.Column("version",sa.Integer(),nullable=False,default=1),
        sa.Column("enabled",sa.Boolean(),nullable=False,default=True),
        sa.Column("created_at",sa.DateTime(),nullable=False),
        sa.Column("updated_at",sa.DateTime(),nullable=False),
    )

    op.create_index("ix_prompt_template_code","prompt_template",["template_code"])
    op.create_unique_constraint(
        "uq_prompt_template_code_version",
        "prompt_template",
        ["template_code","version"],
        )
    
def downgrade() -> None:
        op.drop_constraint("uq_prompt_template_code_version", "prompt_template", type="unique")
        op.drop_index("ix_prompt_template_code", table_name="prompt_template")
        op.drop_table("prompt_template")
