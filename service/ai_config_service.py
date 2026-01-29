# -*- coding: utf-8 -*-
"""
AI配置服务
处理AI配置相关的业务逻辑
"""

from model.ai_config_model import AIConfig
from database import db
from sqlalchemy.exc import IntegrityError

class AIConfigService:
    """
    AI配置服务类
    """
    
    @staticmethod
    def create_config(data):
        """
        创建AI配置
        """
        try:
            # 如果是第一个配置，默认激活
            count = AIConfig.query.count()
            is_active = data.get('is_active', False)
            if count == 0:
                is_active = True
            
            # 如果设置为激活，先取消其他激活状态
            if is_active:
                AIConfig.query.update({AIConfig.is_active: False})
            
            config = AIConfig(
                name=data.get('name'),
                api_url=data.get('api_url'),
                model_name=data.get('model_name'),
                api_key=data.get('api_key'),
                provider=data.get('provider', 'ollama'),
                is_active=is_active,
                description=data.get('description')
            )
            
            db.session.add(config)
            db.session.commit()
            return config
        except IntegrityError:
            db.session.rollback()
            raise ValueError(f"配置名称 '{data.get('name')}' 已存在")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_all_configs():
        """
        获取所有配置
        """
        return AIConfig.query.order_by(AIConfig.created_at.desc()).all()

    @staticmethod
    def get_config_by_id(config_id):
        """
        根据ID获取配置
        """
        return AIConfig.query.get(config_id)

    @staticmethod
    def update_config(config_id, data):
        """
        更新配置
        """
        config = AIConfig.query.get(config_id)
        if not config:
            return None
        
        try:
            if 'name' in data:
                config.name = data['name']
            if 'api_url' in data:
                config.api_url = data['api_url']
            if 'model_name' in data:
                config.model_name = data['model_name']
            if 'api_key' in data:
                config.api_key = data['api_key']
            if 'provider' in data:
                config.provider = data['provider']
            if 'description' in data:
                config.description = data['description']
            
            # 这里的is_active更新通过activate_config专门处理，避免直接更新导致多选
            
            db.session.commit()
            return config
        except IntegrityError:
            db.session.rollback()
            raise ValueError(f"配置名称 '{data.get('name')}' 已存在")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_config(config_id):
        """
        删除配置
        """
        config = AIConfig.query.get(config_id)
        if not config:
            return False
        
        # 如果删除的是激活的配置，且还有其他配置，则激活最新的一个
        was_active = config.is_active
        
        db.session.delete(config)
        db.session.commit()
        
        if was_active:
            latest = AIConfig.query.order_by(AIConfig.created_at.desc()).first()
            if latest:
                latest.is_active = True
                db.session.commit()
                
        return True

    @staticmethod
    def activate_config(config_id):
        """
        激活指定配置
        """
        config = AIConfig.query.get(config_id)
        if not config:
            return False
            
        try:
            # 取消所有激活
            AIConfig.query.update({AIConfig.is_active: False})
            
            # 激活当前
            config.is_active = True
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_active_config():
        """
        获取当前激活的配置
        """
        return AIConfig.query.filter_by(is_active=True).first()
