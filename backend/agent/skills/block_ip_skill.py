# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, Optional
from agent.mcp.skill import BaseSkill
from service.malicious_ip_service import MaliciousIPService

logger = logging.getLogger(__name__)

class BlockIPSkill(BaseSkill):
    """
    恶意IP封禁技能
    封装了恶意IP管理模块的封禁功能，供Agent在分析判断为恶意流量后自动调用。
    执行流程：先确保恶意IP记录存在（不存在则自动创建），再执行封禁操作，
    解决了AI分析速度快于恶意IP入库时导致封禁失败的时序问题。
    """
    
    @property
    def name(self) -> str:
        return "block_ip"
        
    @property
    def description(self) -> str:
        return "封禁指定的恶意IP地址。参数：ip_address(必填), reason(选填), attack_type(选填), threat_level(选填), duration(选填,单位:秒), block_until(选填,格式:YYYY-MM-DD HH:MM:SS)"

    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        执行封禁操作
        :param input_data: 包含 ip_address, reason, attack_type, threat_level, duration 的字典
        :param context: 上下文信息（可选），包含原始日志数据
        :return: 操作结果
        """
        ip_address = None
        reason = "AI自动封禁"
        duration = None  # 默认永久
        block_until = None
        attack_type = None
        threat_level = 'high'  # AI判定为需要封禁，默认威胁等级为高
        source_honeypot_id = None

        # 解析输入参数
        if isinstance(input_data, dict):
            ip_address = input_data.get('ip_address') or input_data.get('source_ip')
            reason = input_data.get('reason', reason)
            duration = input_data.get('duration', duration)
            block_until = input_data.get('block_until', None)
            attack_type = input_data.get('attack_type', None)
            threat_level = input_data.get('threat_level', threat_level)
            source_honeypot_id = input_data.get('source_honeypot_id', None)
        elif isinstance(input_data, str):
            ip_address = input_data

        # 从上下文中补充信息
        if context and isinstance(context, dict):
            if not attack_type:
                attack_type = context.get('attack_type') or context.get('ai_attack_type')
            if not source_honeypot_id:
                source_honeypot_id = context.get('honeypot_id')

        if not ip_address:
            return {
                "success": False,
                "message": "未提供IP地址"
            }

        try:
            from flask import current_app

            # 检查是否在Flask应用上下文中
            try:
                current_app.name
            except RuntimeError:
                logger.warning("BlockIPSkill: 当前不在Flask应用上下文中，数据库操作可能失败")

            # -------------------------------------------------------
            # 关键修复：先确保恶意IP记录存在，再执行封禁
            # 解决 AI 分析速度快于日志入库时，block_ip 找不到记录的时序问题
            # -------------------------------------------------------
            logger.info(f"BlockIPSkill: 正在确保恶意IP记录存在: {ip_address}")
            record_result = MaliciousIPService.record_malicious_ip(
                ip_address=ip_address,
                attack_type=attack_type,
                threat_level=threat_level,
                source_honeypot_id=source_honeypot_id,
                notes=f"由AI自动封禁触发记录: {reason}"
            )

            if record_result is None:
                logger.error(f"BlockIPSkill: 创建/更新恶意IP记录失败: {ip_address}")
                return {
                    "success": False,
                    "message": f"创建恶意IP记录失败，无法封禁 {ip_address}"
                }

            # 执行封禁操作
            logger.info(f"BlockIPSkill: 开始封禁IP: {ip_address}, 原因: {reason}")
            result = MaliciousIPService.block_ip(
                ip_address=ip_address,
                reason=reason,
                duration=duration,
                block_until=block_until
            )

            if result.get('success'):
                logger.info(f"BlockIPSkill: 成功封禁IP {ip_address}")
            else:
                logger.warning(f"BlockIPSkill: 封禁IP {ip_address} 失败: {result.get('message')}")

            return {
                "success": result.get('success', False),
                "message": result.get('message', '未知结果'),
                "ip_address": ip_address,
                "action": "blocked"
            }

        except Exception as e:
            logger.error(f"BlockIPSkill 执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"封禁失败: {str(e)}"
            }
