# -*- coding: utf-8 -*-
"""
权限模型
定义权限相关的数据库表结构
"""

from database import db
from utils.time_utils import get_beijing_time

class Permission(db.Model):
    """
    权限模型类
    存储系统权限信息，用于动态路由控制
    """
    __tablename__ = 'permissions'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='权限ID')
    
    # 权限值（1=管理员，2=普通用户）
    role = db.Column(db.Integer, nullable=False, comment='权限值')
    
    # 权限路径（用于前端路由匹配）
    path = db.Column(db.String(255), nullable=False, comment='权限路径')
    
    # 权限描述
    description = db.Column(db.String(255), nullable=True, comment='权限描述')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, onupdate=get_beijing_time, comment='更新时间')
    
    def __repr__(self):
        """
        权限模型的字符串表示
        返回:
            str: 权限模型的字符串表示
        """
        return f'<Permission {self.role}>'
    
    def to_dict(self):
        """
        将权限模型转换为字典
        返回:
            dict: 权限信息的字典表示
        """
        return {
            'id': self.id,
            'role': self.role,
            'path': self.path,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }