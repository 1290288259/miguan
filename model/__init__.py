# -*- coding: utf-8 -*-
"""
模型模块初始化文件
用于导出所有数据库模型类
"""

# 导入所有模型类
from .user_model import User
from .honeypot_model import Honeypot
from .log_model import Log
from .malicious_ip_model import MaliciousIP
from .match_rule_model import MatchRule
from .attack_stats_model import AttackStats
from .block_history_model import BlockHistory
from .permission_model import Permission
from .ai_config_model import AIConfig
from .user_info_model import UserInfo

# 导出所有模型
__all__ = [
    'User',
    'Honeypot',
    'Log',
    'MaliciousIP',
    'MatchRule',
    'AttackStats',
    'BlockHistory',
    'Permission',
    'AIConfig',
    'UserInfo'
]