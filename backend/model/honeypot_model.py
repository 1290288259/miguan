# -*- coding: utf-8 -*-
"""
蜜罐模型
定义蜜罐相关的数据库表结构
"""

from database import db
from datetime import datetime
from utils.time_utils import get_beijing_time

class Honeypot(db.Model):
    """
    蜜罐模型类
    存储蜜罐配置信息
    """
    __tablename__ = 'honeypots'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='蜜罐ID')
    
    # 蜜罐名称
    name = db.Column(db.String(100), nullable=False, comment='蜜罐名称')
    
    # 蜜罐类型（SSH、HTTP、FTP等）
    type = db.Column(db.String(50), nullable=False, comment='蜜罐类型')
    
    # 监听端口
    port = db.Column(db.Integer, nullable=False, comment='监听端口')
    
    # 绑定IP地址
    ip_address = db.Column(db.String(15), nullable=False, default='0.0.0.0', comment='绑定IP地址')
    
    # 状态（运行、停止等）
    status = db.Column(db.String(20), nullable=False, default='stopped', comment='蜜罐状态')
    
    # 描述
    description = db.Column(db.Text, nullable=True, comment='蜜罐描述')
    
    # 配置参数（JSON格式）
    config = db.Column(db.Text, nullable=True, comment='蜜罐配置参数')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=get_beijing_time, onupdate=get_beijing_time, comment='更新时间')
    
    # 子进程PID（用于服务重启后判断进程是否仍在运行）
    pid = db.Column(db.Integer, nullable=True, comment='蜜罐子进程PID')
    
    def __repr__(self):
        """
        蜜罐模型的字符串表示
        返回:
            str: 蜜罐模型的字符串表示
        """
        return f'<Honeypot {self.name}:{self.port}>'
    
    def to_dict(self):
        """
        将蜜罐模型转换为字典
        返回:
            dict: 蜜罐信息的字典表示
        """
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'port': self.port,
            'ip_address': self.ip_address,
            'status': self.status,
            'description': self.description,
            'config': self.config,
            'pid': self.pid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }