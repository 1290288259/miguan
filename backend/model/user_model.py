# -*- coding: utf-8 -*-
"""
用户模型
定义用户相关的数据库表结构
"""

from database import db

class User(db.Model):
    """
    用户模型类
    存储系统用户信息
    """
    __tablename__ = 'users'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    
    # 账号
    username = db.Column(db.String(80), unique=True, nullable=False, comment='账号')
    
    # 密码（存储加密后的密码）
    password = db.Column(db.String(255), nullable=False, comment='密码')
    
    # 权限（1=管理员，2=普通用户）
    role = db.Column(db.Integer, nullable=False, default=2, comment='权限角色')

    # 失败登录尝试次数
    failed_login_attempts = db.Column(db.Integer, default=0, comment='连续登录失败次数')
    
    # 账户锁定截止时间
    locked_until = db.Column(db.DateTime, nullable=True, comment='账户锁定截止时间')
    
    def __repr__(self):
        """
        用户模型的字符串表示
        返回:
            str: 用户模型的字符串表示
        """
        return f'<User {self.username}>'
    
    def to_dict(self):
        """
        将用户模型转换为字典
        返回:
            dict: 用户信息的字典表示
        """
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }