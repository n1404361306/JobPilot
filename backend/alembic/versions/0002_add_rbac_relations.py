"""add rbac relation tables and seed permissions

Revision ID: 0002_add_rbac_relations
Revises: 0001_init_auth_admin
Create Date: 2026-05-19 15:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_rbac_relations"
down_revision = "0001_init_auth_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sys_user_role",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "sys_role_permission",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("sys_permission.id", ondelete="CASCADE"), primary_key=True),
    )

    op.execute("INSERT INTO sys_role(code, name) VALUES ('admin', '管理员'), ('user', '普通用户')")
    op.execute(
        """
        INSERT INTO sys_permission(code, name) VALUES
        ('admin:users:read', '查看用户'),
        ('admin:users:write', '修改用户状态'),
        ('admin:logs:read', '查看后台日志'),
        ('admin:configs:read', '查看系统配置'),
        ('admin:configs:write', '修改系统配置')
        """
    )
    op.execute(
        """
        INSERT INTO sys_role_permission(role_id, permission_id)
        SELECT r.id, p.id
        FROM sys_role r
        JOIN sys_permission p ON r.code = 'admin'
        """
    )


def downgrade() -> None:
    op.drop_table("sys_role_permission")
    op.drop_table("sys_user_role")
