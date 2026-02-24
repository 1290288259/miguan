# -*- coding: utf-8 -*-
"""
日志模型
定义日志相关的数据库表结构
"""

from database import db
from datetime import datetime
from utils.time_utils import get_beijing_time

class Log(db.Model):
    """
    日志模型类
    存储蜜罐捕获的攻击日志
    """
    __tablename__ = 'logs'  # 表名
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    
    # 关联的蜜罐ID
    honeypot_id = db.Column(db.Integer, db.ForeignKey('honeypots.id'), nullable=False, comment='蜜罐ID')
    
    # 攻击者IP地址
    attacker_ip = db.Column(db.String(15), nullable=False, comment='攻击者IP地址')
    
    # 攻击时间
    attack_time = db.Column(db.DateTime, nullable=False, default=get_beijing_time, comment='攻击时间')
    
    # 原始日志内容
    raw_log = db.Column(db.Text, nullable=False, comment='原始日志内容')
    
    # 源IP地址（从日志中提取）
    source_ip = db.Column(db.String(15), nullable=True, comment='源IP地址')
    
    # 目标IP地址（从日志中提取）
    target_ip = db.Column(db.String(15), nullable=True, comment='目标IP地址')
    
    # 源端口（从日志中提取）
    source_port = db.Column(db.Integer, nullable=True, comment='源端口')
    
    # 目标端口（从日志中提取）
    target_port = db.Column(db.Integer, nullable=True, comment='目标端口')
    
    # 协议类型（从日志中提取）
    protocol = db.Column(db.String(10), nullable=True, comment='协议类型')
    
    # 用户代理（从日志中提取）
    user_agent = db.Column(db.String(255), nullable=True, comment='用户代理')
    
    # 请求路径（从日志中提取）
    request_path = db.Column(db.String(255), nullable=True, comment='请求路径')
    
    # 攻击类型
    attack_type = db.Column(db.String(50), nullable=True, comment='攻击类型')
    
    # 攻击描述
    attack_description = db.Column(db.Text, nullable=True, comment='攻击描述')
    
    # 攻击载荷
    payload = db.Column(db.Text, nullable=True, comment='攻击载荷')
    
    # 威胁等级（低、中、高、严重）
    threat_level = db.Column(db.String(20), nullable=True, comment='威胁等级')
    
    # 是否为恶意流量
    is_malicious = db.Column(db.Boolean, nullable=False, default=False, comment='是否为恶意流量')
    
    # 是否已阻断
    is_blocked = db.Column(db.Boolean, nullable=False, default=False, comment='是否已阻断')
    
    # 阻断时间
    blocked_time = db.Column(db.DateTime, nullable=True, comment='阻断时间')
    
    # 备注
    notes = db.Column(db.Text, nullable=True, comment='备注')

    # AI分析相关字段
    ai_attack_type = db.Column(db.String(50), nullable=True, comment='AI识别的攻击类型')
    ai_confidence = db.Column(db.Float, nullable=True, comment='AI识别置信度')
    ai_analysis_result = db.Column(db.Text, nullable=True, comment='AI完整分析结果')
    ai_rule_match_consistency = db.Column(db.String(20), nullable=True, comment='AI与规则匹配一致性')

    def __repr__(self):
        """
        日志模型的字符串表示
        返回:
            str: 日志模型的字符串表示
        """
        return f'<Log {self.attacker_ip}:{self.attack_type}>'
    
    def to_dict(self):
        """
        将日志模型转换为字典
        返回:
            dict: 日志信息的字典表示
        """
        return {
            'id': self.id,
            'honeypot_id': self.honeypot_id,
            'attacker_ip': self.attacker_ip,
            'attack_time': self.attack_time.isoformat() if self.attack_time else None,
            'raw_log': self.raw_log,
            'source_ip': self.source_ip,
            'target_ip': self.target_ip,
            'source_port': self.source_port,
            'target_port': self.target_port,
            'protocol': self.protocol,
            'user_agent': self.user_agent,
            'request_path': self.request_path,
            'attack_type': self.attack_type,
            'attack_description': self.attack_description,
            'payload': self.payload,
            'threat_level': self.threat_level,
            'is_malicious': self.is_malicious,
            'is_blocked': self.is_blocked,
            'blocked_time': self.blocked_time.isoformat() if self.blocked_time else None,
            'notes': self.notes,
            'ai_attack_type': self.ai_attack_type,
            'ai_confidence': self.ai_confidence,
            'ai_analysis_result': self.ai_analysis_result,
            'ai_rule_match_consistency': self.ai_rule_match_consistency
        }