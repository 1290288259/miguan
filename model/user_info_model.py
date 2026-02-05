# -*- coding: utf-8 -*-
"""
用户信息模型
定义用户信息相关的数据库表结构
"""

from database import db
from datetime import datetime

class UserInfo(db.Model):
    """
    用户信息模型类
    存储用户的详细信息，如手机号、邮箱等
    """
    __tablename__ = 'user_infos'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户信息ID')
    
    # 关联的用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, comment='关联的用户ID')
    
    # 手机号
    phone = db.Column(db.String(20), nullable=True, comment='手机号')
    
    # 邮箱地址
    email = db.Column(db.String(100), nullable=True, comment='邮箱地址')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 定义与User模型的关系（可选，方便反向查询）
    # user = db.relationship('User', backref=db.backref('info', uselist=False))
    
    def __repr__(self):
        """
        用户信息模型的字符串表示
        返回:
            str: 用户信息模型的字符串表示
        """
        return f'<UserInfo {self.user_id}>'
    
    def to_dict(self):
        """
        将用户信息模型转换为字典
        返回:
            dict: 用户信息的字典表示
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
