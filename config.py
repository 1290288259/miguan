# -*- coding: utf-8 -*-
"""
Flask应用程序配置文件
包含应用程序的各种配置参数，包括开发环境、生产环境和测试环境的配置
"""

import os

class Config:
    """
    基础配置类
    包含所有环境共享的配置参数
    """
    # 安全配置 - 密钥，用于会话加密和CSRF保护
    # 在生产环境中应该使用环境变量设置
    SECRET_KEY = os.environ.get('SECRET_KEY') or '这是一个难以猜测的密钥，请更改它'
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-请更改它'
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 访问令牌过期时间（24小时）
    JWT_REFRESH_TOKEN_EXPIRES = 60 * 60 * 24 * 7  # 刷新令牌过期时间（7天）
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 限制上传文件大小为16MB
    
    # 数据库配置
    # 使用MySQL数据库
    DATABASE_URI = f'mysql+pymysql://root:123456@localhost:3306/bishe?charset=utf8mb4'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭SQLAlchemy的修改事件系统，提高性能
    SQLALCHEMY_ECHO = False  # 关闭SQLAlchemy的日志输出
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # 连接池大小
        'pool_recycle': 120,  # 连接回收时间(秒)
        'pool_pre_ping': True  # 连接池预检查
    }
    
    # 邮件配置（如果需要）
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # 分页配置
    POSTS_PER_PAGE = 10
    
    # 语言配置
    LANGUAGES = ['zh', 'en']
    
    # 应用程序信息
    APP_NAME = 'Flask标准框架'
    VERSION = '1.0.0'
    AUTHOR = '开发者'
    CONTACT_EMAIL = 'developer@example.com'

class DevelopmentConfig(Config):
    """
    开发环境配置
    继承自Config类，添加开发环境特有的配置
    """
    DEBUG = True  # 开启调试模式，显示详细错误信息
    # 开发环境数据库配置
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or Config.DATABASE_URI

class TestingConfig(Config):
    """
    测试环境配置
    继承自Config类，添加测试环境特有的配置
    """
    TESTING = True  # 开启测试模式
    # 禁用CSRF保护，便于测试
    WTF_CSRF_ENABLED = False
    # 测试环境数据库配置
    # SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or Config.DATABASE_URI

class ProductionConfig(Config):
    """
    生产环境配置
    继承自Config类，添加生产环境特有的配置
    """
    DEBUG = False  # 关闭调试模式，提高安全性
    # 生产环境数据库配置
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or Config.DATABASE_URI

# 配置字典，根据环境变量选择相应的配置类
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # 默认使用开发环境配置
}