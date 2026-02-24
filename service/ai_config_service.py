# -*- coding: utf-8 -*-
"""
AI配置服务
处理AI配置相关的业务逻辑
"""

from model.ai_config_model import AIConfig
from database import db
from sqlalchemy.exc import IntegrityError
import requests
import time
import json

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
            # 获取当前激活的配置
            current_active = AIConfig.query.filter_by(is_active=True).first()
            
            # 取消所有激活
            AIConfig.query.update({AIConfig.is_active: False})
            
            # 激活当前
            config.is_active = True
            db.session.commit()
            
            # 本地模型服务管理逻辑
            try:
                from service.ai_analysis_service import AIAnalysisService
                
                # 定义判断是否为本地Ollama的辅助函数
                def is_local_ollama(cfg):
                    return cfg and cfg.provider == 'ollama' and ('localhost' in cfg.api_url or '127.0.0.1' in cfg.api_url)

                # 1. 如果之前是本地Ollama，且现在切到了非本地Ollama（或者是不同的本地Ollama），尝试停止旧的
                # 注意：如果只是从一个本地Ollama切到另一个本地Ollama，通常不需要停止服务，因为端口是一样的
                # 但如果用户明确想“切换”，我们可以保持服务运行。
                # 只有当切换到非本地模型时，才停止本地服务。
                if current_active and is_local_ollama(current_active):
                    if not is_local_ollama(config):
                        # 切换到了非本地模型，停止本地服务
                        AIAnalysisService.stop_local_ollama()
                
                # 2. 如果新激活的是本地Ollama，尝试启动
                if is_local_ollama(config):
                    # 在新线程中启动，避免阻塞接口返回
                    import threading
                    def start_service():
                        AIAnalysisService.ensure_local_ollama_started(config.api_url, config.model_name)
                    
                    t = threading.Thread(target=start_service)
                    t.daemon = True
                    t.start()
                    
            except Exception as e:
                print(f"本地模型服务自动管理失败: {e}")

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def deactivate_config(config_id):
        """
        禁用指定配置
        """
        config = AIConfig.query.get(config_id)
        if not config:
            return False
            
        try:
            config.is_active = False
            db.session.commit()
            
            # 本地模型服务管理逻辑
            try:
                from service.ai_analysis_service import AIAnalysisService
                
                # 如果禁用的配置是本地Ollama，尝试停止服务
                if config.provider == 'ollama' and ('localhost' in config.api_url or '127.0.0.1' in config.api_url):
                    AIAnalysisService.stop_local_ollama()
                    
            except Exception as e:
                print(f"本地模型服务自动停止失败: {e}")

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

    @staticmethod
    def test_connection(config_id):
        """
        测试AI配置连接
        """
        config = AIConfig.query.get(config_id)
        if not config:
            raise ValueError("配置不存在")
            
        start_time = time.time()
        
        try:
            # 准备请求数据
            if config.provider == 'ollama':
                payload = {"model": config.model_name, "prompt": "Hello", "stream": False}
                headers = {"Content-Type": "application/json"}
                if config.api_key: headers["Authorization"] = f"Bearer {config.api_key}"
            elif config.provider == 'openai':
                payload = {"model": config.model_name, "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.api_key}"}
            else:
                raise ValueError(f"不支持的提供商: {config.provider}")

            # 发送请求函数
            def send_request(url):
                return requests.post(url, json=payload, headers=headers, timeout=10)

            # 第一次尝试
            try:
                response = send_request(config.api_url)
            except requests.exceptions.ConnectionError:
                raise Exception("连接失败：无法连接到目标服务器，请检查地址和端口是否正确，以及 Ollama 服务是否已启动。")
            except requests.exceptions.Timeout:
                raise Exception("连接超时：服务器响应时间过长。")

            # 智能重试逻辑：处理 404
            if response.status_code == 404:
                new_url = None
                if config.provider == 'openai' and 'chat/completions' not in config.api_url:
                    base = config.api_url.rstrip('/')
                    new_url = f"{base}/chat/completions"
                elif config.provider == 'ollama' and 'api/generate' not in config.api_url:
                    base = config.api_url.rstrip('/')
                    new_url = f"{base}/api/generate"
                
                if new_url:
                    try:
                        response = send_request(new_url)
                    except:
                        pass # 如果重试失败，保持原来的 response

            # 处理响应
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            response_text = ""
            
            if config.provider == 'ollama':
                response_text = data.get('response', '')
            elif config.provider == 'openai':
                if 'choices' in data and len(data['choices']) > 0:
                    response_text = data['choices'][0]['message']['content']
                else:
                    response_text = "No response content"

            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "success": True,
                "latency": latency,
                "response": response_text[:100] + "..." if len(response_text) > 100 else response_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
