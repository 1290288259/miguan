# -*- coding: utf-8 -*-
"""
匹配规则路由
处理匹配规则相关的HTTP请求
"""

from flask import Blueprint, request, current_app
from utils.api_response import ApiResponse
from service.match_rule_service import MatchRuleService
from functools import wraps
import jwt

# 创建匹配规则蓝图
match_rule_bp = Blueprint('match_rule', __name__, url_prefix='/api')

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

@match_rule_bp.route('/match-rules', methods=['GET'])
@token_required
def get_rules():
    """
    分页获取匹配规则列表
    
    请求参数:
    - page: 页码，默认为1
    - per_page: 每页数量，默认为20
    - attack_type: 攻击类型过滤条件
    - threat_level: 威胁等级过滤条件
    - is_enabled: 是否启用过滤条件
    - keyword: 关键字，可以匹配多个字段
    
    返回:
    - 成功: 规则列表和分页信息
    - 失败: 错误信息
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        attack_type = request.args.get('attack_type')
        threat_level = request.args.get('threat_level')
        is_enabled = request.args.get('is_enabled')
        keyword = request.args.get('keyword')
        
        # 参数验证
        if page < 1:
            return ApiResponse.error("页码必须大于0")
        
        if per_page < 1 or per_page > 100:
            return ApiResponse.error("每页数量必须在1-100之间")
        
        # 转换is_enabled参数
        if is_enabled is not None:
            is_enabled = is_enabled.lower() in ['true', '1', 'yes']
        
        # 调用服务层获取规则
        rules, pagination = MatchRuleService.get_rules(
            page=page, 
            per_page=per_page,
            attack_type=attack_type,
            threat_level=threat_level,
            is_enabled=is_enabled,
            keyword=keyword
        )
        
        # 检查是否有错误
        if 'error' in pagination:
            return ApiResponse.error(f"查询匹配规则失败: {pagination['error']}")
        
        # 返回成功响应
        return ApiResponse.success({
            'rules': rules,
            'pagination': pagination
        }, "查询匹配规则成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules/<int:rule_id>', methods=['GET'])
@token_required
def get_rule_by_id(rule_id):
    """
    根据ID获取单条匹配规则
    
    参数:
    - rule_id: 规则ID
    
    返回:
    - 成功: 规则信息
    - 失败: 错误信息
    """
    try:
        # 参数验证
        if rule_id < 1:
            return ApiResponse.error("规则ID必须大于0")
        
        # 调用服务层获取规则
        rule = MatchRuleService.get_rule_by_id(rule_id)
        
        # 检查是否找到规则
        if not rule:
            return ApiResponse.error("未找到指定的匹配规则", 404)
        
        # 返回成功响应
        return ApiResponse.success(rule, "查询匹配规则成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules', methods=['POST'])
@token_required
def create_rule():
    """
    创建匹配规则
    
    请求参数:
    - name: 规则名称
    - attack_type: 攻击类型
    - regex_pattern: 正则表达式
    - threat_level: 威胁等级
    - description: 规则描述
    - match_field: 匹配字段
    - is_enabled: 是否启用
    - priority: 规则优先级
    - auto_block: 是否自动封禁
    - block_duration: 封禁时长
    - created_by: 创建者ID
    
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
        
        name = data.get('name')
        attack_type = data.get('attack_type')
        regex_pattern = data.get('regex_pattern')
        
        if not name:
            return ApiResponse.error("规则名称不能为空")
        
        if not attack_type:
            return ApiResponse.error("攻击类型不能为空")
        
        if not regex_pattern:
            return ApiResponse.error("正则表达式不能为空")
        
        # 调用服务层创建规则
        result = MatchRuleService.create_rule(data)
        
        # 检查是否有错误
        if 'error' in result:
            return ApiResponse.error(f"创建匹配规则失败: {result['error']}")
        
        # 返回成功响应
        return ApiResponse.success(result, "匹配规则创建成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules/<int:rule_id>', methods=['PUT'])
@token_required
def update_rule(rule_id):
    """
    更新匹配规则
    
    参数:
    - rule_id: 规则ID
    
    请求参数:
    - name: 规则名称
    - attack_type: 攻击类型
    - regex_pattern: 正则表达式
    - threat_level: 威胁等级
    - description: 规则描述
    - match_field: 匹配字段
    - is_enabled: 是否启用
    - priority: 规则优先级
    - auto_block: 是否自动封禁
    - block_duration: 封禁时长
    
    返回:
    - 成功: 更新结果
    - 失败: 错误信息
    """
    try:
        # 参数验证
        if rule_id < 1:
            return ApiResponse.error("规则ID必须大于0")
        
        # 获取请求数据
        data = request.get_json()
        
        # 参数验证
        if not data:
            return ApiResponse.error("请求数据不能为空")
        
        # 调用服务层更新规则
        result = MatchRuleService.update_rule(rule_id, data)
        
        # 检查是否有错误
        if 'error' in result:
            return ApiResponse.error(f"更新匹配规则失败: {result['error']}")
        
        # 返回成功响应
        return ApiResponse.success(result, "匹配规则更新成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules/<int:rule_id>', methods=['DELETE'])
@token_required
def delete_rule(rule_id):
    """
    删除匹配规则
    
    参数:
    - rule_id: 规则ID
    
    返回:
    - 成功: 删除结果
    - 失败: 错误信息
    """
    try:
        # 参数验证
        if rule_id < 1:
            return ApiResponse.error("规则ID必须大于0")
        
        # 调用服务层删除规则
        result = MatchRuleService.delete_rule(rule_id)
        
        # 检查是否有错误
        if 'error' in result:
            return ApiResponse.error(f"删除匹配规则失败: {result['error']}")
        
        # 返回成功响应
        return ApiResponse.success(result, "匹配规则删除成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules/<int:rule_id>/toggle', methods=['PUT'])
@token_required
def toggle_rule_status(rule_id):
    """
    切换匹配规则的启用状态
    
    参数:
    - rule_id: 规则ID
    
    返回:
    - 成功: 切换结果
    - 失败: 错误信息
    """
    try:
        # 参数验证
        if rule_id < 1:
            return ApiResponse.error("规则ID必须大于0")
        
        # 调用服务层切换规则状态
        result = MatchRuleService.toggle_rule_status(rule_id)
        
        # 检查是否有错误
        if 'error' in result:
            return ApiResponse.error(f"切换规则状态失败: {result['error']}")
        
        # 返回成功响应
        return ApiResponse.success(result, "规则状态切换成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules/attack-types', methods=['GET'])
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
        attack_types = MatchRuleService.get_attack_types()
        
        # 返回成功响应
        return ApiResponse.success(attack_types, "获取攻击类型成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)

@match_rule_bp.route('/match-rules/threat-levels', methods=['GET'])
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
        threat_levels = MatchRuleService.get_threat_levels()
        
        # 返回成功响应
        return ApiResponse.success(threat_levels, "获取威胁等级成功")
        
    except Exception as e:
        return ApiResponse.error(f"服务器错误: {str(e)}", 500)
