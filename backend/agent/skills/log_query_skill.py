# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from agent.mcp.skill import BaseSkill
# from service.log_service import LogService # 移除导致循环引用的导入
from utils.time_utils import get_beijing_time
from database import db
from model.log_model import Log

class LogQuerySkill(BaseSkill):
    """
    日志查询技能
    用于查询指定IP最近一段时间内的流量日志，帮助AI判断是否为恶意IP
    """
    
    @property
    def name(self) -> str:
        return "log_query"
        
    @property
    def description(self) -> str:
        return "查询指定IP最近24小时内的流量日志，获取攻击频率和类型"
    
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        执行技能
        :param input_data: 输入数据，通常是包含 'ip_address' 的字典或直接是 IP 字符串
        :return: 包含日志统计信息的字典
        """
        ip_address = None
        
        # 解析输入
        if isinstance(input_data, dict):
            ip_address = input_data.get('ip_address') or input_data.get('source_ip')
        elif isinstance(input_data, str):
            ip_address = input_data
            
        if not ip_address:
            return None
            
        try:
            # 计算24小时前的时间
            end_time = get_beijing_time()
            start_time = end_time - timedelta(days=1)
            
            # 查询该IP作为源IP的日志
            # 注意：这里直接使用 SQLAlchemy 查询，避免循环依赖 Service 层过多的逻辑
            logs = Log.query.filter(
                Log.source_ip == ip_address,
                Log.attack_time >= start_time,
                Log.attack_time <= end_time
            ).all()
            
            if not logs:
                return {
                    "ip_address": ip_address,
                    "log_count": 0,
                    "message": "近24小时内无流量记录"
                }
            
            # 统计信息
            total_count = len(logs)
            attack_types = {}
            malicious_count = 0
            
            recent_logs = []
            
            for log in logs:
                # 统计恶意流量
                if log.is_malicious:
                    malicious_count += 1
                
                # 统计攻击类型
                if log.attack_type:
                    attack_types[log.attack_type] = attack_types.get(log.attack_type, 0) + 1
                
                # 收集最近的5条日志摘要作为样本
                if len(recent_logs) < 5:
                    recent_logs.append({
                        "timestamp": log.attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "request_path": log.request_path,
                        "attack_type": log.attack_type,
                        "payload": log.payload[:100] if log.payload else ""
                    })
            
            return {
                "ip_address": ip_address,
                "period": "24h",
                "total_logs": total_count,
                "malicious_logs": malicious_count,
                "attack_type_distribution": attack_types,
                "recent_samples": recent_logs,
                "is_suspicious": malicious_count > 0 or total_count > 500 # 提高阈值，避免正常高频访问被误判
            }
            
        except Exception as e:
            print(f"LogQuerySkill 执行失败: {e}")
            return None
