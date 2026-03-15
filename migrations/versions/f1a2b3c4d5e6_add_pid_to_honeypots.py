"""add_pid_to_honeypots

Revision ID: f1a2b3c4d5e6
Revises: e3a37730dc6b
Create Date: 2026-03-15 14:00:00.000000

为 honeypots 表新增 pid 字段，用于持久化蜜罐子进程的 PID。
服务重启后通过 psutil 检查该 PID 对应的进程是否仍在运行，
避免重复启动已存活的蜜罐进程，修复蜜罐进程状态重启后丢失的 Bug。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e3a37730dc6b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('honeypots', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'pid',
            sa.Integer(),
            nullable=True,
            comment='蜜罐子进程PID，用于重启后判断进程是否仍在运行'
        ))


def downgrade():
    with op.batch_alter_table('honeypots', schema=None) as batch_op:
        batch_op.drop_column('pid')
