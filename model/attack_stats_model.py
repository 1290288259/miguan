# -*- coding: utf-8 -*-
"""
攻击统计模型
定义攻击统计相关的数据库表结构
"""

from database import db
from datetime import datetime

class AttackStats(db.Model):
    """
    攻击统计模型类
    存储按时间维度统计的攻击数据
    """
    __tablename__ = 'attack_stats'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='统计记录ID')
    
    # 统计时间点
    stats_time = db.Column(db.DateTime, nullable=False, comment='统计时间点')
    
    # 统计类型（hour:小时, day:天, week:周, month:月）
    stats_type = db.Column(db.String(10), nullable=False, comment='统计类型')
    
    # 攻击总数
    total_attacks = db.Column(db.Integer, nullable=False, default=0, comment='攻击总数')
    
    # 恶意攻击数
    malicious_attacks = db.Column(db.Integer, nullable=False, default=0, comment='恶意攻击数')
    
    # 唯一攻击IP数
    unique_ips = db.Column(db.Integer, nullable=False, default=0, comment='唯一攻击IP数')
    
    # 按攻击类型分类统计（JSON格式）
    attacks_by_type = db.Column(db.Text, nullable=True, comment='按攻击类型分类统计')
    
    # 按威胁等级分类统计（JSON格式）
    attacks_by_threat = db.Column(db.Text, nullable=True, comment='按威胁等级分类统计')
    
    # 按地理位置分类统计（JSON格式）
    attacks_by_location = db.Column(db.Text, nullable=True, comment='按地理位置分类统计')
    
    # 按蜜罐分类统计（JSON格式）
    attacks_by_honeypot = db.Column(db.Text, nullable=True, comment='按蜜罐分类统计')
    
    # 已封禁IP数
    blocked_ips = db.Column(db.Integer, nullable=False, default=0, comment='已封禁IP数')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        """
        攻击统计模型的字符串表示
        返回:
            str: 攻击统计模型的字符串表示
        """
        return f'<AttackStats {self.stats_type}:{self.stats_time}>'
    
    def to_dict(self):
        """
        将攻击统计模型转换为字典
        返回:
            dict: 攻击统计信息的字典表示
        """
        return {
            'id': self.id,
            'stats_time': self.stats_time.isoformat() if self.stats_time else None,
            'stats_type': self.stats_type,
            'total_attacks': self.total_attacks,
            'malicious_attacks': self.malicious_attacks,
            'unique_ips': self.unique_ips,
            'attacks_by_type': self.attacks_by_type,
            'attacks_by_threat': self.attacks_by_threat,
            'attacks_by_location': self.attacks_by_location,
            'attacks_by_honeypot': self.attacks_by_honeypot,
            'blocked_ips': self.blocked_ips,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }