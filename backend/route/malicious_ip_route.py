# -*- coding: utf-8 -*-
"""
恶意IP路由
处理恶意IP相关的HTTP请求
"""

from flask import Blueprint, request, current_app
from utils.api_response import ApiResponse
from service.malicious_ip_service import MaliciousIPService
from functools import wraps
import jwt

# 创建恶意IP蓝图
malicious_ip_bp = Blueprint('malicious_ip', __name__, url_prefix='/api/malicious-ips')

def token_required(f):
    """
    JWT认证装饰器
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
        except jwt.ExpiredSignatureError:
            return ApiResponse.error("token已过期", 401)
        except jwt.InvalidTokenError:
            return ApiResponse.error("无效的token", 401)
        
        return f(*args, **kwargs)
    
    return decorated

@malicious_ip_bp.route('', methods=['GET'])
@token_required
def get_malicious_ips():
    """
    分页获取恶意IP列表
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 处理布尔值参数
        is_blocked_param = request.args.get('is_blocked')
        is_blocked = None
        if is_blocked_param is not None:
            if is_blocked_param.lower() == 'true':
                is_blocked = True
            elif is_blocked_param.lower() == 'false':
                is_blocked = False
                
        threat_level = request.args.get('threat_level')
        keyword = request.args.get('keyword')
        
        items, pagination = MaliciousIPService.get_malicious_ips(
            page=page,
            per_page=per_page,
            is_blocked=is_blocked,
            threat_level=threat_level,
            keyword=keyword
        )
        
        return ApiResponse.success(data={
            'items': items,
            'pagination': pagination
        })
        
    except Exception as e:
        return ApiResponse.error(f"获取列表失败: {str(e)}")

@malicious_ip_bp.route('/block', methods=['POST'])
@token_required
def block_ip():
    """
    封禁IP
    """
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        reason = data.get('reason')
        duration = data.get('duration') # 可选，封禁时长（秒）
        block_until = data.get('block_until') # 可选，封禁截止时间
        
        if not ip_address:
            return ApiResponse.error("IP地址不能为空")
            
        result = MaliciousIPService.block_ip(ip_address, reason, duration, block_until)
        
        if result['success']:
            return ApiResponse.success(message=result['message'])
        else:
            return ApiResponse.error(result['message'])
            
    except Exception as e:
        return ApiResponse.error(f"封禁操作失败: {str(e)}")

@malicious_ip_bp.route('/unblock', methods=['POST'])
@token_required
def unblock_ip():
    """
    解封IP
    """
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return ApiResponse.error("IP地址不能为空")
            
        result = MaliciousIPService.unblock_ip(ip_address)
        
        if result['success']:
            return ApiResponse.success(message=result['message'])
        else:
            return ApiResponse.error(result['message'])
            
    except Exception as e:
        return ApiResponse.error(f"解封操作失败: {str(e)}")

@malicious_ip_bp.route('/brute-force-config', methods=['GET'])
@token_required
def get_brute_force_config():
    """
    获取暴力破解自动封禁配置
    """
    try:
        from service.system_config_service import SystemConfigService
        config = SystemConfigService.get_brute_force_config()
        return ApiResponse.success(data=config)
    except Exception as e:
        return ApiResponse.error(f"获取配置失败: {str(e)}")

@malicious_ip_bp.route('/brute-force-config', methods=['PUT'])
@token_required
def update_brute_force_config():
    """
    更新暴力破解自动封禁配置
    """
    try:
        data = request.get_json()
        auto_block = data.get('auto_block', False)
        block_duration = data.get('block_duration', 24)
        from service.system_config_service import SystemConfigService
        SystemConfigService.set_brute_force_config(auto_block, block_duration)
        return ApiResponse.success(message="更新配置成功")
    except Exception as e:
        return ApiResponse.error(f"更新配置失败: {str(e)}")

@malicious_ip_bp.route('/add', methods=['POST'])
@token_required
def add_malicious_ip():
    """
    手动新增恶意IP
    """
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        threat_level = data.get('threat_level')
        notes = data.get('notes')
        block_immediately = data.get('block_immediately', True)
        reason = data.get('reason')
        block_until = data.get('block_until')
        
        if not ip_address:
            return ApiResponse.error("IP地址不能为空")
        if not threat_level:
            return ApiResponse.error("威胁等级不能为空")
            
        result = MaliciousIPService.add_manual_ip(
            ip_address=ip_address,
            threat_level=threat_level,
            notes=notes,
            block_immediately=block_immediately,
            reason=reason,
            block_until=block_until
        )
        
        if result['success']:
            return ApiResponse.success(message=result['message'])
        else:
            return ApiResponse.error(result['message'])
            
    except Exception as e:
        return ApiResponse.error(f"新增操作失败: {str(e)}")
