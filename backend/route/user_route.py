# -*- coding: utf-8 -*-
"""
用户路由
处理用户相关的HTTP请求
"""

from flask import request, jsonify, Blueprint
from functools import wraps
import jwt
from utils.api_response import ApiResponse
from service.user_service import create_user, create_admin_user, login_user, verify_jwt_token, get_user_detail, update_user_detail, get_user_list, delete_user, admin_update_user, get_all_permissions, get_all_modules

# 创建用户路由蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/register', methods=['POST'])
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
        
        # 获取可选的用户信息
        phone = data.get('phone')
        email = data.get('email')
        
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
            
        # 验证手机号格式（简单验证）
        if phone and len(phone) < 11:
             return ApiResponse.bad_request(message="手机号格式不正确")
             
        # 验证邮箱格式（简单验证）
        if email and '@' not in email:
             return ApiResponse.bad_request(message="邮箱格式不正确")
        
        # 调用服务层创建用户
        result = create_user(username, password, role, phone=phone, email=email)
        
        # 根据服务层结果返回相应的响应
        if result['success']:
            return ApiResponse.created(
                data={'user_id': result['user_id']},
                message=result['message']
            )
        else:
            print(f"Registration failed for user {username}: {result['message']}")
            return ApiResponse.bad_request(message=result['message'])
            
    except Exception as e:
        print(f"Registration exception: {str(e)}")
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")

@user_bp.route('/login', methods=['POST'])
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

def admin_required(f):
    """
    管理员权限验证装饰器
    必须先使用 @token_required
    
    参数:
        f: 被装饰的函数
        
    返回:
        function: 装饰后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 检查是否已获取用户信息
        if not hasattr(request, 'current_user') or not request.current_user:
            return ApiResponse.unauthorized(message="需要登录")
            
        # 检查是否是管理员 (role=1)
        if request.current_user.get('role') != 1:
            return ApiResponse.forbidden(message="需要管理员权限")
        
        return f(*args, **kwargs)
    
    return decorated

@user_bp.route('/permissions', methods=['GET'])
@token_required
@admin_required
def get_permissions():
    """
    获取所有权限列表
    """
    try:
        result = get_all_permissions()
        if result['success']:
            return ApiResponse.success(data=result['data'])
        else:
            return ApiResponse.server_error(message=result['message'])
    except Exception as e:
        return ApiResponse.server_error(message=str(e))

@user_bp.route('/list', methods=['GET'])
@token_required
@admin_required
def get_users():
    """
    获取用户列表（管理员）
    
    参数:
        page: 页码
        size: 每页数量
        keyword: 搜索关键词
        role: 角色ID
    """
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        keyword = request.args.get('keyword')
        role = request.args.get('role', type=int)
        
        result = get_user_list(page, size, keyword, role)
        
        if result['success']:
            return ApiResponse.success(data=result['data'])
        else:
            return ApiResponse.server_error(message=result['message'])
    except Exception as e:
        return ApiResponse.server_error(message=str(e))

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user_route(user_id):
    """
    删除用户（管理员）
    """
    try:
        # 防止删除自己
        if user_id == request.current_user['user_id']:
            return ApiResponse.bad_request(message="不能删除当前登录账号")
            
        result = delete_user(user_id)
        
        if result['success']:
            return ApiResponse.success(message=result['message'])
        else:
            return ApiResponse.bad_request(message=result['message'])
    except Exception as e:
        return ApiResponse.server_error(message=str(e))

@user_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user_route(user_id):
    """
    更新用户信息（管理员）
    """
    try:
        data = request.get_json()
        if not data:
            return ApiResponse.bad_request(message="没有提供更新数据")
            
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        phone = data.get('phone')
        email = data.get('email')
        module_ids = data.get('module_ids')
        
        result = admin_update_user(user_id, username, password, role, phone, email, module_ids)
        
        if result['success']:
            return ApiResponse.success(message=result['message'])
        else:
            return ApiResponse.bad_request(message=result['message'])
    except Exception as e:
        return ApiResponse.server_error(message=str(e))

@user_bp.route('/add', methods=['POST'])
@token_required
@admin_required
def add_user_route():
    """
    添加用户（管理员）
    """
    try:
        data = request.get_json()
        if not data:
            return ApiResponse.bad_request(message="没有提供用户数据")
            
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 2)
        phone = data.get('phone')
        email = data.get('email')
        module_ids = data.get('module_ids')
        
        if not username or not password:
            return ApiResponse.bad_request(message="账号和密码必填")
            
        result = create_user(username, password, role, phone, email, module_ids)
        
        if result['success']:
            return ApiResponse.created(data={'user_id': result['user_id']}, message="用户创建成功")
        else:
            return ApiResponse.bad_request(message=result['message'])
    except Exception as e:
        return ApiResponse.server_error(message=str(e))

@user_bp.route('/modules', methods=['GET'])
@token_required
def get_modules_route():
    """
    获取所有模块列表（已登录用户均可获取，用于前端展示）
    """
    try:
        result = get_all_modules()
        if result['success']:
            return ApiResponse.success(data=result['data'], message="获取模块列表成功")
        else:
            return ApiResponse.server_error(message=result['message'])
    except Exception as e:
        return ApiResponse.server_error(message=str(e))

@user_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """
    获取当前用户信息
    
    返回:
        JSON: 当前用户信息
    """
    try:
        # 从请求上下文中获取用户信息
        token_info = request.current_user
        user_id = token_info['user_id']
        
        # 获取用户详细信息
        result = get_user_detail(user_id)
        
        if result['success']:
            return ApiResponse.success(
                data=result['data'],
                message="获取用户信息成功"
            )
        else:
            return ApiResponse.bad_request(message=result['message'])
    except Exception as e:
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")

@user_bp.route('/me', methods=['PUT'])
@token_required
def update_current_user():
    """
    更新当前用户信息
    
    接收参数:
        phone: 手机号 (可选)
        email: 邮箱 (可选)
        
    返回:
        JSON: 更新结果
    """
    try:
        # 从请求上下文中获取用户信息
        token_info = request.current_user
        user_id = token_info['user_id']
        
        # 获取请求中的JSON数据
        data = request.get_json()
        if not data:
            return ApiResponse.bad_request(message="没有提供更新数据")
            
        phone = data.get('phone')
        email = data.get('email')
        password = data.get('password')
        old_password = data.get('old_password')
        
        # 验证手机号格式（简单验证）
        if phone and len(phone) < 11:
            return ApiResponse.bad_request(message="手机号格式不正确")
            
        # 验证邮箱格式（简单验证）
        if email and '@' not in email:
            return ApiResponse.bad_request(message="邮箱格式不正确")
        
        # 验证新密码长度
        if password and len(password) < 6:
            return ApiResponse.bad_request(message="新密码长度不能少于6位")

        # 调用服务层更新用户信息
        result = update_user_detail(user_id, phone=phone, email=email, password=password, old_password=old_password)
        
        if result['success']:
            return ApiResponse.success(message=result['message'])
        else:
            return ApiResponse.bad_request(message=result['message'])
    except Exception as e:
        # 处理异常情况
        return ApiResponse.server_error(message=f"服务器内部错误: {str(e)}")

@user_bp.route('/create_admin', methods=['POST'])
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