# -*- coding: utf-8 -*-
"""
模块模型
定义系统功能模块及用户-模块关联
"""

from database import db
from datetime import datetime

class Module(db.Model):
    """
    系统模块表
    """
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='模块ID')
    name = db.Column(db.String(50), nullable=False, comment='模块名称')
    title = db.Column(db.String(50), nullable=False, comment='模块标题(显示用)')
    path = db.Column(db.String(100), nullable=False, comment='前端路由路径')
    description = db.Column(db.String(200), nullable=True, comment='模块描述')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'path': self.path,
            'description': self.description
        }

class UserModule(db.Model):
    """
    用户-模块关联表
    """
    __tablename__ = 'user_modules'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False, comment='模块ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='授权时间')

    # 建立关系，方便查询
    # user = db.relationship('User', backref=db.backref('modules', lazy='dynamic'))
    # module = db.relationship('Module')
