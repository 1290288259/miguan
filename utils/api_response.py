# -*- coding: utf-8 -*-
"""
HTTP响应封装模块
提供统一的API响应格式，符合HTTP标准
"""

from flask import jsonify, Response
import json
from typing import Any, Dict, Optional, Tuple

class ApiResponse:
    """
    API响应封装类
    提供统一的响应格式，包含状态码、消息和数据
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", status_code: int = 200) -> Tuple[Response, int]:
        """
        成功响应
        
        参数:
            data: 响应数据，可以是任意类型
            message: 响应消息，默认为"操作成功"
            status_code: HTTP状态码，默认为200
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        response_data = {
            'success': True,
            'code': status_code,
            'message': message,
            'data': data
        }
        return jsonify(response_data), status_code
    
    @staticmethod
    def error(message: str = "操作失败", status_code: int = 400, error_code: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[Response, int]:
        """
        错误响应
        
        参数:
            message: 错误消息，默认为"操作失败"
            status_code: HTTP状态码，默认为400
            error_code: 自定义错误代码，可选
            details: 错误详细信息，可选
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        response_data = {
            'success': False,
            'code': status_code,
            'message': message
        }
        
        # 添加自定义错误代码（如果提供）
        if error_code:
            response_data['error_code'] = error_code
            
        # 添加错误详细信息（如果提供）
        if details:
            response_data['details'] = details
            
        return jsonify(response_data), status_code
    
    @staticmethod
    def created(data: Any = None, message: str = "创建成功") -> Tuple[Response, int]:
        """
        资源创建成功响应（201状态码）
        
        参数:
            data: 响应数据，可以是任意类型
            message: 响应消息，默认为"创建成功"
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.success(data=data, message=message, status_code=201)
    
    @staticmethod
    def no_content(message: str = "操作成功") -> Tuple[Response, int]:
        """
        无内容响应（204状态码）
        适用于成功操作但不返回内容的场景
        
        参数:
            message: 响应消息，默认为"操作成功"
            
        返回:
            tuple: 包含空响应和状态码的元组
        """
        response_data = {
            'success': True,
            'code': 204,
            'message': message,
            'data': None
        }
        return jsonify(response_data), 204
    
    @staticmethod
    def bad_request(message: str = "请求参数错误", error_code: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[Response, int]:
        """
        请求参数错误响应（400状态码）
        
        参数:
            message: 错误消息，默认为"请求参数错误"
            error_code: 自定义错误代码，可选
            details: 错误详细信息，可选
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.error(message=message, status_code=400, error_code=error_code, details=details)
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> Tuple[Response, int]:
        """
        未授权响应（401状态码）
        
        参数:
            message: 错误消息，默认为"未授权访问"
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.error(message=message, status_code=401, error_code="UNAUTHORIZED")
    
    @staticmethod
    def forbidden(message: str = "禁止访问") -> Tuple[Response, int]:
        """
        禁止访问响应（403状态码）
        
        参数:
            message: 错误消息，默认为"禁止访问"
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.error(message=message, status_code=403, error_code="FORBIDDEN")
    
    @staticmethod
    def not_found(message: str = "资源不存在") -> Tuple[Response, int]:
        """
        资源不存在响应（404状态码）
        
        参数:
            message: 错误消息，默认为"资源不存在"
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.error(message=message, status_code=404, error_code="NOT_FOUND")
    
    @staticmethod
    def server_error(message: str = "服务器内部错误", error_code: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[Response, int]:
        """
        服务器内部错误响应（500状态码）
        
        参数:
            message: 错误消息，默认为"服务器内部错误"
            error_code: 自定义错误代码，可选
            details: 错误详细信息，可选
            
        返回:
            tuple: 包含JSON响应和状态码的元组
        """
        return ApiResponse.error(message=message, status_code=500, error_code=error_code, details=details)