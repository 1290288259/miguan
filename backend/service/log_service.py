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
from service.traffic_analyzer_service import TrafficAnalyzerService
from utils.time_utils import get_beijing_time

class LogService:
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
        log_id: str = None,
        source_ip: str = None,
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

            if log_id:
                query = query.filter(Log.id == log_id)
            if source_ip:
                query = query.filter(Log.source_ip.like(f"%{source_ip}%"))

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

            query = query.order_by(Log.id.desc())

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

            if log_id:
                query = query.filter(Log.id == log_id)
            if source_ip:
                query = query.filter(Log.source_ip.like(f"%{source_ip}%"))

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
            # 调用独立的流量分析服务，获取判定结果
            # ============================================================
            analysis_result = TrafficAnalyzerService.analyze(log_data)
            
            attack_type = analysis_result["attack_type"]
            threat_level = analysis_result["threat_level"]
            behavior_is_malicious = analysis_result["is_malicious"]
            attack_description = analysis_result["attack_description"]
            auto_block = analysis_result.get("auto_block", False)
            block_duration = analysis_result.get("block_duration", 0)

            # 检查是否已经在恶意IP表中
            is_known_malicious_ip = False
            try:
                from model.malicious_ip_model import MaliciousIP
                attacker_ip = log_data.get("attacker_ip")
                if attacker_ip:
                    existing_malicious = MaliciousIP.query.filter_by(ip_address=attacker_ip).first()
                    if existing_malicious:
                        is_known_malicious_ip = True
            except Exception as e:
                print(f"查询恶意IP表失败: {str(e)}")

            # 两个判断：1是查询是否在恶意ip表中，2是这次行为是否构成恶意攻击
            final_is_malicious = behavior_is_malicious or is_known_malicious_ip
            
            if is_known_malicious_ip and not behavior_is_malicious:
                threat_level = "medium" if threat_level == "low" else threat_level
                if attack_description:
                    attack_description += " | 命中历史恶意IP"
                else:
                    attack_description = "命中历史恶意IP"

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
                is_malicious=final_is_malicious,
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

            # 构成攻击的行为会让其IP进入恶意IP表
            if behavior_is_malicious:
                try:
                    from service.malicious_ip_service import MaliciousIPService

                    MaliciousIPService.record_malicious_ip(
                        ip_address=log.attacker_ip,
                        attack_type=log.attack_type,
                        threat_level=log.threat_level,
                        source_honeypot_id=log.honeypot_id,
                        notes=f"触发日志 ID: {log.id}",
                    )
                    
                    if auto_block:
                        # 获取封禁时长（秒）
                        duration_seconds = block_duration * 3600 if block_duration > 0 else None
                        
                        # 调用封禁逻辑
                        block_res = MaliciousIPService.block_ip(
                            ip_address=log.attacker_ip,
                            reason=f"自动封禁触发: {log.attack_description}",
                            duration=duration_seconds
                        )
                        if block_res.get('success'):
                            log.is_blocked = True
                            log.blocked_time = get_beijing_time()
                            db.session.commit()
                            
                except Exception as e:
                    print(f"自动记录或封禁恶意 IP 失败: {str(e)}")

            # 满足其中一个就算是恶意IP，触发WebSocket推送
            if final_is_malicious:
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
