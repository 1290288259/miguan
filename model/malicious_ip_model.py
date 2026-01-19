# -*- coding: utf-8 -*-
"""
恶意IP模型
定义恶意IP相关的数据库表结构
"""

from database import db
from datetime import datetime

class MaliciousIP(db.Model):
    """
    恶意IP模型类
    存储恶意IP及其封禁状态
    """
    __tablename__ = 'malicious_ips'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='恶意IP记录ID')
    
    # IP地址
    ip_address = db.Column(db.String(15), unique=True, nullable=False, comment='IP地址')
    
    # 首次发现时间
    first_seen = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='首次发现时间')
    
    # 最后活动时间
    last_seen = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='最后活动时间')
    
    # 攻击次数
    attack_count = db.Column(db.Integer, nullable=False, default=1, comment='攻击次数')
    
    # 攻击类型列表（JSON格式存储多种攻击类型）
    attack_types = db.Column(db.Text, nullable=True, comment='攻击类型列表')
    
    # 威胁等级（低、中、高、严重）
    threat_level = db.Column(db.String(20), nullable=False, default='medium', comment='威胁等级')
    
    # 是否被标记为恶意
    is_marked = db.Column(db.Boolean, nullable=False, default=True, comment='是否被标记为恶意')
    
    # 是否被封禁
    is_blocked = db.Column(db.Boolean, nullable=False, default=False, comment='是否被封禁')
    
    # 封禁时间
    blocked_time = db.Column(db.DateTime, nullable=True, comment='封禁时间')
    
    # 封禁原因
    block_reason = db.Column(db.Text, nullable=True, comment='封禁原因')
    
    # 封禁期限（永久封禁为null）
    block_until = db.Column(db.DateTime, nullable=True, comment='封禁期限')
    
    # 来源蜜罐ID列表（JSON格式）
    source_honeypots = db.Column(db.Text, nullable=True, comment='来源蜜罐ID列表')
    
    # 地理位置（国家、地区等）
    location = db.Column(db.String(100), nullable=True, comment='地理位置')
    
    # ISP信息
    isp = db.Column(db.String(100), nullable=True, comment='ISP信息')
    
    # 备注
    notes = db.Column(db.Text, nullable=True, comment='备注')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        """
        恶意IP模型的字符串表示
        返回:
            str: 恶意IP模型的字符串表示
        """
        return f'<MaliciousIP {self.ip_address}>'
    
    def to_dict(self):
        """
        将恶意IP模型转换为字典
        返回:
            dict: 恶意IP信息的字典表示
        """
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'attack_count': self.attack_count,
            'attack_types': self.attack_types,
            'threat_level': self.threat_level,
            'is_marked': self.is_marked,
            'is_blocked': self.is_blocked,
            'blocked_time': self.blocked_time.isoformat() if self.blocked_time else None,
            'block_reason': self.block_reason,
            'block_until': self.block_until.isoformat() if self.block_until else None,
            'source_honeypots': self.source_honeypots,
            'location': self.location,
            'isp': self.isp,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }