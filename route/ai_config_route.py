# -*- coding: utf-8 -*-
"""
AI配置路由
提供AI配置相关的API接口
"""

from flask import Blueprint, request, jsonify
from service.ai_config_service import AIConfigService
from utils.api_response import ApiResponse
from functools import wraps

# 创建蓝图
ai_config_bp = Blueprint('ai_config', __name__, url_prefix='/api/ai-config')

@ai_config_bp.route('/', methods=['GET'])
def get_configs():
    """
    获取所有配置
    """
    try:
        configs = AIConfigService.get_all_configs()
        return ApiResponse.success(data=[c.to_dict() for c in configs])
    except Exception as e:
        return ApiResponse.error(message=str(e))

@ai_config_bp.route('/', methods=['POST'])
def create_config():
    """
    创建配置
    """
    try:
        data = request.json
        if not data.get('name') or not data.get('api_url') or not data.get('model_name'):
            return ApiResponse.error(message="名称、API地址和模型名称必填")
            
        config = AIConfigService.create_config(data)
        return ApiResponse.success(data=config.to_dict(), message="创建成功")
    except ValueError as e:
        return ApiResponse.error(message=str(e))
    except Exception as e:
        return ApiResponse.error(message=f"创建失败: {str(e)}")

@ai_config_bp.route('/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """
    更新配置
    """
    try:
        data = request.json
        config = AIConfigService.update_config(config_id, data)
        if not config:
            return ApiResponse.error(message="配置不存在", status_code=404)
        return ApiResponse.success(data=config.to_dict(), message="更新成功")
    except ValueError as e:
        return ApiResponse.error(message=str(e))
    except Exception as e:
        return ApiResponse.error(message=f"更新失败: {str(e)}")

@ai_config_bp.route('/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """
    删除配置
    """
    try:
        if AIConfigService.delete_config(config_id):
            return ApiResponse.success(message="删除成功")
        else:
            return ApiResponse.error(message="配置不存在", status_code=404)
    except Exception as e:
        return ApiResponse.error(message=f"删除失败: {str(e)}")

@ai_config_bp.route('/<int:config_id>/activate', methods=['POST'])
def activate_config(config_id):
    """
    激活配置
    """
    try:
        if AIConfigService.activate_config(config_id):
            return ApiResponse.success(message="激活成功")
        else:
            return ApiResponse.error(message="配置不存在", status_code=404)
    except Exception as e:
        return ApiResponse.error(message=f"激活失败: {str(e)}")

@ai_config_bp.route('/<int:config_id>/deactivate', methods=['POST'])
def deactivate_config(config_id):
    """
    禁用配置
    """
    try:
        if AIConfigService.deactivate_config(config_id):
            return ApiResponse.success(message="禁用成功")
        else:
            return ApiResponse.error(message="配置不存在", status_code=404)
    except Exception as e:
        return ApiResponse.error(message=f"禁用失败: {str(e)}")

@ai_config_bp.route('/<int:config_id>/test', methods=['POST'])
def test_config(config_id):
    """
    测试配置连接
    """
    try:
        result = AIConfigService.test_connection(config_id)
        if result['success']:
            return ApiResponse.success(data=result, message="连接测试成功")
        else:
            return ApiResponse.error(message=f"连接测试失败: {result.get('error')}")
    except ValueError as e:
        return ApiResponse.error(message=str(e), status_code=404)
    except Exception as e:
        return ApiResponse.error(message=f"系统错误: {str(e)}")
