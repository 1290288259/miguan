# -*- coding: utf-8 -*-
"""
日志服务
处理日志相关的业务逻辑
"""

from model.log_model import Log
from database import db
from datetime import datetime
from typing import Dict, List, Optional, Tuple


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
            # 使用distinct获取不重复的攻击类型
            attack_types = db.session.query(Log.attack_type).filter(Log.attack_type.isnot(None)).distinct().all()
            # 提取值并过滤掉空值
            return [at[0] for at in attack_types if at[0]]
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
            # 使用distinct获取不重复的威胁等级
            threat_levels = db.session.query(Log.threat_level).filter(Log.threat_level.isnot(None)).distinct().all()
            # 提取值并过滤掉空值
            return [tl[0] for tl in threat_levels if tl[0]]
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
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
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