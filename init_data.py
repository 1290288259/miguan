# -*- coding: utf-8 -*-
"""
数据初始化脚本
用于插入默认数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from database import db
from model import user_model, honeypot_model, log_model, malicious_ip_model, match_rule_model, attack_stats_model, block_history_model, permission_model

def init_data():
    """
    初始化数据
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    # 在应用上下文中操作数据
    with app.app_context():
        print("正在初始化数据...")
        
        # 创建默认管理员用户
        try:
            # 检查是否已有管理员用户
            admin_user = user_model.User.query.filter_by(username='administrator').first()
            if not admin_user:
                # 创建管理员用户
                admin_user = user_model.User(
                    username='administrator',
                    password='e10adc3949ba59abbe56e057f20f883e',  # 123456的MD5值
                    role=1  # 管理员角色
                )
                db.session.add(admin_user)
                db.session.commit()
                print("已创建默认管理员用户: administrator/123456")
            else:
                print("管理员用户已存在")
        except Exception as e:
            print(f"创建管理员用户时出错: {e}")
            db.session.rollback()
        
        # 创建默认权限数据
        try:
            # 检查是否已有权限数据
            permission_count = permission_model.Permission.query.count()
            if permission_count == 0:
                # 创建管理员权限
                admin_permissions = [
                    {'role': 1, 'path': '/', 'description': '管理员-首页'},
                    {'role': 1, 'path': '/dashboard', 'description': '管理员-仪表盘'},
                    {'role': 1, 'path': '/logs', 'description': '管理员-日志管理'},
                    {'role': 1, 'path': '/honeypots', 'description': '管理员-蜜罐管理'},
                    {'role': 1, 'path': '/rules', 'description': '管理员-规则管理'},
                    {'role': 1, 'path': '/ips', 'description': '管理员-IP管理'},
                    {'role': 1, 'path': '/statistics', 'description': '管理员-统计分析'},
                    {'role': 1, 'path': '/users', 'description': '管理员-用户管理'},
                    {'role': 1, 'path': '/settings', 'description': '管理员-系统设置'},
                ]
                
                # 创建普通用户权限
                user_permissions = [
                    {'role': 2, 'path': '/', 'description': '用户-首页'},
                    {'role': 2, 'path': '/dashboard', 'description': '用户-仪表盘'},
                    {'role': 2, 'path': '/logs', 'description': '用户-日志查看'},
                    {'role': 2, 'path': '/statistics', 'description': '用户-统计分析'},
                ]
                
                # 添加所有权限
                for perm_data in admin_permissions + user_permissions:
                    permission = permission_model.Permission(**perm_data)
                    db.session.add(permission)
                
                db.session.commit()
                print("已创建默认权限数据")
            else:
                print("权限数据已存在")
        except Exception as e:
            print(f"创建权限数据时出错: {e}")
            db.session.rollback()
        
        # 创建示例蜜罐数据
        try:
            # 检查是否已有蜜罐数据
            honeypot_count = honeypot_model.Honeypot.query.count()
            if honeypot_count == 0:
                # 创建示例蜜罐
                honeypots = [
                    {
                        'name': 'SSH蜜罐',
                        'type': 'SSH',
                        'port': 2222,
                        'ip_address': '0.0.0.0',
                        'status': 'stopped',
                        'description': '模拟SSH服务的蜜罐，用于捕获SSH攻击'
                    },
                    {
                        'name': 'HTTP蜜罐',
                        'type': 'HTTP',
                        'port': 80,
                        'ip_address': '0.0.0.0',
                        'status': 'running',
                        'description': '模拟HTTP服务的蜜罐，用于捕获Web攻击'
                    },
                    {
                        'name': 'FTP蜜罐',
                        'type': 'FTP',
                        'port': 21,
                        'ip_address': '0.0.0.0',
                        'status': 'stopped',
                        'description': '模拟FTP服务的蜜罐，用于捕获FTP攻击'
                    }
                ]
                
                # 添加所有蜜罐
                for hp_data in honeypots:
                    honeypot = honeypot_model.Honeypot(**hp_data)
                    db.session.add(honeypot)
                
                db.session.commit()
                print("已创建示例蜜罐数据")
            else:
                print("蜜罐数据已存在")
        except Exception as e:
            print(f"创建蜜罐数据时出错: {e}")
            db.session.rollback()
        
        # 创建示例匹配规则
        try:
            # 检查是否已有匹配规则数据
            rule_count = match_rule_model.MatchRule.query.count()
            if rule_count == 0:
                # 创建示例匹配规则
                rules = [
                    {
                        'name': 'SQL注入检测',
                        'attack_type': 'SQL注入',
                        'regex_pattern': r'(?i)(union|select|insert|update|delete|drop|exec)',
                        'threat_level': 'high',
                        'description': '检测常见的SQL注入攻击',
                        'match_field': 'raw_log',
                        'is_enabled': True,
                        'priority': 2,
                        'auto_block': True,
                        'block_duration': 24
                    },
                    {
                        'name': 'XSS攻击检测',
                        'attack_type': 'XSS',
                        'regex_pattern': r'(?i)(<script|javascript:|onload=|onerror=|alert\(|prompt\()|onclick=|onmouseover=',
                        'threat_level': 'medium',
                        'description': '检测跨站脚本攻击',
                        'match_field': 'raw_log',
                        'is_enabled': True,
                        'priority': 1,
                        'auto_block': False,
                        'block_duration': 0
                    },
                    {
                        'name': '目录遍历检测',
                        'attack_type': '目录遍历',
                        'regex_pattern': r'(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)',
                        'threat_level': 'medium',
                        'description': '检测目录遍历攻击',
                        'match_field': 'raw_log',
                        'is_enabled': True,
                        'priority': 3,
                        'auto_block': False,
                        'block_duration': 0
                    }
                ]
                
                # 添加所有规则
                for rule_data in rules:
                    rule = match_rule_model.MatchRule(**rule_data)
                    db.session.add(rule)
                
                db.session.commit()
                print("已创建示例匹配规则")
            else:
                print("匹配规则数据已存在")
        except Exception as e:
            print(f"创建匹配规则时出错: {e}")
            db.session.rollback()
        
        # 创建示例日志数据
        try:
            # 检查是否已有日志数据
            log_count = log_model.Log.query.count()
            if log_count == 0:
                # 获取蜜罐数据
                ssh_honeypot = honeypot_model.Honeypot.query.filter_by(type='SSH').first()
                http_honeypot = honeypot_model.Honeypot.query.filter_by(type='HTTP').first()
                
                if ssh_honeypot and http_honeypot:
                    # 创建示例日志
                    from datetime import datetime, timedelta
                    import random
                    
                    # 生成随机IP地址
                    def random_ip():
                        return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    
                    # 创建示例日志数据
                    for i in range(50):
                        # 随机选择蜜罐
                        honeypot = random.choice([ssh_honeypot, http_honeypot])
                        
                        # 随机生成攻击时间
                        attack_time = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                        
                        # 根据蜜罐类型生成不同的日志
                        if honeypot.type == 'SSH':
                            raw_log = f"Failed password for root from {random_ip()} port {random.randint(10000, 60000)} ssh2"
                            attack_type = random.choice(['暴力破解', '字典攻击', '凭证填充'])
                            protocol = 'SSH'
                            source_port = random.randint(10000, 60000)
                            target_port = 22
                        else:  # HTTP
                            raw_log = f"{random_ip()} - - [{attack_time.strftime('%d/%b/%Y:%H:%M:%S +0000')}] \"GET /admin.php?id=1' OR '1'='1 HTTP/1.1\" 200 1234"
                            attack_type = random.choice(['SQL注入', 'XSS', '目录遍历', '命令注入'])
                            protocol = 'HTTP'
                            source_port = random.randint(10000, 60000)
                            target_port = 80
                        
                        # 创建日志记录
                        log = log_model.Log(
                            honeypot_id=honeypot.id,
                            attacker_ip=random_ip(),
                            attack_time=attack_time,
                            raw_log=raw_log,
                            source_ip=random_ip(),
                            target_ip='192.168.1.100',
                            source_port=source_port,
                            target_port=target_port,
                            protocol=protocol,
                            user_agent=random.choice(['Mozilla/5.0', 'curl/7.68.0', 'python-requests/2.25.1']),
                            request_path=random.choice(['/admin.php', '/login.php', '/index.php', '/config.php']),
                            attack_type=attack_type,
                            attack_description=f"检测到{attack_type}攻击",
                            payload=random.choice(["' OR '1'='1", "<script>alert('XSS')</script>", "../../../etc/passwd"]),
                            threat_level=random.choice(['low', 'medium', 'high', 'critical']),
                            is_malicious=random.choice([True, False]),
                            is_blocked=random.choice([True, False]),
                            blocked_time=attack_time if random.choice([True, False]) else None,
                            notes=f"示例日志数据 {i+1}"
                        )
                        
                        db.session.add(log)
                    
                    db.session.commit()
                    print("已创建示例日志数据")
                else:
                    print("未找到蜜罐数据，跳过创建日志数据")
            else:
                print("日志数据已存在")
        except Exception as e:
            print(f"创建日志数据时出错: {e}")
            db.session.rollback()
        
        print("数据初始化完成！")

if __name__ == '__main__':
    init_data()