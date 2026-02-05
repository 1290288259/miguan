# -*- coding: utf-8 -*-
"""
数据库初始化模块
用于创建数据库连接和初始化数据库表
"""

from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from flask_migrate import Migrate

# 创建SQLAlchemy实例
db = SQLAlchemy()

# 创建Migrate实例，用于数据库迁移
migrate = Migrate()

def init_db(app):
    """
    初始化数据库
    
    参数:
        app: Flask应用实例
    """
    # 将SQLAlchemy实例与应用关联
    db.init_app(app)
    
    # 初始化Flask-Migrate
    migrate.init_app(app, db)
    
    # 在应用上下文中导入所有模型类，确保它们被注册
    with app.app_context():
        # 导入所有模型类，确保它们被注册
        from model import user_model, honeypot_model, log_model, malicious_ip_model, match_rule_model, attack_stats_model, block_history_model, permission_model, user_info_model, ai_config_model
        
        # 打印所有模型类，用于调试
        print("正在导入的模型类:")
        print("User:", user_model.User)
        print("Honeypot:", honeypot_model.Honeypot)
        print("Log:", log_model.Log)
        print("MaliciousIP:", malicious_ip_model.MaliciousIP)
        print("MatchRule:", match_rule_model.MatchRule)
        print("AttackStats:", attack_stats_model.AttackStats)
        print("BlockHistory:", block_history_model.BlockHistory)
        print("Permission:", permission_model.Permission)
        print("UserInfo:", user_info_model.UserInfo)
        print("AIConfig:", ai_config_model.AIConfig)
        
        print("数据库初始化完成！使用Flask-Migrate进行数据库迁移管理。")