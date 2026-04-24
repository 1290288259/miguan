# -*- coding: utf-8 -*-
"""
恶意流量分析识别服务 (独立的分析引擎)
封装所有恶意流量（正则、行为频次）的判定逻辑
"""

import re
from typing import Dict, Any, Tuple
from database import db
from model.log_model import Log
from model.match_rule_model import MatchRule
from utils.time_utils import get_beijing_time


class TrafficAnalyzerService:
    SAFE_ATTACK_TYPES = {
        "normal", "page visit", "web visit", "safe", "unknown", 
        "正常", "正常流量"
    }
    MALICIOUS_THREAT_LEVELS = {"medium", "high", "critical"}

    BRUTE_FORCE_THRESHOLD = 20
    BRUTE_FORCE_WINDOW_MINUTES = 1

    # 认证类载荷的正则模式：用于判断 HTTP 等协议的载荷是否包含账号密码
    _CREDENTIAL_PATTERN = re.compile(r"Username:\s*.+,\s*Password:\s*.+", re.IGNORECASE)
    
    # 编译后正则表达式缓存
    _compiled_rules_cache = {}

    THREAT_LEVEL_WEIGHTS = {
        "critical": 50,
        "high": 40,
        "medium": 30,
        "low": 20,
        "info": 10
    }

    @classmethod
    def _is_safe_attack_type(cls, attack_type: str) -> bool:
        if not attack_type:
            return False
        return attack_type.strip().lower() in cls.SAFE_ATTACK_TYPES

    @classmethod
    def _is_credential_payload(cls, payload: str) -> bool:
        if not payload:
            return False
        return bool(cls._CREDENTIAL_PATTERN.search(payload))

    @classmethod
    def _check_brute_force(cls, attacker_ip: str, protocol: str = None, current_payload: str = None) -> bool:
        from datetime import timedelta
        
        if not attacker_ip:
            return False

        if protocol and protocol.upper() == "HTTP":
            if not cls._is_credential_payload(current_payload):
                return False

        one_min_ago = get_beijing_time() - timedelta(minutes=cls.BRUTE_FORCE_WINDOW_MINUTES)

        base_filter = [
            Log.attacker_ip == attacker_ip,
            Log.attack_time >= one_min_ago,
            Log.payload.isnot(None),
            Log.payload != "",
        ]

        # 匹配相同的协议
        if protocol:
            base_filter.append(Log.protocol == protocol)

        if protocol and protocol.upper() == "HTTP":
            base_filter.append(
                Log.payload.like("%Username:%") & Log.payload.like("%Password:%")
            )

        # 仅统计已被识别为正常/尝试登录，或者已经判定为暴力破解的历史流量
        valid_types = list(cls.SAFE_ATTACK_TYPES) + [
            "SSH尝试登录", "FTP尝试登录", "MySQL尝试登录", "Redis尝试登录", 
            "HTTP尝试登录", "暴力破解"
        ]
        base_filter.append(Log.attack_type.in_(valid_types))

        count = db.session.query(db.func.count(Log.id)).filter(*base_filter).scalar()
        return (count + 1) >= cls.BRUTE_FORCE_THRESHOLD

    @classmethod
    def _infer_is_malicious(cls, attack_type: str, threat_level: str) -> bool:
        if cls._is_safe_attack_type(attack_type):
            return False
        if threat_level and threat_level.strip().lower() in cls.MALICIOUS_THREAT_LEVELS:
            return True
        return bool(attack_type)

    @classmethod
    def analyze(cls, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单条流量日志进行恶意判定
        返回: 判定后的 attack_type, threat_level, is_malicious, attack_description
        """
        protocol_val = log_data.get("protocol", "").upper()
        request_path = log_data.get("request_path", "")

        threat_level = "low"
        attack_description = None
        is_malicious = True
        auto_block = False
        block_duration = 0

        if protocol_val == "SSH":
            attack_type = "SSH尝试登录"
        elif protocol_val == "FTP":
            attack_type = "FTP尝试登录"
        elif protocol_val == "MYSQL":
            attack_type = "MySQL尝试登录"
        elif protocol_val == "REDIS":
            attack_type = "Redis尝试登录"
        elif protocol_val == "HTTP":
            if request_path == "/login":
                attack_type = "HTTP尝试登录"
            else:
                attack_type = "正常流量"
                is_malicious = False
        else:
            attack_type = "正常流量"
            is_malicious = False

        # ============================================================
        # 第一级：规则引擎匹配（正则识别）
        # ============================================================
        try:
            rules = (
                MatchRule.query.filter_by(is_enabled=True)
                .order_by(MatchRule.priority.asc())
                .all()
            )

            combined_content = " ".join(filter(None, [
                str(log_data.get("raw_log") or ""),
                str(log_data.get("payload") or ""),
                str(log_data.get("request_path") or ""),
                str(log_data.get("user_agent") or "")
            ]))

            matched_priority = None
            matched_attack_types = []
            max_threat_weight = -1
            final_threat_level = threat_level

            for rule in rules:
                try:
                    if rule.match_field == "raw_log":
                        match_content = combined_content
                    else:
                        match_content = str(log_data.get(rule.match_field) or "") or combined_content

                    if match_content:
                        content_str = str(match_content)
                        
                        cache_key = rule.id
                        if cache_key not in cls._compiled_rules_cache or cls._compiled_rules_cache[cache_key]['pattern'] != rule.regex_pattern:
                            optimized_pattern = re.sub(r'(?<!\\)\((?!\?)', '(?:', rule.regex_pattern)
                            try:
                                cls._compiled_rules_cache[cache_key] = {
                                    'pattern': rule.regex_pattern,
                                    'compiled': re.compile(optimized_pattern, re.IGNORECASE)
                                }
                            except re.error:
                                cls._compiled_rules_cache[cache_key] = {
                                    'pattern': rule.regex_pattern,
                                    'compiled': re.compile(rule.regex_pattern, re.IGNORECASE)
                                }
                        
                        compiled_pattern = cls._compiled_rules_cache[cache_key]['compiled']

                        if compiled_pattern.search(content_str):
                            if matched_priority is None:
                                is_malicious = cls._infer_is_malicious(rule.attack_type, rule.threat_level)
                                matched_priority = rule.priority
                                auto_block = getattr(rule, 'auto_block', False)
                                block_duration = getattr(rule, 'block_duration', 0)
                            
                            # Collect attack_type
                            if rule.attack_type not in matched_attack_types:
                                matched_attack_types.append(rule.attack_type)
                            
                            # Determine max threat level
                            current_weight = cls.THREAT_LEVEL_WEIGHTS.get(rule.threat_level.lower(), 0)
                            if current_weight > max_threat_weight:
                                max_threat_weight = current_weight
                                final_threat_level = rule.threat_level

                            rule_msg = f"触发规则: {rule.name}"
                            if not attack_description:
                                attack_description = rule_msg
                            elif rule_msg not in attack_description:
                                attack_description += f" | {rule_msg}"
                                
                            rule.match_count += 1
                            rule.last_matched = get_beijing_time()
                except Exception as e:
                    print(f"应用规则 {rule.name} 时出错: {str(e)}")
                    continue
            
            if matched_priority is not None:
                attack_type = " | ".join(matched_attack_types)
                threat_level = final_threat_level

        except Exception as e:
            print(f"规则匹配过程中出错: {str(e)}")

        # ============================================================
        # 第二级：暴力破解分析（行为频次识别）
        # ============================================================
        if matched_priority is None:
            payload = log_data.get("payload")
            protocol = log_data.get("protocol")
            if payload:
                is_brute_force = cls._check_brute_force(
                    attacker_ip=log_data.get("attacker_ip"),
                    protocol=protocol,
                    current_payload=payload,
                )
                if is_brute_force:
                    attack_type = "暴力破解"
                    threat_level = "high"
                    is_malicious = True
                    rule_msg = "触发系统引擎: 暴力破解检测"
                    from service.system_config_service import SystemConfigService
                    bf_config = SystemConfigService.get_brute_force_config()
                    if bf_config.get("auto_block"):
                        auto_block = True
                        block_duration = bf_config.get("block_duration", 24)
                    
                    if not attack_description:
                        attack_description = rule_msg
                    elif rule_msg not in attack_description:
                        attack_description += f" | {rule_msg}"

        return {
            "attack_type": attack_type,
            "threat_level": threat_level,
            "is_malicious": is_malicious,
            "attack_description": attack_description,
            "auto_block": auto_block,
            "block_duration": block_duration
        }
