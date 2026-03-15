# -*- coding: utf-8 -*-
"""
封禁历史模型
定义封禁历史相关的数据库表结构
"""

from database import db
from datetime import datetime
from utils.time_utils import get_beijing_time

class BlockHistory(db.Model):
    """
    封禁历史模型类
    存储IP封禁和解封的历史记录
    """
    __tablename__ = 'block_history'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='封禁记录ID')
    
    # IP地址
    ip_address = db.Column(db.String(15), nullable=False, comment='IP地址')
    
    # 封禁时间
    block_time = db.Column(db.DateTime, nullable=False, default=get_beijing_time, comment='封禁时间')
    
    # 解封时间
    unblock_time = db.Column(db.DateTime, nullable=True, comment='解封时间')
    
    # 封禁原因
    block_reason = db.Column(db.Text, nullable=True, comment='封禁原因')
    
    # 封禁类型（manual:手动, auto:自动）
    block_type = db.Column(db.String(10), nullable=False, default='manual', comment='封禁类型')
    
    # 封禁时长（小时，0表示永久封禁）
    block_duration = db.Column(db.Integer, nullable=False, default=0, comment='封禁时长（小时）')
    
    # 预计解封时间
    scheduled_unblock_time = db.Column(db.DateTime, nullable=True, comment='预计解封时间')
    
    # 操作人ID（手动封禁时记录）
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='操作人ID')
    
    # 关联的匹配规则ID（自动封禁时记录）
    rule_id = db.Column(db.Integer, db.ForeignKey('match_rules.id'), nullable=True, comment='关联的匹配规则ID')
    
    # 关联的日志ID列表（JSON格式）
    related_logs = db.Column(db.Text, nullable=True, comment='关联的日志ID列表')
    
    # 解封原因
    unblock_reason = db.Column(db.Text, nullable=True, comment='解封原因')
    
    # 解封操作人ID
    unblock_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='解封操作人ID')
    
    # 是否已解封
    is_unblocked = db.Column(db.Boolean, nullable=False, default=False, comment='是否已解封')
    
    # 备注
    notes = db.Column(db.Text, nullable=True, comment='备注')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, onupdate=get_beijing_time, comment='更新时间')
    
    def __repr__(self):
        """
        封禁历史模型的字符串表示
        返回:
            str: 封禁历史模型的字符串表示
        """
        return f'<BlockHistory {self.ip_address}:{self.block_time}>'
    
    def to_dict(self):
        """
        将封禁历史模型转换为字典
        返回:
            dict: 封禁历史信息的字典表示
        """
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'block_time': self.block_time.isoformat() if self.block_time else None,
            'unblock_time': self.unblock_time.isoformat() if self.unblock_time else None,
            'block_reason': self.block_reason,
            'block_type': self.block_type,
            'block_duration': self.block_duration,
            'scheduled_unblock_time': self.scheduled_unblock_time.isoformat() if self.scheduled_unblock_time else None,
            'operator_id': self.operator_id,
            'rule_id': self.rule_id,
            'related_logs': self.related_logs,
            'unblock_reason': self.unblock_reason,
            'unblock_operator_id': self.unblock_operator_id,
            'is_unblocked': self.is_unblocked,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }