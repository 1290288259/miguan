# -*- coding: utf-8 -*-
"""
蜜罐路由
处理蜜罐相关的HTTP请求
"""

from flask import Blueprint, request
from utils.api_response import ApiResponse
from service.honeypot_service import HoneypotService
from functools import wraps
import jwt
from flask import current_app

# 创建蜜罐蓝图
honeypot_bp = Blueprint('honeypot', __name__, url_prefix='/api')

def token_required(f):
    """
    JWT认证装饰器 (复用)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return ApiResponse.error("无效的token格式", 401)
        
        if not token:
            return ApiResponse.error("需要认证token", 401)
        
        try:
            jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        except Exception:
            return ApiResponse.error("无效的token或已过期", 401)
        
        return f(*args, **kwargs)
    return decorated

@honeypot_bp.route('/honeypots', methods=['GET'])
@token_required
def get_honeypots():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        type_ = request.args.get('type')
        status = request.args.get('status')
        keyword = request.args.get('keyword')
        
        data, pagination = HoneypotService.get_honeypots(page, per_page, type_, status, keyword)
        return ApiResponse.success({'honeypots': data, 'pagination': pagination})
    except Exception as e:
        return ApiResponse.error(str(e))

@honeypot_bp.route('/honeypots', methods=['POST'])
@token_required
def create_honeypot():
    try:
        data = request.get_json()
        result = HoneypotService.create_honeypot(data)
        if 'error' in result:
            return ApiResponse.error(result['error'])
        return ApiResponse.success(result)
    except Exception as e:
        return ApiResponse.error(str(e))

@honeypot_bp.route('/honeypots/<int:hp_id>', methods=['PUT'])
@token_required
def update_honeypot(hp_id):
    try:
        data = request.get_json()
        result = HoneypotService.update_honeypot(hp_id, data)
        if 'error' in result:
            return ApiResponse.error(result['error'])
        return ApiResponse.success(result)
    except Exception as e:
        return ApiResponse.error(str(e))

@honeypot_bp.route('/honeypots/<int:hp_id>', methods=['DELETE'])
@token_required
def delete_honeypot(hp_id):
    try:
        result = HoneypotService.delete_honeypot(hp_id)
        if 'error' in result:
            return ApiResponse.error(result['error'])
        return ApiResponse.success(result)
    except Exception as e:
        return ApiResponse.error(str(e))

@honeypot_bp.route('/honeypots/<int:hp_id>/start', methods=['POST'])
@token_required
def start_honeypot(hp_id):
    try:
        result = HoneypotService.start_honeypot(hp_id)
        if 'error' in result:
            return ApiResponse.error(result['error'])
        return ApiResponse.success(result)
    except Exception as e:
        return ApiResponse.error(str(e))

@honeypot_bp.route('/honeypots/<int:hp_id>/stop', methods=['POST'])
@token_required
def stop_honeypot(hp_id):
    try:
        result = HoneypotService.stop_honeypot(hp_id)
        if 'error' in result:
            return ApiResponse.error(result['error'])
        return ApiResponse.success(result)
    except Exception as e:
        return ApiResponse.error(str(e))

@honeypot_bp.route('/honeypots/<int:hp_id>/health', methods=['GET'])
@token_required
def check_honeypot_health(hp_id):
    try:
        result = HoneypotService.health_check(hp_id)
        if 'error' in result:
            return ApiResponse.error(result['error'])
        return ApiResponse.success(result)
    except Exception as e:
        return ApiResponse.error(str(e))
