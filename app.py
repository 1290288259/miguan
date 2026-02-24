# -*- coding: utf-8 -*-
"""
Flask应用程序主文件
这是应用程序的入口点，负责创建和配置Flask应用实例
"""

from flask import Flask, request, jsonify
import os

# 导入配置文件
from config import Config

# 导入CORS扩展，用于处理跨域请求
from flask_cors import CORS

# 导入数据库初始化模块
from database import db, init_db

# 导入Flask-Migrate用于数据库迁移
from flask_migrate import Migrate

# 导入测试路由蓝图
from route.test_route import test_bp

# 导入用户路由蓝图
from route.user_route import user_bp

# 导入日志路由蓝图
from route.log_route import log_bp

# 导入匹配规则路由蓝图
from route.match_rule_route import match_rule_bp

# 导入蜜罐路由蓝图
from route.honeypot_route import honeypot_bp

# 导入恶意IP路由蓝图
from route.malicious_ip_route import malicious_ip_bp

# 导入仪表盘路由蓝图
from routes.dashboard_routes import dashboard_bp

# 导入蜜罐服务用于初始化
from service.honeypot_service import HoneypotService

# 导入AI分析服务用于初始化
from service.ai_analysis_service import AIAnalysisService

# 导入AI配置路由蓝图
from route.ai_config_route import ai_config_bp

# 导入恶意IP服务用于初始化
from service.malicious_ip_service import MaliciousIPService

# 导入API响应封装
from utils.api_response import ApiResponse
import threading
import time

def start_expired_ip_check(app):
    """
    启动过期IP检查线程
    """
    def check_loop():
        while True:
            try:
                MaliciousIPService.check_expired_blocks(app)
            except Exception as e:
                print(f"IP检查线程出错: {str(e)}")
            # 每60秒检查一次
            time.sleep(60)
            
    # 设置为守护线程，随主线程退出而退出
    check_thread = threading.Thread(target=check_loop, daemon=True)
    check_thread.start()
    print("已启动恶意IP过期自动解封检查线程")

def create_app():
    """
    应用工厂函数
    用于创建和配置Flask应用实例
    
    返回:
        Flask: 配置好的Flask应用实例
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 确保上传文件夹存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 配置CORS跨域资源共享
    # 允许所有域的跨域请求，生产环境中应该指定具体的域名
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # 允许所有来源，生产环境中应该指定具体域名
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 允许的HTTP方法
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]  # 允许的请求头
        }
    })
    
    # 初始化数据库
    init_db(app)
      
    # 定义根路径API
    @app.route('/')
    def api_root():
        """
        根路径API
        返回API基本信息
        
        返回:
            dict: 包含API信息的JSON响应
        """
        return ApiResponse.success(
            data={
                'version': '1.0.0',
                'endpoints': [
                        '/api/test/hello - 测试问候API',
                        '/api/test/hello_with_name - 带名字的测试问候API',
                        '/api/user/register - 用户注册API',
                        '/api/user/create_admin - 创建管理员API',
                        '/api/user/login - 用户登录API',
                        '/api/user/me - 获取当前用户信息API',
                        '/api/logs - 分页获取日志列表API',
                        '/api/logs/<id> - 获取单条日志API',
                        '/api/logs/attack-types - 获取攻击类型API',
                        '/api/logs/threat-levels - 获取威胁等级API',
                        '/api/logs/statistics - 获取日志统计信息API',
                        '/api/match-rules - 分页获取匹配规则列表API',
                        '/api/match-rules/<id> - 获取单条匹配规则API',
                        '/api/match-rules/<id>/toggle - 切换匹配规则状态API',
                        '/api/match-rules/attack-types - 获取攻击类型API',
                        '/api/match-rules/threat-levels - 获取威胁等级API'
                    ]
            },
            message="欢迎使用Flask纯后端API"
        )
    
    # 错误处理 - 404错误
    @app.errorhandler(404)
    def not_found_error(error):
        """
        处理404错误
        返回JSON格式的错误信息
        
        参数:
            error: 错误信息
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.not_found(message="API端点不存在")
    
    # 错误处理 - 500错误
    @app.errorhandler(500)
    def internal_error(error):
        """
        处理500错误
        返回JSON格式的错误信息
        
        参数:
            error: 错误信息
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.server_error(message="服务器内部错误")
    
    return app

# 创建应用实例
app = create_app()

# 注册测试路由蓝图
app.register_blueprint(test_bp)

# 注册用户路由蓝图
app.register_blueprint(user_bp)

# 注册日志路由蓝图
app.register_blueprint(log_bp)

# 注册匹配规则路由蓝图
app.register_blueprint(match_rule_bp)

# 注册蜜罐路由蓝图
app.register_blueprint(honeypot_bp)

# 注册恶意IP路由蓝图
app.register_blueprint(malicious_ip_bp)

# 注册仪表盘路由蓝图
app.register_blueprint(dashboard_bp)

# 注册AI配置路由蓝图
app.register_blueprint(ai_config_bp)

# 如果直接运行此文件，则启动开发服务器
if __name__ == '__main__':
    # 初始化蜜罐服务（自动启动状态为running的蜜罐）
    with app.app_context():
        print("正在初始化蜜罐服务...")
        HoneypotService.init_honeypots()
        
    # 初始化AI模型 (传入app实例以便在线程中使用上下文)
    AIAnalysisService.init_model(app)

    # 启动过期IP检查线程
    start_expired_ip_check(app)

    # 启动Flask开发服务器
    # debug=False表示关闭调试模式，避免watchdog兼容性问题
    # use_reloader=False表示关闭自动重新加载功能
    # host='0.0.0.0'表示可以从任何IP访问
    # port=5000是默认端口号
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)