# -*- coding: utf-8 -*-
"""
仪表盘服务
提供攻击趋势、排名、地图等统计数据
"""

from model.log_model import Log
from model.malicious_ip_model import MaliciousIP
from database import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta

class DashboardService:
    """
    仪表盘服务类
    """
    
    @staticmethod
    def get_attack_trend(days=7):
        """
        获取攻击趋势数据（最近N天）
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            print(f"DEBUG: Querying trend from {start_date} to {end_date}")

            # 按天统计
            results = db.session.query(
                func.date(Log.attack_time).label('date'),
                func.count(Log.id).label('count')
            ).filter(
                Log.attack_time >= start_date
            ).group_by(
                func.date(Log.attack_time)
            ).all()
            
            print(f"DEBUG: Raw query results: {results}")

            # 补全日期
            # 确保日期键为字符串格式
            date_map = {str(r[0]): r[1] for r in results}
            data = []
            
            for i in range(days):
                d = (start_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
                data.append({
                    'date': d,
                    'count': date_map.get(d, 0)
                })
                
            print(f"DEBUG: Final trend data: {data}")
            return data
            
        except Exception as e:
            print(f"获取攻击趋势失败: {e}")
            return []

    @staticmethod
    def get_attack_type_stats(limit=5):
        """
        获取攻击类型排名
        """
        try:
            results = db.session.query(
                Log.attack_type,
                func.count(Log.id).label('count')
            ).filter(
                Log.attack_type != None
            ).group_by(
                Log.attack_type
            ).order_by(
                desc('count')
            ).limit(limit).all()
            
            return [{'name': r[0], 'value': r[1]} for r in results]
            
        except Exception as e:
            print(f"获取攻击类型统计失败: {e}")
            return []

    @staticmethod
    def get_map_data():
        """
        获取世界地图数据（基于IP位置）
        注意：这依赖于 MaliciousIP 表中的 location 字段
        如果 MaliciousIP 表中数据不全，统计结果可能不准
        """
        try:
            # 统计 MaliciousIP 表中的 location
            results = db.session.query(
                MaliciousIP.location,
                func.count(MaliciousIP.id).label('count')
            ).filter(
                MaliciousIP.location != None
            ).group_by(
                MaliciousIP.location
            ).all()
            
            # 简单的归一化处理，例如 'China' -> 'China', 'CN' -> 'China'
            # 这里假设 location 已经是标准格式或者需要在前端处理
            
            return [{'name': r[0], 'value': r[1]} for r in results]
            
        except Exception as e:
            print(f"获取地图数据失败: {e}")
            return []
            
    @staticmethod
    def get_summary_stats():
        """
        获取汇总数据
        """
        try:
            total_attacks = Log.query.count()
            today_attacks = Log.query.filter(func.date(Log.attack_time) == datetime.now().strftime('%Y-%m-%d')).count()
            malicious_ips = MaliciousIP.query.count()
            
            return {
                'total_attacks': total_attacks,
                'today_attacks': today_attacks,
                'malicious_ips': malicious_ips
            }
        except Exception as e:
            print(f"获取汇总数据失败: {e}")
            return {}
