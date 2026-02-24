# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional
from agent.mcp.skill import BaseSkill
from service.malicious_ip_service import MaliciousIPService

class BlockIPSkill(BaseSkill):
    """
    恶意IP封禁技能
    封装了恶意IP管理模块的封禁功能，供Agent在分析判断为恶意流量后自动调用
    """
    
    @property
    def name(self) -> str:
        return "block_ip"
        
    @property
    def description(self) -> str:
        return "封禁指定的恶意IP地址。参数：ip_address(必填), reason(选填), duration(选填,单位:秒), block_until(选填,格式:YYYY-MM-DD HH:MM:SS)"

    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        执行封禁操作
        :param input_data: 包含 ip_address, reason, duration 的字典
        :return: 操作结果
        """
        ip_address = None
        reason = "AI自动封禁"
        duration = None # 默认永久
        block_until = None
        
        # 解析输入
        if isinstance(input_data, dict):
            ip_address = input_data.get('ip_address') or input_data.get('source_ip')
            reason = input_data.get('reason', reason)
            duration = input_data.get('duration', duration) 
            block_until = input_data.get('block_until', None) 
        elif isinstance(input_data, str):
            ip_address = input_data
            
        if not ip_address:
            return {
                "success": False,
                "message": "未提供IP地址"
            }
            
        try:
            # 排除白名单或自身IP
            # 这里可以调用 MaliciousIPService 中的检查逻辑
            
            # 调用封禁服务
            # 如果提供了 duration (int)，则转换或直接使用
            # 如果提供了 block_until (str)，则使用 block_until
            
            # 注意：MaliciousIPService.block_ip 需要在应用上下文中运行
            # 但这里作为 skill 被调用时通常是在 AI 分析线程中
            
            # 使用 app_context 是必要的，因为涉及到数据库操作
            from flask import current_app
            
            # 尝试在应用上下文中执行
            try:
                # 检查是否已在应用上下文中
                current_app.name
                in_context = True
            except RuntimeError:
                in_context = False
                
            if in_context:
                result = MaliciousIPService.block_ip(
                    ip_address=ip_address,
                    reason=reason,
                    duration=duration,
                    block_until=block_until
                )
            else:
                # 如果不在上下文中（例如在独立线程），可能需要传入 app 实例
                # 但目前的架构 skill 很难直接获取 app 实例
                # 暂时假设调用方会在上下文中
                print("BlockIPSkill: Warning - Not in application context, database operations might fail")
                result = MaliciousIPService.block_ip(
                    ip_address=ip_address,
                    reason=reason,
                    duration=duration,
                    block_until=block_until
                )
                
            return {
                "success": result.get('success', False),
                "message": result.get('message', '未知结果'),
                "ip_address": ip_address,
                "action": "blocked"
            }
            
        except Exception as e:
            print(f"BlockIPSkill 执行失败: {e}")
            return {
                "success": False,
                "message": f"封禁失败: {str(e)}"
            }
