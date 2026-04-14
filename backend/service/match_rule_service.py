# -*- coding: utf-8 -*-
"""
匹配规则服务
处理匹配规则相关的业务逻辑
"""

from model.match_rule_model import MatchRule
from database import db
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class MatchRuleService:
    """
    匹配规则服务类
    提供匹配规则的增删改查功能
    """
    
    @staticmethod
    def get_rules(page: int = 1, per_page: int = 20, attack_type: str = None, 
                 threat_level: str = None, is_enabled: bool = None, keyword: str = None) -> Tuple[List[Dict], Dict]:
        """
        分页查询匹配规则（支持条件查询和关键字查询）
        
        参数:
            page: 页码，默认为1
            per_page: 每页数量，默认为20
            attack_type: 攻击类型过滤条件
            threat_level: 威胁等级过滤条件
            is_enabled: 是否启用过滤条件
            keyword: 关键字，可以匹配多个字段
            
        返回:
            Tuple[List[Dict], Dict]: 规则列表和分页信息
        """
        try:
            # 构建查询
            query = MatchRule.query
            
            # 添加过滤条件
            if attack_type:
                query = query.filter(MatchRule.attack_type == attack_type)
                
            if threat_level:
                query = query.filter(MatchRule.threat_level == threat_level)
                
            if is_enabled is not None:
                query = query.filter(MatchRule.is_enabled == is_enabled)
            
            # 添加关键字查询条件
            if keyword:
                # 使用OR条件匹配多个字段
                query = query.filter(
                    MatchRule.name.like(f'%{keyword}%') |
                    MatchRule.attack_type.like(f'%{keyword}%') |
                    MatchRule.threat_level.like(f'%{keyword}%') |
                    MatchRule.description.like(f'%{keyword}%') |
                    MatchRule.regex_pattern.like(f'%{keyword}%')
                )
            
            # 按优先级升序排列，优先级高的排在前面
            query = query.order_by(MatchRule.priority.asc(), MatchRule.id.desc())
            
            # 计算总数
            total = query.count()
            
            # 计算分页
            offset = (page - 1) * per_page
            rules = query.offset(offset).limit(per_page).all()
            
            # 转换为字典列表
            rule_list = [rule.to_dict() for rule in rules]
            
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
            
            return rule_list, pagination
            
        except Exception as e:
            # 记录错误日志
            print(f"查询匹配规则时发生错误: {str(e)}")
            return [], {'error': str(e)}
    
    @staticmethod
    def get_rule_by_id(rule_id: int) -> Optional[Dict]:
        """
        根据ID获取单条匹配规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            Optional[Dict]: 规则信息，如果不存在则返回None
        """
        try:
            rule = MatchRule.query.get(rule_id)
            if rule:
                return rule.to_dict()
            return None
        except Exception as e:
            print(f"根据ID查询匹配规则时发生错误: {str(e)}")
            return None
    
    @staticmethod
    def create_rule(rule_data: Dict) -> Dict:
        """
        创建匹配规则
        
        参数:
            rule_data: 规则数据字典
            
        返回:
            Dict: 创建结果
        """
        try:
            import re
            pattern = rule_data.get('regex_pattern')
            if pattern:
                try:
                    re.compile(pattern)
                except re.error as e:
                    return {'error': f'正则表达式语法错误: {str(e)}'}

            # 创建新的规则对象
            rule = MatchRule(
                name=rule_data.get('name'),
                attack_type=rule_data.get('attack_type'),
                regex_pattern=rule_data.get('regex_pattern'),
                threat_level=rule_data.get('threat_level', 'medium'),
                description=rule_data.get('description'),
                match_field=rule_data.get('match_field', 'raw_log'),
                is_enabled=rule_data.get('is_enabled', True),
                priority=rule_data.get('priority', 100),
                auto_block=rule_data.get('auto_block', False),
                block_duration=rule_data.get('block_duration', 0),
                created_by=rule_data.get('created_by')
            )
            
            # 保存到数据库
            db.session.add(rule)
            db.session.commit()
            
            return {
                'rule_id': rule.id,
                'status': 'created',
                'message': '匹配规则创建成功'
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"创建匹配规则时发生错误: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def update_rule(rule_id: int, rule_data: Dict) -> Dict:
        """
        更新匹配规则
        
        参数:
            rule_id: 规则ID
            rule_data: 规则数据字典
            
        返回:
            Dict: 更新结果
        """
        try:
            # 查找规则
            rule = MatchRule.query.get(rule_id)
            
            if not rule:
                return {
                    'error': f'未找到ID为 {rule_id} 的匹配规则'
                }
            
            # 更新规则字段
            if 'name' in rule_data:
                rule.name = rule_data['name']
            if 'attack_type' in rule_data:
                rule.attack_type = rule_data['attack_type']
            if 'regex_pattern' in rule_data:
                pattern = rule_data['regex_pattern']
                import re
                try:
                    re.compile(pattern)
                except re.error as e:
                    return {'error': f'正则表达式语法错误: {str(e)}'}
                rule.regex_pattern = pattern
            if 'threat_level' in rule_data:
                rule.threat_level = rule_data['threat_level']
            if 'description' in rule_data:
                rule.description = rule_data['description']
            if 'match_field' in rule_data:
                rule.match_field = rule_data['match_field']
            if 'is_enabled' in rule_data:
                rule.is_enabled = rule_data['is_enabled']
            if 'priority' in rule_data:
                rule.priority = rule_data['priority']
            if 'auto_block' in rule_data:
                rule.auto_block = rule_data['auto_block']
            if 'block_duration' in rule_data:
                rule.block_duration = rule_data['block_duration']
            
            # 更新时间会自动更新
            db.session.commit()
            
            return {
                'rule_id': rule.id,
                'status': 'updated',
                'message': '匹配规则更新成功'
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"更新匹配规则时发生错误: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def delete_rule(rule_id: int) -> Dict:
        """
        删除匹配规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            Dict: 删除结果
        """
        try:
            # 查找规则
            rule = MatchRule.query.get(rule_id)
            
            if not rule:
                return {
                    'error': f'未找到ID为 {rule_id} 的匹配规则'
                }
            
            # 删除规则
            db.session.delete(rule)
            db.session.commit()
            
            return {
                'rule_id': rule_id,
                'status': 'deleted',
                'message': '匹配规则删除成功'
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"删除匹配规则时发生错误: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def toggle_rule_status(rule_id: int) -> Dict:
        """
        切换匹配规则的启用状态
        
        参数:
            rule_id: 规则ID
            
        返回:
            Dict: 切换结果
        """
        try:
            # 查找规则
            rule = MatchRule.query.get(rule_id)
            
            if not rule:
                return {
                    'error': f'未找到ID为 {rule_id} 的匹配规则'
                }
            
            # 切换启用状态
            rule.is_enabled = not rule.is_enabled
            db.session.commit()
            
            return {
                'rule_id': rule_id,
                'is_enabled': rule.is_enabled,
                'status': 'toggled',
                'message': f'匹配规则已{"启用" if rule.is_enabled else "禁用"}'
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"切换匹配规则状态时发生错误: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def get_attack_types() -> List[str]:
        """
        获取所有攻击类型
        
        返回:
            List[str]: 攻击类型列表
        """
        try:
            # 使用distinct获取不重复的攻击类型
            attack_types = db.session.query(MatchRule.attack_type).filter(
                MatchRule.attack_type.isnot(None)
            ).distinct().all()
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
            threat_levels = db.session.query(MatchRule.threat_level).filter(
                MatchRule.threat_level.isnot(None)
            ).distinct().all()
            # 提取值并过滤掉空值
            return [tl[0] for tl in threat_levels if tl[0]]
        except Exception as e:
            print(f"获取威胁等级时发生错误: {str(e)}")
            return []
