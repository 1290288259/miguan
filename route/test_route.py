# -*- coding: utf-8 -*-
"""
测试路由模块
提供测试API接口
"""

from flask import request
from utils.api_response import ApiResponse
from service.test_service import TestService

# 创建测试服务实例
test_service = TestService()

def hello():
    """
    测试问候接口
    
    返回:
        dict: 包含问候消息的JSON响应
    """
    try:
        # 调用服务层获取问候消息
        message = test_service.get_hello_message()
        # 返回成功响应
        return ApiResponse.success(
            data={'message': message},
            message="获取问候消息成功"
        )
    except Exception as e:
        # 错误处理
        return ApiResponse.server_error(
            message="获取问候消息失败",
            details={'error': str(e)}
        )

def hello_with_name():
    """
    带用户名的测试问候接口
    
    返回:
        dict: 包含自定义问候消息的JSON响应
    """
    try:
        # 获取请求参数
        data = request.get_json() if request.is_json else request.args.to_dict()
        name = data.get('name', '朋友')
        
        # 调用服务层获取自定义问候消息
        message = test_service.get_custom_message(name)
        
        # 返回成功响应
        return ApiResponse.success(
            data={
                'message': message,
                'name': name
            },
            message="获取自定义问候消息成功"
        )
    except Exception as e:
        # 错误处理
        return ApiResponse.server_error(
            message="获取自定义问候消息失败",
            details={'error': str(e)}
        )