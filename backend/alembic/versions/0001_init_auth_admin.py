"""init auth and admin tables

Revision ID: 0001_init_auth_admin
Revises:
Create Date: 2026-05-19 15:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init_auth_admin"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sys_user",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sys_user_username", "sys_user", ["username"], unique=True)
    op.create_index("ix_sys_user_email", "sys_user", ["email"], unique=True)

    op.create_table(
        "sys_role",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_sys_role_code", "sys_role", ["code"], unique=True)

    op.create_table(
        "sys_permission",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
    )
    op.create_index("ix_sys_permission_code", "sys_permission", ["code"], unique=True)

    op.create_table(
        "system_config",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("config_key", sa.String(length=128), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
    )
    op.create_index("ix_system_config_key", "system_config", ["config_key"], unique=True)

    op.create_table(
        "ai_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "ocr_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "system_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_log")
    op.drop_table("ocr_log")
    op.drop_table("ai_log")
    op.drop_index("ix_system_config_key", table_name="system_config")
    op.drop_table("system_config")
    op.drop_index("ix_sys_permission_code", table_name="sys_permission")
    op.drop_table("sys_permission")
    op.drop_index("ix_sys_role_code", table_name="sys_role")
    op.drop_table("sys_role")
    op.drop_index("ix_sys_user_email", table_name="sys_user")
    op.drop_index("ix_sys_user_username", table_name="sys_user")
    op.drop_table("sys_user")
