# -*- coding: utf-8 -*-
"""
AI分析服务
对接Ollama本地大模型(deepseek-r1:7b)进行流量日志分析
已重构为使用独立的 TrafficAnalysisAgent
"""

import logging
import threading
from typing import Dict
from service.ai_config_service import AIConfigService
from agent.core import TrafficAnalysisAgent
from agent.llm_client import LLMClient

# 配置日志
logger = logging.getLogger(__name__)

class AIAnalysisService:
    """
    AI分析服务类
    负责调用 TrafficAnalysisAgent 进行日志分析
    """
    
    # 默认配置 (用于回退或初始化)
    DEFAULT_API_URL = "http://localhost:11434/api/generate"
    DEFAULT_MODEL_NAME = "deepseek-r1:7b"
    
    @classmethod
    def get_active_config(cls):
        """
        获取当前激活的配置
        """
        try:
            config = AIConfigService.get_active_config()
            if config:
                return {
                    "api_url": config.api_url,
                    "model_name": config.model_name,
                    "provider": config.provider,
                    "api_key": config.api_key
                }
        except Exception as e:
            logger.error(f"获取AI配置失败: {e}")
        
        # 回退到默认配置
        return {
            "api_url": cls.DEFAULT_API_URL,
            "model_name": cls.DEFAULT_MODEL_NAME,
            "provider": "ollama",
            "api_key": None
        }

    @classmethod
    def ensure_local_ollama_started(cls, api_url, model_name):
        """
        检查并尝试启动本地Ollama服务
        代理给 LLMClient 处理
        """
        return LLMClient.ensure_local_ollama_started(api_url, model_name)

    @classmethod
    def stop_local_ollama(cls):
        """
        停止本地Ollama服务
        代理给 LLMClient 处理
        """
        return LLMClient.stop_local_ollama()

    @classmethod
    def init_model(cls, app=None):
        """
        初始化AI模型
        仅加载当前激活配置，不再自动启动本地 Ollama 服务
        """
        def _init_process(app_obj):
            # 如果提供了app对象，则使用上下文
            context = app_obj.app_context() if app_obj else None
            if context:
                context.push()
            
            try:
                # 获取配置
                config = cls.get_active_config()
                api_url = config['api_url']
                model_name = config['model_name']
                provider = config['provider']
                
                # 记录当前配置，不再自动启动服务
                print(f"AI模型初始化完成: 使用 {provider} 模型 {model_name}")
                logger.info(f"AI模型初始化完成: 使用 {provider} 模型 {model_name}")
            
            except Exception as e:
                print(f"初始化AI模型失败: {e}")
                logger.error(f"初始化AI模型失败: {e}")
            finally:
                if context:
                    context.pop()

        # 在新线程中执行初始化，避免阻塞主程序启动
        thread = threading.Thread(target=_init_process, args=(app,))
        thread.daemon = True
        thread.start()

    @classmethod
    def analyze_log(cls, log_data: Dict) -> Dict[str, any]:
        """
        分析日志内容
        使用 TrafficAnalysisAgent 进行分析
        """
        try:
            # 获取配置
            config = cls.get_active_config()
            
            # 初始化 Agent
            agent = TrafficAnalysisAgent(config)
            
            # 执行分析
            result = agent.analyze(log_data)
            
            return result
            
        except Exception as e:
            logger.error(f"AI分析过程中出错: {str(e)}")
            return {
                "ai_attack_type": "Error",
                "ai_confidence": 0.0,
                "ai_analysis_result": f"AI分析出错: {str(e)}"
            }
