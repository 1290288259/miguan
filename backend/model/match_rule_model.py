# -*- coding: utf-8 -*-
"""
匹配规则模型
定义匹配规则相关的数据库表结构
"""

from database import db
from datetime import datetime
from utils.time_utils import get_beijing_time

class MatchRule(db.Model):
    """
    匹配规则模型类
    存储用于判断恶意流量的正则表达式规则
    """
    __tablename__ = 'match_rules'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='规则ID')
    
    # 规则名称
    name = db.Column(db.String(100), nullable=False, comment='规则名称')
    
    # 攻击类型
    attack_type = db.Column(db.String(50), nullable=False, comment='攻击类型')
    
    # 正则表达式
    regex_pattern = db.Column(db.Text, nullable=False, comment='正则表达式')
    
    # 威胁等级（低、中、高、严重）
    threat_level = db.Column(db.String(20), nullable=False, default='medium', comment='威胁等级')
    
    # 规则描述
    description = db.Column(db.Text, nullable=True, comment='规则描述')
    
    # 匹配字段（指定在日志的哪个字段进行匹配）
    match_field = db.Column(db.String(50), nullable=False, default='raw_log', comment='匹配字段')
    
    # 是否启用
    is_enabled = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    
    # 匹配次数统计
    match_count = db.Column(db.Integer, nullable=False, default=0, comment='匹配次数统计')
    
    # 最后匹配时间
    last_matched = db.Column(db.DateTime, nullable=True, comment='最后匹配时间')
    
    # 规则优先级（数字越小优先级越高）
    priority = db.Column(db.Integer, nullable=False, default=100, comment='规则优先级')
    
    # 是否自动封禁
    auto_block = db.Column(db.Boolean, nullable=False, default=False, comment='是否自动封禁')
    
    # 封禁时长（小时，0表示永久封禁）
    block_duration = db.Column(db.Integer, nullable=False, default=0, comment='封禁时长（小时）')
    
    # 创建者ID
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='创建者ID')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, onupdate=get_beijing_time, comment='更新时间')
    
    def __repr__(self):
        """
        匹配规则模型的字符串表示
        返回:
            str: 匹配规则模型的字符串表示
        """
        return f'<MatchRule {self.name}:{self.attack_type}>'
    
    def to_dict(self):
        """
        将匹配规则模型转换为字典
        返回:
            dict: 匹配规则信息的字典表示
        """
        return {
            'id': self.id,
            'name': self.name,
            'attack_type': self.attack_type,
            'regex_pattern': self.regex_pattern,
            'threat_level': self.threat_level,
            'description': self.description,
            'match_field': self.match_field,
            'is_enabled': self.is_enabled,
            'match_count': self.match_count,
            'last_matched': self.last_matched.isoformat() if self.last_matched else None,
            'priority': self.priority,
            'auto_block': self.auto_block,
            'block_duration': self.block_duration,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }