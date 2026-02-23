# -*- coding: utf-8 -*-
"""
日志服务
处理日志相关的业务逻辑
"""

from model.log_model import Log
from model.honeypot_model import Honeypot
from model.match_rule_model import MatchRule
from service.ai_analysis_service import AIAnalysisService
from database import db
from datetime import datetime
from utils.time_utils import get_beijing_time
from typing import Dict, List, Optional, Tuple
import re
import threading


class LogService:
    """
    日志服务类
    提供日志查询、统计等功能
    """
    
    @staticmethod
    def get_logs(page: int = 1, per_page: int = 20, attack_type: str = None, 
                 threat_level: str = None, protocol: str = None, 
                 start_time: str = None, end_time: str = None, keyword: str = None) -> Tuple[List[Dict], Dict]:
        """
        分页查询日志（支持条件查询和关键字查询）
        
        参数:
            page: 页码，默认为1
            per_page: 每页数量，默认为20
            attack_type: 攻击类型过滤条件
            threat_level: 威胁等级过滤条件
            protocol: 协议类型过滤条件
            start_time: 开始时间过滤条件
            end_time: 结束时间过滤条件
            keyword: 关键字，可以匹配多个字段
            
        返回:
            Tuple[List[Dict], Dict]: 日志列表和分页信息
        """
        try:
            # 构建查询
            query = Log.query
            
            # 添加过滤条件
            if attack_type:
                query = query.filter(Log.attack_type == attack_type)
                
            if threat_level:
                query = query.filter(Log.threat_level == threat_level)
                
            if protocol:
                query = query.filter(Log.protocol == protocol)
                
            if start_time:
                # 将字符串转换为datetime对象
                start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(Log.attack_time >= start_datetime)
                
            if end_time:
                # 将字符串转换为datetime对象
                end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(Log.attack_time <= end_datetime)
            
            # 添加关键字查询条件
            if keyword:
                # 使用OR条件匹配多个字段
                query = query.filter(
                    Log.attack_type.like(f'%{keyword}%') |
                    Log.threat_level.like(f'%{keyword}%') |
                    Log.protocol.like(f'%{keyword}%') |
                    Log.source_ip.like(f'%{keyword}%') |
                    Log.target_ip.like(f'%{keyword}%') |
                    Log.attack_description.like(f'%{keyword}%') |
                    Log.raw_log.like(f'%{keyword}%') |
                    Log.request_path.like(f'%{keyword}%') |
                    Log.payload.like(f'%{keyword}%') |
                    Log.user_agent.like(f'%{keyword}%') |
                    Log.notes.like(f'%{keyword}%')
                )
            
            # 按攻击时间倒序排列
            query = query.order_by(Log.attack_time.desc())
            
            # 计算总数
            total = query.count()
            
            # 计算分页
            offset = (page - 1) * per_page
            logs = query.offset(offset).limit(per_page).all()
            
            # 转换为字典列表
            log_list = [log.to_dict() for log in logs]
            
            # 构建分页信息
            pagination = {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,  # 向上取整
                'has_prev': page > 1,
                'has_next': page * per_page < total,
                'prev_num': page - 1 if page > 1 else None,
                'next_num': page + 1 if page * per_page < total else None
            }
            
            return log_list, pagination
            
        except Exception as e:
            # 记录错误日志
            print(f"查询日志时发生错误: {str(e)}")
            return [], {'error': str(e)}

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[Dict]:
        """
        根据ID获取单条日志
        
        参数:
            log_id: 日志ID
            
        返回:
            Optional[Dict]: 日志信息，如果不存在则返回None
        """
        try:
            log = Log.query.get(log_id)
            if log:
                return log.to_dict()
            return None
        except Exception as e:
            print(f"根据ID查询日志时发生错误: {str(e)}")
            return None

    @staticmethod
    def get_attack_types() -> List[str]:
        """
        获取所有攻击类型
        
        返回:
            List[str]: 攻击类型列表
        """
        try:
            # 查询所有不重复的攻击类型
            attack_types = db.session.query(Log.attack_type).distinct().filter(Log.attack_type.isnot(None)).all()
            return [at[0] for at in attack_types]
        except Exception as e:
            print(f"获取攻击类型时发生错误: {str(e)}")
            return []

    @staticmethod
    def get_threat_levels() -> List[str]:
        """
        获取所有威胁等级
        
        返回:
            List[str]: 威胁等级列表
        """
        try:
            # 查询所有不重复的威胁等级
            threat_levels = db.session.query(Log.threat_level).distinct().filter(Log.threat_level.isnot(None)).all()
            return [tl[0] for tl in threat_levels]
        except Exception as e:
            print(f"获取威胁等级时发生错误: {str(e)}")
            return []

    @staticmethod
    def get_log_statistics() -> Dict:
        """
        获取日志统计信息
        
        返回:
            Dict: 统计信息
        """
        try:
            # 总日志数
            total_logs = Log.query.count()
            
            # 恶意日志数
            malicious_logs = Log.query.filter(Log.is_malicious == True).count()
            
            # 已阻断日志数
            blocked_logs = Log.query.filter(Log.is_blocked == True).count()
            
            # 按攻击类型统计
            attack_type_stats = db.session.query(
                Log.attack_type, 
                db.func.count(Log.id).label('count')
            ).filter(Log.attack_type.isnot(None)).group_by(Log.attack_type).all()
            
            # 按威胁等级统计
            threat_level_stats = db.session.query(
                Log.threat_level, 
                db.func.count(Log.id).label('count')
            ).filter(Log.threat_level.isnot(None)).group_by(Log.threat_level).all()
            
            # 按日期统计最近7天的日志
            from datetime import timedelta
            seven_days_ago = get_beijing_time() - timedelta(days=7)
            daily_stats = db.session.query(
                db.func.date(Log.attack_time).label('date'),
                db.func.count(Log.id).label('count')
            ).filter(Log.attack_time >= seven_days_ago).group_by(db.func.date(Log.attack_time)).all()
            
            return {
                'total_logs': total_logs,
                'malicious_logs': malicious_logs,
                'blocked_logs': blocked_logs,
                'attack_type_stats': [{'type': at[0], 'count': at[1]} for at in attack_type_stats],
                'threat_level_stats': [{'level': tl[0], 'count': tl[1]} for tl in threat_level_stats],
                'daily_stats': [{'date': str(ds[0]), 'count': ds[1]} for ds in daily_stats]
            }
        except Exception as e:
            print(f"获取日志统计信息时发生错误: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def create_log(log_data: Dict) -> Dict:
        """
        创建日志记录
        
        参数:
            log_data: 日志数据字典
            
        返回:
            Dict: 创建结果
        """
        try:
            # 查找对应的蜜罐
            honeypot_port = log_data.get('honeypot_port')
            honeypot = Honeypot.query.filter_by(port=honeypot_port).first()
            
            if not honeypot:
                return {'error': f'未找到端口为 {honeypot_port} 的蜜罐'}
            
            # 初始化字段
            attack_type = log_data.get('attack_type')
            threat_level = log_data.get('threat_level', 'low')
            attack_description = log_data.get('attack_description')
            is_malicious = True  # 蜜罐捕获的默认标记为恶意
            
            # 规则匹配逻辑
            try:
                # 获取所有启用的规则，按优先级排序
                rules = MatchRule.query.filter_by(is_enabled=True).order_by(MatchRule.priority.asc()).all()
                
                for rule in rules:
                    # 获取待匹配的内容
                    match_content = log_data.get(rule.match_field)
                    
                    # 如果指定字段为空，尝试匹配raw_log
                    if match_content is None and rule.match_field != 'raw_log':
                         # 如果指定字段不存在但有raw_log，也可以尝试匹配raw_log(视需求而定，这里暂且严格匹配)
                         pass
                    
                    # 确保内容为字符串
                    if match_content is not None:
                        content_str = str(match_content)
                        # 执行正则匹配
                        if re.search(rule.regex_pattern, content_str, re.IGNORECASE):
                            # 匹配成功，更新攻击信息
                            attack_type = rule.attack_type
                            threat_level = rule.threat_level
                            
                            # 更新描述
                            rule_msg = f"触发规则: {rule.name}"
                            if not attack_description:
                                attack_description = rule_msg
                            else:
                                if rule_msg not in attack_description:
                                    attack_description += f" | {rule_msg}"
                            
                            # 更新规则统计信息
                            rule.match_count += 1
                            rule.last_matched = get_beijing_time()
                            
                            # 匹配到一个规则后停止（优先级高的先生效）
                            break
                            
            except Exception as e:
                print(f"规则匹配过程出错: {str(e)}")
                # 继续执行，确保日志能保存
            
            # 创建新的日志对象
            log = Log(
                honeypot_id=honeypot.id,
                attacker_ip=log_data.get('attacker_ip'),
                attack_time=get_beijing_time(),
                raw_log=log_data.get('raw_log'),
                source_ip=log_data.get('attacker_ip'),
                target_ip=log_data.get('target_ip', '127.0.0.1'),
                source_port=log_data.get('attacker_port'),
                target_port=log_data.get('honeypot_port'),
                protocol=log_data.get('protocol'),
                user_agent=log_data.get('user_agent'),
                request_path=log_data.get('request_path'),
                attack_type=attack_type,
                attack_description=attack_description,
                payload=log_data.get('payload'),
                threat_level=threat_level,
                is_malicious=is_malicious,
                notes=log_data.get('notes')
            )
            
            # 保存到数据库
            db.session.add(log)
            db.session.commit()
            
            # 异步执行AI分析（避免阻塞主流程）
            try:
                def run_ai_analysis(app, log_id, log_data_dict):
                    with app.app_context():
                        try:
                            # 重新获取日志对象
                            log_entry = Log.query.get(log_id)
                            if not log_entry:
                                return
                            
                            # 执行分析
                            ai_result = AIAnalysisService.analyze_log(log_data_dict)
                            
                            # 更新日志字段
                            log_entry.ai_attack_type = ai_result.get('ai_attack_type')
                            log_entry.ai_confidence = ai_result.get('ai_confidence')
                            log_entry.ai_analysis_result = ai_result.get('ai_analysis_result')
                            
                            db.session.commit()
                            print(f"日志 ID {log_id} AI分析完成: {ai_result.get('ai_attack_type')}")
                            
                        except Exception as e:
                            print(f"异步AI分析出错: {str(e)}")
                            
                # 获取当前app实例以便在线程中使用上下文
                from flask import current_app
                # 需要使用app的真实代理，因为current_app是线程局部的
                # 注意：在某些部署方式下，这种传递app的方式可能需要调整
                # 这里假设是简单的单进程部署
                app = current_app._get_current_object()
                
                # 准备传给线程的数据（避免直接传ORM对象）
                log_data_dict = log.to_dict()
                # 补充可能缺少的原始字段
                log_data_dict['payload'] = log.payload
                log_data_dict['protocol'] = log.protocol
                log_data_dict['request_path'] = log.request_path
                
                thread = threading.Thread(
                    target=run_ai_analysis,
                    args=(app, log.id, log_data_dict)
                )
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                print(f"启动AI分析线程失败: {str(e)}")
            
            # 如果是恶意流量，记录到恶意IP表
            if is_malicious:
                try:
                    from service.malicious_ip_service import MaliciousIPService
                    MaliciousIPService.record_malicious_ip(
                        ip_address=log.attacker_ip,
                        attack_type=log.attack_type,
                        threat_level=log.threat_level,
                        source_honeypot_id=log.honeypot_id,
                        notes=f"触发日志ID: {log.id}"
                    )
                except Exception as e:
                    print(f"自动记录恶意IP失败: {str(e)}")
            
            return {
                'log_id': log.id,
                'status': 'created',
                'message': '日志创建成功'
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"创建日志时发生错误: {str(e)}")
            return {'error': str(e)}
