# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseSkill(ABC):
    """
    基础技能类 (MCP Skill Interface)
    所有Agent技能都应该继承此类
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @abstractmethod
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        执行技能
        :param input_data: 输入数据
        :param context: 上下文信息
        :return: 执行结果字典，如果无法处理则返回None
        """
        pass

class SkillRegistry:
    """
    技能注册表
    用于管理和检索可用技能
    """
    _skills: Dict[str, BaseSkill] = {}
    
    @classmethod
    def register(cls, skill: BaseSkill):
        """注册一个技能"""
        cls._skills[skill.name] = skill
        print(f"Skill registered: {skill.name}")
        
    @classmethod
    def get_skill(cls, name: str) -> Optional[BaseSkill]:
        """获取指定名称的技能"""
        return cls._skills.get(name)
        
    @classmethod
    def get_all_skills(cls) -> Dict[str, BaseSkill]:
        """获取所有已注册技能"""
        return cls._skills.copy()
