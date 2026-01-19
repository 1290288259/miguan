# -*- coding: utf-8 -*-
"""
用户路由
处理用户相关的HTTP请求
"""

from flask import request, jsonify
from functools import wraps
import jwt
from utils.api_response import ApiResponse
from service.user_service import create_user, create_admin_user, login_user, verify_jwt_token

def register():
    """
    用户注册接口
    
    接收参数:
        username: 账号
        password: 密码
        
    返回:
        JSON: 注册结果
    """
    try:
        # 获取请求中的JSON数据
        data = request.get_json()
        
        # 检查是否提供了账号和密码
        if not data or 'username' not in data or 'password' not in data:
            return ApiResponse.bad_request(message="请提供账号和密码")
        
        # 获取账号和密码
        username = data['username']
        password = data['password']
        
        # 获取用户角色，默认为2（普通用户）
        role = data.get('role', 2)
        
        # 验证角色值是否有效
        if role not in [1, 2]:
            return ApiResponse.bad_request(message="角色值无效，必须是1（管理员）或2（普通用户）")
        
        # 验证账号长度是否超过6位
        if len(username) < 6:
            return ApiResponse.bad_request(message="账号长度不能少于6位")
        
        # 验证密码长度是否超过6位
        if len(password) < 6:
            return ApiResponse.bad_request(message="密码长度不能少于6位")
        
        # 调用服务层创建用户
        result = create_user(username, password, role)
        
        # 根据服务层结果返回相应的响应
        if result['success']:
            return ApiResponse.created(
                data={'user_id': result['user_id']},
                message=result['message']
            )
        else:
            return ApiResponse.bad_request(message=result['message'])
            
    except Exception as e:
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")

def login():
    """
    用户登录接口
    
    接收参数:
        username: 账号
        password: 密码
        
    返回:
        JSON: 登录结果，包含JWT令牌
    """
    try:
        # 获取请求中的JSON数据
        data = request.get_json()
        
        # 检查是否提供了账号和密码
        if not data or 'username' not in data or 'password' not in data:
            return ApiResponse.bad_request(message="请提供账号和密码")
        
        # 获取账号和密码
        username = data['username']
        password = data['password']
        
        # 验证账号长度是否超过6位
        if len(username) < 6:
            return ApiResponse.bad_request(message="账号长度不能少于6位")
        
        # 验证密码长度是否超过6位
        if len(password) < 6:
            return ApiResponse.bad_request(message="密码长度不能少于6位")
        
        # 调用服务层进行用户登录验证
        result = login_user(username, password)
        
        # 根据服务层结果返回相应的响应
        if result['success']:
            return ApiResponse.success(
                data={
                    'access_token': result['access_token'],
                    'refresh_token': result['refresh_token'],
                    'user': result['user']
                },
                message=result['message']
            )
        else:
            return ApiResponse.unauthorized(message=result['message'])
            
    except Exception as e:
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")

def token_required(f):
    """
    JWT令牌验证装饰器
    
    参数:
        f: 被装饰的函数
        
    返回:
        function: 装饰后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头中获取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return ApiResponse.unauthorized(message="令牌格式错误，应为'Bearer <token>'")
        
        # 检查令牌是否存在
        if not token:
            return ApiResponse.unauthorized(message="缺少访问令牌")
        
        # 验证令牌
        result = verify_jwt_token(token)
        
        if not result['success']:
            return ApiResponse.unauthorized(message=result['message'])
        
        # 将令牌载荷添加到请求上下文中
        request.current_user = result['payload']
        
        return f(*args, **kwargs)
    
    return decorated

def get_current_user():
    """
    获取当前用户信息
    
    返回:
        JSON: 当前用户信息
    """
    try:
        # 使用token_required装饰器验证令牌
        @token_required
        def _get_current_user():
            # 从请求上下文中获取用户信息
            user_info = request.current_user
            
            # 返回用户信息
            return ApiResponse.success(
                data={
                    'id': user_info['user_id'],
                    'username': user_info['username'],
                    'role': user_info['role']
                },
                message="获取用户信息成功"
            )
        
        return _get_current_user()
    except Exception as e:
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")

def create_admin():
    """
    创建管理员用户接口
    
    接收参数:
        username: 管理员账号
        password: 管理员密码
        
    返回:
        JSON: 创建结果
    """
    try:
        # 获取请求中的JSON数据
        data = request.get_json()
        
        # 检查是否提供了账号和密码
        if not data or 'username' not in data or 'password' not in data:
            return ApiResponse.bad_request(message="请提供管理员账号和密码")
        
        # 获取账号和密码
        username = data['username']
        password = data['password']
        
        # 验证账号长度是否超过6位
        if len(username) < 6:
            return ApiResponse.bad_request(message="账号长度不能少于6位")
        
        # 验证密码长度是否超过6位
        if len(password) < 6:
            return ApiResponse.bad_request(message="密码长度不能少于6位")
        
        # 调用服务层创建管理员用户
        result = create_admin_user(username, password)
        
        # 根据服务层结果返回相应的响应
        if result['success']:
            return ApiResponse.created(
                data={'user_id': result['user_id']},
                message=result['message']
            )
        else:
            return ApiResponse.bad_request(message=result['message'])
            
    except Exception as e:
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")