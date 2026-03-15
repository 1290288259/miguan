# -*- coding: utf-8 -*-
"""
测试服务模块
提供简单的测试服务功能
"""

class TestService:
    """
    测试服务类
    用于测试route和service层的交互
    """
    
    def __init__(self):
        """
        初始化测试服务
        """
        self.message = "你好"
    
    def get_hello_message(self):
        """
        获取问候消息
        
        返回:
            str: 问候消息
        """
        return self.message
    
    def get_custom_message(self, name):
        """
        获取自定义问候消息
        
        参数:
            name (str): 用户名
            
        返回:
            str: 自定义问候消息
        """
        return f"{self.message}, {name}!"