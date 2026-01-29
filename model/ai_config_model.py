# -*- coding: utf-8 -*-
"""
AI配置模型
定义AI配置相关的数据库表结构
"""

from database import db
from datetime import datetime

class AIConfig(db.Model):
    """
    AI配置模型类
    存储AI API的配置信息
    """
    __tablename__ = 'ai_configs'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='配置ID')
    
    # 配置名称
    name = db.Column(db.String(100), nullable=False, unique=True, comment='配置名称')
    
    # API地址
    api_url = db.Column(db.String(255), nullable=False, comment='API地址')
    
    # 模型名称
    model_name = db.Column(db.String(100), nullable=False, comment='模型名称')
    
    # API密钥 (可选)
    api_key = db.Column(db.String(255), nullable=True, comment='API密钥')
    
    # 提供商 (ollama, openai等)
    provider = db.Column(db.String(50), nullable=False, default='ollama', comment='提供商')
    
    # 是否启用
    is_active = db.Column(db.Boolean, nullable=False, default=False, comment='是否启用')
    
    # 描述
    description = db.Column(db.Text, nullable=True, comment='描述')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def to_dict(self):
        """
        转换为字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'api_url': self.api_url,
            'model_name': self.model_name,
            'api_key': self.api_key,
            'provider': self.provider,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
