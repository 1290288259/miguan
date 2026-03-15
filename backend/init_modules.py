# -*- coding: utf-8 -*-
"""
模块初始化脚本
用于初始化系统模块数据，并根据用户角色迁移权限
"""

from app import create_app
from database import db
from model.module_model import Module, UserModule
from model.user_model import User

def init_modules():
    app = create_app()
    with app.app_context():
        print("开始初始化模块数据...")
        
        # 确保表存在
        db.create_all()
        
        # 1. 清空模块表和用户模块关联表
        try:
            UserModule.query.delete()
            Module.query.delete()
            db.session.commit()
            print("已清空现有模块数据")
        except Exception as e:
            db.session.rollback()
            print(f"清空数据失败: {e}")
            
        # 2. 定义系统所有模块
        modules = [
            {"name": "dashboard", "title": "系统首页", "path": "/", "description": "系统概览与监控"},
            {"name": "log-query", "title": "日志查询", "path": "/log-query", "description": "查看系统日志"},
            {"name": "match-rule", "title": "匹配规则管理", "path": "/match-rule-management", "description": "管理入侵检测规则"},
            {"name": "honeypot", "title": "蜜罐管理", "path": "/honeypot-management", "description": "管理蜜罐服务"},
            {"name": "malicious-ip", "title": "恶意IP管理", "path": "/malicious-ip-management", "description": "管理封禁IP"},
            {"name": "ai-config", "title": "AI模型配置", "path": "/ai-config-management", "description": "配置AI分析模型"},
            {"name": "user-management", "title": "用户管理", "path": "/user-management", "description": "管理用户与权限"}
        ]
        
        # 3. 添加模块到数据库
        created_modules = {}
        for m in modules:
            module = Module(
                name=m["name"],
                title=m["title"],
                path=m["path"],
                description=m["description"]
            )
            db.session.add(module)
            db.session.flush() # 获取ID
            created_modules[m["name"]] = module
            
        # 4. 为现有用户分配初始模块权限
        users = User.query.all()
        for user in users:
            user_modules = []
            
            # 管理员(Role=1): 拥有所有权限
            if user.role == 1:
                user_modules = list(created_modules.values())
            
            # 普通用户(Role=2): 拥有基础权限
            elif user.role == 2:
                # 基础权限: 首页, 日志查询, 恶意IP管理 (参考 init_permissions.py)
                user_modules = [
                    created_modules["dashboard"],
                    created_modules["log-query"],
                    created_modules["malicious-ip"]
                ]
                
            # 创建关联
            for module in user_modules:
                um = UserModule(user_id=user.id, module_id=module.id)
                db.session.add(um)
                
        try:
            db.session.commit()
            print(f"成功初始化 {len(modules)} 个模块，并为 {len(users)} 个用户分配了权限")
        except Exception as e:
            db.session.rollback()
            print(f"初始化失败: {e}")
            
if __name__ == "__main__":
    init_modules()
