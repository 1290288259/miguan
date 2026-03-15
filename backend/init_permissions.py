# -*- coding: utf-8 -*-
"""
权限初始化脚本
用于初始化数据库中的权限数据
"""

from app import create_app
from database import db
from model.permission_model import Permission

def init_permissions():
    """
    初始化权限数据
    
    普通用户(Role=2)只能访问:
    1. 系统首页 (/)
    2. 日志查询 (/log-query)
    3. 恶意IP管理 (/malicious-ip-management)
    
    管理员(Role=1)可以访问所有功能
    """
    app = create_app()
    
    with app.app_context():
        print("开始初始化权限数据...")
        
        # 清空现有权限数据
        try:
            Permission.query.delete()
            db.session.commit()
            print("已清空现有权限数据")
        except Exception as e:
            db.session.rollback()
            print(f"清空数据失败: {e}")
            
        # 定义权限列表
        permissions = [
            # 普通用户权限 (Role=2)
            {"role": 2, "path": "/", "description": "系统首页"},
            {"role": 2, "path": "/log-query", "description": "日志查询"},
            {"role": 2, "path": "/malicious-ip-management", "description": "恶意IP管理"},
            
            # 管理员权限 (Role=1) - 包含所有功能
            {"role": 1, "path": "/", "description": "系统首页"},
            {"role": 1, "path": "/log-query", "description": "日志查询"},
            {"role": 1, "path": "/match-rule-management", "description": "匹配规则管理"},
            {"role": 1, "path": "/honeypot-management", "description": "蜜罐管理"},
            {"role": 1, "path": "/malicious-ip-management", "description": "恶意IP管理"},
            {"role": 1, "path": "/ai-config-management", "description": "AI模型配置"},
        ]
        
        # 批量添加权限
        count = 0
        for p in permissions:
            perm = Permission(
                role=p["role"],
                path=p["path"],
                description=p["description"]
            )
            db.session.add(perm)
            count += 1
            
        try:
            db.session.commit()
            print(f"成功添加 {count} 条权限记录")
        except Exception as e:
            db.session.rollback()
            print(f"添加权限失败: {e}")
            
    print("权限初始化完成!")

if __name__ == "__main__":
    init_permissions()
