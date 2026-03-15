# -*- coding: utf-8 -*-
"""
日志路由
处理日志相关的HTTP请求
"""

from flask import Blueprint, request, current_app, make_response
from utils.api_response import ApiResponse
from service.log_service import LogService
from functools import wraps
import jwt

# 创建日志蓝图
log_bp = Blueprint('log', __name__, url_prefix='/api')

def token_required(f):
    """
    JWT认证装饰器
    验证请求头中的token是否有效
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头中获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return ApiResponse.error("无效的token格式", 401)
        
        # 如果没有token，返回错误
        if not token:
            return ApiResponse.error("需要认证token", 401)
        
        try:
            # 解码token，使用应用配置中的JWT密钥
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            # 这里可以添加额外的用户验证逻辑
        except jwt.ExpiredSignatureError:
            return ApiResponse.error("token已过期", 401)
        except jwt.InvalidTokenError:
            return ApiResponse.error("无效的token", 401)
        
        return f(*args, **kwargs)
    
    return decorated

@log_bp.route('/logs', methods=['GET'])
@token_required
def get_logs():
    """
    分页获取日志列表
    
    请求参数:
    - page: 页码，默认为1
    - per_page: 每页数量，默认为20
    - attack_type: 攻击类型过滤条件
    - threat_level: 威胁等级过滤条件
    - protocol: 协议类型过滤条件
    - start_time: 开始时间过滤条件
    - end_time: 结束时间过滤条件
    - keyword: 关键字，可以匹配多个字段
    
    返回:
    - 成功: 日志列表和分页信息
    - 失败: 错误信息
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        attack_type = request.args.get('attack_type')
        threat_level = request.args.get('threat_level')
        protocol = request.args.get('protocol')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        keyword = request.args.get('keyword')
        
        # 参数验证
        if page < 1:
            return ApiResponse.error("页码必须大于0")
        
        if per_page < 1 or per_page > 100:
            return ApiResponse.error("每页数量必须在1-100之间")
        
        # 调用服务层获取日志
        logs, pagination = LogService.get_logs(
            page=page, 
            per_page=per_page,
            attack_type=attack_type,
            threat_level=threat_level,
            protocol=protocol,
            start_time=start_time,
            end_time=end_time,
            keyword=keyword
        )
        
        # 检查是否有错误
        if 'error' in pagination:
            return ApiResponse.error(f"查询日志失败: {pagination['error']}")
        
        # 返回成功响应
        return ApiResponse.success({
            'logs': logs,
            'pagination': pagination
        }, "查询日志成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@log_bp.route('/logs/export', methods=['GET'])
@token_required
def export_logs():
    """
    导出日志
    
    请求参数:
    - attack_type: 攻击类型过滤条件
    - threat_level: 威胁等级过滤条件
    - protocol: 协议类型过滤条件
    - start_time: 开始时间过滤条件
    - end_time: 结束时间过滤条件
    - keyword: 关键字
    
    返回:
    - 成功: CSV文件
    - 失败: 错误信息
    """
    try:
        # 获取查询参数
        attack_type = request.args.get('attack_type')
        threat_level = request.args.get('threat_level')
        protocol = request.args.get('protocol')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        keyword = request.args.get('keyword')
        source_ip = request.args.get('source_ip')
        target_ip = request.args.get('target_ip')
        target_port = request.args.get('target_port', type=int)
        
        is_malicious_str = request.args.get('is_malicious')
        is_malicious = None
        if is_malicious_str == 'true':
            is_malicious = True
        elif is_malicious_str == 'false':
            is_malicious = False
            
        is_blocked_str = request.args.get('is_blocked')
        is_blocked = None
        if is_blocked_str == 'true':
            is_blocked = True
        elif is_blocked_str == 'false':
            is_blocked = False
        
        # 调用服务层导出日志
        csv_content, filename_or_error = LogService.export_logs(
            attack_type=attack_type,
            threat_level=threat_level,
            protocol=protocol,
            start_time=start_time,
            end_time=end_time,
            keyword=keyword,
            source_ip=source_ip,
            target_ip=target_ip,
            target_port=target_port,
            is_malicious=is_malicious,
            is_blocked=is_blocked
        )
        
        # 检查是否成功
        if csv_content is None:
            return ApiResponse.error(f"导出日志失败: {filename_or_error}")
        
        # 构建响应
        response = make_response(csv_content)
        
        # 添加BOM头以支持Excel正确打开UTF-8编码的CSV
        response.data = b'\xef\xbb\xbf' + response.data
        
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename_or_error}'
        
        return response
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@log_bp.route('/logs/<int:log_id>', methods=['GET'])
@token_required
def get_log_by_id(log_id):
    """
    根据ID获取单条日志
    
    参数:
    - log_id: 日志ID
    
    返回:
    - 成功: 日志信息
    - 失败: 错误信息
    """
    try:
        # 参数验证
        if log_id < 1:
            return ApiResponse.error("日志ID必须大于0")
        
        # 调用服务层获取日志
        log = LogService.get_log_by_id(log_id)
        
        # 检查是否找到日志
        if not log:
            return ApiResponse.error("未找到指定的日志", 404)
        
        # 返回成功响应
        return ApiResponse.success(log, "查询日志成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@log_bp.route('/logs/attack-types', methods=['GET'])
@token_required
def get_attack_types():
    """
    获取所有攻击类型
    
    返回:
    - 成功: 攻击类型列表
    - 失败: 错误信息
    """
    try:
        # 调用服务层获取攻击类型
        attack_types = LogService.get_attack_types()
        
        # 返回成功响应
        return ApiResponse.success(attack_types, "获取攻击类型成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@log_bp.route('/logs/threat-levels', methods=['GET'])
@token_required
def get_threat_levels():
    """
    获取所有威胁等级
    
    返回:
    - 成功: 威胁等级列表
    - 失败: 错误信息
    """
    try:
        # 调用服务层获取威胁等级
        threat_levels = LogService.get_threat_levels()
        
        # 返回成功响应
        return ApiResponse.success(threat_levels, "获取威胁等级成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@log_bp.route('/logs/statistics', methods=['GET'])
@token_required
def get_log_statistics():
    """
    获取日志统计信息
    
    返回:
    - 成功: 统计信息
    - 失败: 错误信息
    """
    try:
        # 调用服务层获取统计信息
        statistics = LogService.get_log_statistics()
        
        # 检查是否有错误
        if 'error' in statistics:
            return ApiResponse.error(f"获取统计信息失败: {statistics['error']}")
        
        # 返回成功响应
        return ApiResponse.success(statistics, "获取统计信息成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@log_bp.route('/logs/internal/upload', methods=['POST'])
def upload_log():
    """
    内部日志上传接口（供蜜罐脚本使用）
    不需要JWT认证
    
    请求参数:
    - honeypot_port: 蜜罐端口
    - attacker_ip: 攻击者IP
    - attacker_port: 攻击者端口
    - raw_log: 原始日志
    - payload: 攻击载荷
    - protocol: 协议
    - attack_type: 攻击类型
    
    返回:
    - 成功: 创建结果
    - 失败: 错误信息
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 参数验证
        if not data:
            return ApiResponse.error("请求数据不能为空")
        
        # 调用服务层创建日志
        result = LogService.create_log(data)
        
        # 检查是否有错误
        if 'error' in result:
            return ApiResponse.error(f"日志上传失败: {result['error']}")
        
        # 返回成功响应
        return ApiResponse.success(result, "日志上传成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)