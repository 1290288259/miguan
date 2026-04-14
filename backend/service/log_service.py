# -*- coding: utf-8 -*-
"""
日志服务
处理日志相关的业务逻辑。
"""

from datetime import datetime
from io import StringIO
from typing import Dict, List, Optional, Tuple
import csv
import re

from database import db
from model.honeypot_model import Honeypot
from model.log_model import Log
from model.match_rule_model import MatchRule
from service.ai_analysis_service import AIAnalysisService
from utils.time_utils import get_beijing_time


class LogService:
    SAFE_ATTACK_TYPES = {
        "normal",
        "page visit",
        "web visit",
        "safe",
        "unknown",
        "正常",
        "正常流量",
        "ftp登录",
        "web登录",
        "mysql登录",
        "ssh登录",
    }
    MALICIOUS_THREAT_LEVELS = {"medium", "high", "critical"}

    @classmethod
    def _is_safe_attack_type(cls, attack_type: str) -> bool:
        if not attack_type:
            return False
        return attack_type.strip().lower() in cls.SAFE_ATTACK_TYPES

    # 暴力破解判定阈值：1分钟内同一IP的有效认证尝试次数
    BRUTE_FORCE_THRESHOLD = 20
    BRUTE_FORCE_WINDOW_MINUTES = 1

    # 认证类载荷的正则模式：用于判断 HTTP 等协议的载荷是否包含账号密码
    # 匹配 "Username: xxx, Password: xxx" 格式（各蜜罐统一的凭证格式）
    _CREDENTIAL_PATTERN = re.compile(r"Username:\s*.+,\s*Password:\s*.+", re.IGNORECASE)

    @classmethod
    def _is_credential_payload(cls, payload: str) -> bool:
        """
        判断载荷是否包含认证凭证（用户名+密码）。
        用于暴力破解检测时，区分有效的认证尝试和普通请求。

        参数:
            payload: 请求载荷字符串

        返回:
            bool: 是否包含认证凭证
        """
        if not payload:
            return False
        return bool(cls._CREDENTIAL_PATTERN.search(payload))

    @classmethod
    def _check_brute_force(
        cls, attacker_ip: str, protocol: str = None, current_payload: str = None
    ) -> bool:
        """
        判断是否为暴力破解行为。

        多级识别引擎的第二级：行为频次分析。
        规则：同一IP在1分钟内有效认证尝试次数 >= 20 则判定为暴力破解。

        对于HTTP协议：只统计包含账号密码的载荷（如登录表单提交），
        普通的GET请求、路径探测等不计入暴力破解计数。

        对于其他协议（FTP/SSH/MySQL/Redis等）：所有带载荷的请求均计入，
        因为这些协议连接本身就代表认证尝试。

        参数:
            attacker_ip: 攻击者IP地址
            protocol: 协议类型（HTTP、FTP、SSH等）
            current_payload: 当前请求的载荷，用于判断当前请求是否算一次有效尝试

        返回:
            bool: 是否为暴力破解
        """
        from datetime import timedelta
        from utils.time_utils import get_beijing_time

        if not attacker_ip:
            return False

        # 对于HTTP协议，当前请求必须包含凭证才算有效认证尝试
        if protocol and protocol.upper() == "HTTP":
            if not cls._is_credential_payload(current_payload):
                return False

        one_min_ago = get_beijing_time() - timedelta(
            minutes=cls.BRUTE_FORCE_WINDOW_MINUTES
        )

        # 构建基础查询：同一IP、1分钟内、载荷非空
        base_filter = [
            Log.attacker_ip == attacker_ip,
            Log.attack_time >= one_min_ago,
            Log.payload.isnot(None),
            Log.payload != "",
        ]

        # 对于HTTP协议，额外过滤：只统计包含凭证的载荷
        if protocol and protocol.upper() == "HTTP":
            base_filter.append(Log.payload.like("%Username:%Password:%"))

        count = db.session.query(db.func.count(Log.id)).filter(*base_filter).scalar()

        # +1 包含当前这一条（尚未入库）
        return (count + 1) >= cls.BRUTE_FORCE_THRESHOLD

    @classmethod
    def _infer_is_malicious(cls, attack_type: str, threat_level: str) -> bool:
        if cls._is_safe_attack_type(attack_type):
            return False

        if threat_level and threat_level.strip().lower() in cls.MALICIOUS_THREAT_LEVELS:
            return True

        return bool(attack_type)

    @staticmethod
    def get_logs(
        page: int = 1,
        per_page: int = 20,
        attack_type: str = None,
        threat_level: str = None,
        protocol: str = None,
        start_time: str = None,
        end_time: str = None,
        keyword: str = None,
    ) -> Tuple[List[Dict], Dict]:
        """
        分页查询日志，支持条件筛选和关键字检索。

        参数:
            page: 页码，默认为 1
            per_page: 每页数量，默认为 20
            attack_type: 攻击类型过滤条件
            threat_level: 威胁等级过滤条件
            protocol: 协议类型过滤条件
            start_time: 开始时间过滤条件
            end_time: 结束时间过滤条件
            keyword: 关键字，可匹配多个字段

        返回:
            Tuple[List[Dict], Dict]: 日志列表和分页信息
        """
        try:
            query = Log.query

            if attack_type:
                query = query.filter(Log.attack_type == attack_type)

            if threat_level:
                query = query.filter(Log.threat_level == threat_level)

            if protocol:
                query = query.filter(Log.protocol == protocol)

            if start_time:
                start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                query = query.filter(Log.attack_time >= start_datetime)

            if end_time:
                end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                query = query.filter(Log.attack_time <= end_datetime)

            if keyword:
                query = query.filter(
                    Log.attack_type.like(f"%{keyword}%")
                    | Log.threat_level.like(f"%{keyword}%")
                    | Log.protocol.like(f"%{keyword}%")
                    | Log.source_ip.like(f"%{keyword}%")
                    | Log.target_ip.like(f"%{keyword}%")
                    | Log.attack_description.like(f"%{keyword}%")
                    | Log.raw_log.like(f"%{keyword}%")
                    | Log.request_path.like(f"%{keyword}%")
                    | Log.payload.like(f"%{keyword}%")
                    | Log.user_agent.like(f"%{keyword}%")
                    | Log.notes.like(f"%{keyword}%")
                )

            query = query.order_by(Log.attack_time.desc())

            total = query.count()
            offset = (page - 1) * per_page
            logs = query.offset(offset).limit(per_page).all()
            log_list = [log.to_dict() for log in logs]

            pagination = {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "has_prev": page > 1,
                "has_next": page * per_page < total,
                "prev_num": page - 1 if page > 1 else None,
                "next_num": page + 1 if page * per_page < total else None,
            }

            return log_list, pagination

        except Exception as e:
            print(f"查询日志时发生错误: {str(e)}")
            return [], {"error": str(e)}

    @staticmethod
    def export_logs(
        attack_type: str = None,
        threat_level: str = None,
        protocol: str = None,
        start_time: str = None,
        end_time: str = None,
        keyword: str = None,
        source_ip: str = None,
        target_ip: str = None,
        target_port: int = None,
        is_malicious: bool = None,
        is_blocked: bool = None,
    ) -> Tuple[str, str]:
        """
        导出日志。

        参数:
            attack_type: 攻击类型过滤条件
            threat_level: 威胁等级过滤条件
            protocol: 协议类型过滤条件
            start_time: 开始时间过滤条件
            end_time: 结束时间过滤条件
            keyword: 关键字，可匹配多个字段
            source_ip: 源 IP
            target_ip: 目标 IP
            target_port: 目标端口
            is_malicious: 是否为恶意 IP
            is_blocked: 是否已封禁

        返回:
            Tuple[str, str]: (csv_content, filename) 或 (None, error_message)
        """
        try:
            query = Log.query

            if attack_type:
                query = query.filter(Log.attack_type == attack_type)

            if threat_level:
                query = query.filter(Log.threat_level == threat_level)

            if protocol:
                query = query.filter(Log.protocol == protocol)

            if source_ip:
                query = query.filter(Log.source_ip.like(f"%{source_ip}%"))

            if target_ip:
                query = query.filter(Log.target_ip.like(f"%{target_ip}%"))

            if target_port is not None:
                query = query.filter(Log.target_port == target_port)

            if is_malicious is not None:
                query = query.filter(Log.is_malicious == is_malicious)

            if is_blocked is not None:
                query = query.filter(Log.is_blocked == is_blocked)

            if start_time and end_time:
                start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                time_diff = end_datetime - start_datetime
                if time_diff.days > 365:
                    return None, "导出时间范围不能超过一年"

                query = query.filter(Log.attack_time >= start_datetime)
                query = query.filter(Log.attack_time <= end_datetime)
            elif start_time:
                start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                query = query.filter(Log.attack_time >= start_datetime)
            elif end_time:
                end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                query = query.filter(Log.attack_time <= end_datetime)

            if keyword:
                query = query.filter(
                    Log.attack_type.like(f"%{keyword}%")
                    | Log.threat_level.like(f"%{keyword}%")
                    | Log.protocol.like(f"%{keyword}%")
                    | Log.source_ip.like(f"%{keyword}%")
                    | Log.target_ip.like(f"%{keyword}%")
                    | Log.attack_description.like(f"%{keyword}%")
                    | Log.raw_log.like(f"%{keyword}%")
                    | Log.request_path.like(f"%{keyword}%")
                    | Log.payload.like(f"%{keyword}%")
                    | Log.user_agent.like(f"%{keyword}%")
                    | Log.notes.like(f"%{keyword}%")
                )

            query = query.order_by(Log.attack_time.desc())
            logs = query.all()

            output = StringIO()
            writer = csv.writer(output)
            headers = [
                "ID",
                "攻击时间",
                "攻击类型",
                "威胁等级",
                "源IP",
                "源端口",
                "目标IP",
                "目标端口",
                "协议",
                "请求路径",
                "是否恶意",
                "是否阻断",
                "攻击描述",
            ]
            writer.writerow(headers)

            for log in logs:
                writer.writerow(
                    [
                        log.id,
                        log.attack_time.strftime("%Y-%m-%d %H:%M:%S")
                        if log.attack_time
                        else "",
                        log.attack_type or "",
                        log.threat_level or "",
                        log.source_ip or "",
                        log.source_port or "",
                        log.target_ip or "",
                        log.target_port or "",
                        log.protocol or "",
                        log.request_path or "",
                        "是" if log.is_malicious else "否",
                        "是" if log.is_blocked else "否",
                        log.attack_description or "",
                    ]
                )

            csv_content = output.getvalue()
            output.close()

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"logs_export_{timestamp}.csv"
            return csv_content, filename

        except Exception as e:
            print(f"导出日志时发生错误: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[Dict]:
        """
        根据 ID 获取单条日志。

        参数:
            log_id: 日志 ID

        返回:
            Optional[Dict]: 日志信息，如果不存在则返回 None
        """
        try:
            log = Log.query.get(log_id)
            if log:
                return log.to_dict()
            return None
        except Exception as e:
            print(f"根据 ID 查询日志时发生错误: {str(e)}")
            return None

    @staticmethod
    def get_attack_types() -> List[str]:
        """
        获取所有攻击类型。

        返回:
            List[str]: 攻击类型列表
        """
        try:
            attack_types = (
                db.session.query(Log.attack_type)
                .distinct()
                .filter(Log.attack_type.isnot(None))
                .all()
            )
            return [at[0] for at in attack_types]
        except Exception as e:
            print(f"获取攻击类型时发生错误: {str(e)}")
            return []

    @staticmethod
    def get_threat_levels() -> List[str]:
        """
        获取所有威胁等级。

        返回:
            List[str]: 威胁等级列表
        """
        try:
            threat_levels = (
                db.session.query(Log.threat_level)
                .distinct()
                .filter(Log.threat_level.isnot(None))
                .all()
            )
            return [tl[0] for tl in threat_levels]
        except Exception as e:
            print(f"获取威胁等级时发生错误: {str(e)}")
            return []

    @staticmethod
    def get_log_statistics() -> Dict:
        """
        获取日志统计信息。

        返回:
            Dict: 统计信息
        """
        try:
            total_logs = Log.query.count()
            malicious_logs = Log.query.filter(Log.is_malicious == True).count()
            blocked_logs = Log.query.filter(Log.is_blocked == True).count()

            attack_type_stats = (
                db.session.query(
                    Log.attack_type,
                    db.func.count(Log.id).label("count"),
                )
                .filter(Log.attack_type.isnot(None))
                .group_by(Log.attack_type)
                .all()
            )

            threat_level_stats = (
                db.session.query(
                    Log.threat_level,
                    db.func.count(Log.id).label("count"),
                )
                .filter(Log.threat_level.isnot(None))
                .group_by(Log.threat_level)
                .all()
            )

            from datetime import timedelta

            seven_days_ago = get_beijing_time() - timedelta(days=7)
            daily_stats = (
                db.session.query(
                    db.func.date(Log.attack_time).label("date"),
                    db.func.count(Log.id).label("count"),
                )
                .filter(Log.attack_time >= seven_days_ago)
                .group_by(db.func.date(Log.attack_time))
                .all()
            )

            return {
                "total_logs": total_logs,
                "malicious_logs": malicious_logs,
                "blocked_logs": blocked_logs,
                "attack_type_stats": [
                    {"type": at[0], "count": at[1]} for at in attack_type_stats
                ],
                "threat_level_stats": [
                    {"level": tl[0], "count": tl[1]} for tl in threat_level_stats
                ],
                "daily_stats": [
                    {"date": str(ds[0]), "count": ds[1]} for ds in daily_stats
                ],
            }
        except Exception as e:
            print(f"获取日志统计信息时发生错误: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def create_log(log_data: Dict) -> Dict:
        """
        创建日志记录。

        实现"正则 -> 频次 -> AI"三级恶意流量识别引擎：
        1. 规则引擎匹配（正则识别）：正则匹配黑名单规则，直接定性已知攻击特征
        2. 暴力破解分析（行为识别）：若正则未命中，分析频次判断是否为暴力破解
        3. AI深度分析（大模型识别）：经过上述判断后，触发AI进行深度综合分析

        参数:
            log_data: 日志数据字典（蜜罐上报的原始数据，不含 attack_type/threat_level）

        返回:
            Dict: 创建结果
        """
        try:
            honeypot_port = log_data.get("honeypot_port")
            honeypot = Honeypot.query.filter_by(port=honeypot_port).first()

            if not honeypot:
                return {"error": f"未找到端口为 {honeypot_port} 的蜜罐"}

            # ============================================================
            # 初始化：蜜罐上报的原始流量默认为"正常流量"
            # 蜜罐作为纯粹的数据收集层，不做任何业务判定
            # 所有分类工作由以下多级识别引擎完成
            # ============================================================
            attack_type = "正常流量"
            threat_level = "low"
            attack_description = None
            is_malicious = False

            # ============================================================
            # 第一级：规则引擎匹配（正则识别）
            # 提取流量载荷，过一遍黑名单正则匹配引擎
            # 判断是否包含 SQL注入、命令注入、XSS 等明显恶意特征
            # ============================================================
            try:
                rules = (
                    MatchRule.query.filter_by(is_enabled=True)
                    .order_by(MatchRule.priority.asc())
                    .all()
                )

                for rule in rules:
                    try:
                        match_content = log_data.get(rule.match_field)

                        if match_content is None and rule.match_field != "raw_log":
                            pass

                        if match_content is not None:
                            content_str = str(match_content)
                            if re.search(rule.regex_pattern, content_str, re.IGNORECASE):
                                attack_type = rule.attack_type
                                threat_level = rule.threat_level
                                is_malicious = LogService._infer_is_malicious(
                                    attack_type, threat_level
                                )

                                rule_msg = f"触发规则: {rule.name}"
                                if not attack_description:
                                    attack_description = rule_msg
                                elif rule_msg not in attack_description:
                                    attack_description += f" | {rule_msg}"

                                rule.match_count += 1
                                rule.last_matched = get_beijing_time()
                                break
                    except re.error as e:
                        print(f"规则 {rule.name} 正则表达式错误: {str(e)}")
                        continue
                    except Exception as e:
                        print(f"应用规则 {rule.name} 时出错: {str(e)}")
                        continue

            except Exception as e:
                print(f"规则匹配过程中出错: {str(e)}")

            # ============================================================
            # 第二级：暴力破解分析（行为频次识别）
            # 仅在正则引擎未命中（流量仍为"正常"）时触发
            # 分析同一IP短时间内的认证尝试频次
            # HTTP协议：需要载荷包含账号密码才算一次有效认证尝试
            # 其他协议：带载荷的请求即算有效认证尝试
            # ============================================================
            if not is_malicious:
                payload = log_data.get("payload")
                protocol = log_data.get("protocol")
                if payload:
                    is_brute_force = LogService._check_brute_force(
                        attacker_ip=log_data.get("attacker_ip"),
                        protocol=protocol,
                        current_payload=payload,
                    )
                    if is_brute_force:
                        attack_type = "暴力破解"
                        threat_level = "high"
                        is_malicious = True
                        rule_msg = "触发系统引擎: 暴力破解检测"
                        if not attack_description:
                            attack_description = rule_msg
                        elif rule_msg not in attack_description:
                            attack_description += f" | {rule_msg}"

            log = Log(
                honeypot_id=honeypot.id,
                attacker_ip=log_data.get("attacker_ip"),
                attack_time=get_beijing_time(),
                raw_log=log_data.get("raw_log"),
                source_ip=log_data.get("attacker_ip"),
                target_ip=log_data.get("target_ip", "127.0.0.1"),
                source_port=log_data.get("attacker_port"),
                target_port=log_data.get("honeypot_port"),
                protocol=log_data.get("protocol"),
                user_agent=log_data.get("user_agent"),
                request_path=log_data.get("request_path"),
                attack_type=attack_type,
                attack_description=attack_description,
                payload=log_data.get("payload"),
                threat_level=threat_level,
                is_malicious=is_malicious,
                notes=log_data.get("notes"),
            )

            db.session.add(log)
            db.session.commit()

            # ============================================================
            # 第三级：AI深度分析（大模型识别）
            # 经过正则和频次判断后，异步触发AI进行深度综合分析
            # AI会最终敲定完整的攻击描述与威胁等级
            # ============================================================
            try:
                log_data_dict = log.to_dict()
                log_data_dict["payload"] = log.payload
                log_data_dict["protocol"] = log.protocol
                log_data_dict["request_path"] = log.request_path
                AIAnalysisService.add_task(log.id, log_data_dict)
            except Exception as e:
                print(f"添加 AI 分析任务失败: {str(e)}")

            if is_malicious:
                try:
                    from service.malicious_ip_service import MaliciousIPService

                    MaliciousIPService.record_malicious_ip(
                        ip_address=log.attacker_ip,
                        attack_type=log.attack_type,
                        threat_level=log.threat_level,
                        source_honeypot_id=log.honeypot_id,
                        notes=f"触发日志 ID: {log.id}",
                    )
                except Exception as e:
                    print(f"自动记录恶意 IP 失败: {str(e)}")

                # WebSocket 实时推送
                try:
                    from extensions import socketio
                    from utils.ip_utils import get_ip_coordinates

                    # 动态获取IP的经纬度用于大屏展示脉冲红点
                    longitude, latitude = get_ip_coordinates(log.attacker_ip)

                    ws_payload = {
                        "log_id": log.id,
                        "source_ip": log.attacker_ip,
                        "attack_type": log.attack_type,
                        "threat_level": log.threat_level,
                        "protocol": log.protocol,
                        "target_port": log.target_port,
                        "attack_time": log.attack_time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "attack_description": log.attack_description,
                        "longitude": longitude,
                        "latitude": latitude,
                    }
                    socketio.emit("new_attack", ws_payload, namespace="/ws")
                except Exception as e:
                    print(f"WebSocket 推送失败: {str(e)}")

            return {
                "log_id": log.id,
                "status": "created",
                "message": "日志创建成功",
            }

        except Exception as e:
            db.session.rollback()
            print(f"创建日志时发生错误: {str(e)}")
            return {"error": str(e)}
