# -*- coding: utf-8 -*-
"""
AI分析服务
对接Ollama本地大模型(deepseek-r1:7b)进行流量日志分析
已重构为使用独立的 TrafficAnalysisAgent
"""

import logging
import threading
import queue
import time
from typing import Dict
from service.ai_config_service import AIConfigService
from agent.core import TrafficAnalysisAgent
from agent.llm_client import LLMClient
from model.log_model import Log
from database import db

# 配置日志
logger = logging.getLogger(__name__)

class AIAnalysisService:
    """
    AI分析服务类
    负责调用 TrafficAnalysisAgent 进行日志分析
    """
    
    # 任务队列
    _task_queue = queue.Queue()
    _worker_thread = None
    
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
                    "api_key": config.api_key,
                    "is_auto_block": config.is_auto_block
                }
        except Exception as e:
            logger.error(f"获取AI配置失败: {e}")
        
        # 回退到默认配置
        return {
            "api_url": cls.DEFAULT_API_URL,
            "model_name": cls.DEFAULT_MODEL_NAME,
            "provider": "ollama",
            "api_key": None,
            "is_auto_block": False
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
        1. 仅加载当前激活配置，不再自动启动本地 Ollama 服务
        2. 启动后台分析任务队列Worker
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
        
        # 启动队列处理Worker
        if app:
            cls.start_worker(app)

    @classmethod
    def start_worker(cls, app):
        """启动后台处理线程"""
        if cls._worker_thread and cls._worker_thread.is_alive():
            return

        def worker_loop():
            print("AI分析任务队列Worker已启动")
            while True:
                try:
                    # 获取任务，阻塞等待
                    task = cls._task_queue.get()
                    if task is None:
                        break
                    
                    log_id, log_data = task
                    
                    # 为每个任务创建新的应用上下文
                    with app.app_context():
                        try:
                            cls._process_single_log(log_id, log_data)
                        except Exception as e:
                            logger.error(f"处理日志 {log_id} 失败: {e}")
                            print(f"处理日志 {log_id} 失败: {e}")
                        finally:
                            # 标记任务完成
                            cls._task_queue.task_done()
                            
                except Exception as e:
                    logger.error(f"Worker循环异常: {e}")
                    time.sleep(1) # 防止死循环刷屏

        cls._worker_thread = threading.Thread(target=worker_loop, daemon=True)
        cls._worker_thread.start()

    @classmethod
    def add_task(cls, log_id, log_data):
        """添加分析任务到队列"""
        cls._task_queue.put((log_id, log_data))
        qsize = cls._task_queue.qsize()
        if qsize > 10:
            logger.warning(f"AI分析队列堆积: {qsize} 个任务等待中")

    @classmethod
    def _process_single_log(cls, log_id, log_data_dict):
        """处理单条日志分析 (从LogService迁移过来的逻辑)"""
        try:
            # 重新获取日志对象
            log_entry = Log.query.get(log_id)
            if not log_entry:
                logger.warning(f"日志 ID {log_id} 不存在，跳过分析")
                return
            
            # 执行分析
            ai_result = cls.analyze_log(log_data_dict)
            
            # 更新日志字段
            ai_attack_type = ai_result.get('ai_attack_type')
            log_entry.ai_attack_type = ai_attack_type
            log_entry.ai_confidence = ai_result.get('ai_confidence')
            log_entry.ai_analysis_result = ai_result.get('ai_analysis_result')
            
            # 判断与规则匹配是否一致
            rule_is_malicious = log_entry.is_malicious
            
            # 归一化 AI 判定结果
            safe_types = ['normal', 'page visit', 'safe', 'unknown', '正常流量', '正常']
            ai_type_lower = ai_attack_type.lower() if ai_attack_type else 'unknown'
            ai_is_malicious = ai_type_lower not in safe_types
            
            # 特殊处理: 如果规则判定为 'Web Visit' 且 AI 判定为正常流量，视为一致
            rule_attack_type = log_entry.attack_type
            if rule_attack_type and rule_attack_type.lower() == 'web visit' and not ai_is_malicious:
                log_entry.ai_rule_match_consistency = '一致'
            elif rule_is_malicious == ai_is_malicious:
                log_entry.ai_rule_match_consistency = '一致'
            else:
                log_entry.ai_rule_match_consistency = '不一致'
            
            db.session.commit()
            print(f"日志 ID {log_id} AI分析完成: {ai_attack_type}, 一致性: {log_entry.ai_rule_match_consistency}")
            
            # 如果是恶意流量，自动记录到恶意IP表 (如果配置了自动封禁，Agent内部已经处理了封禁，这里只记录DB)
            # 注意: Agent.analyze 内部已经有了自动封禁逻辑 (lines 84-93 in core.py)
            # 但这里还需要调用 MaliciousIPService.record_malicious_ip 来记录到数据库?
            # 查看原 LogService 逻辑，是在 analyze 之后调用的。
            # 原逻辑中: is_malicious 是规则判断的结果!
            # 等等，原逻辑是在线程外部判断 is_malicious (规则结果) 然后记录 IP。
            # 线程内部只做 AI 分析。
            # 所以这里不需要做 IP 记录，IP 记录在 LogService 主流程中已经完成了。
            # 只有 AI 的自动封禁 (BlockIPSkill) 是在 Agent 内部做的。
            
        except Exception as e:
            logger.error(f"处理日志 {log_id} 过程出错: {str(e)}")
            db.session.rollback()

    @classmethod
    def analyze_log(cls, log_data: Dict) -> Dict[str, any]:
        """
        分析日志内容
        使用 TrafficAnalysisAgent 进行分析
        """
        try:
            # 获取配置
            config = cls.get_active_config()
            logger.info(f"AI分析使用配置: {config.get('model_name')}, 自动封禁: {config.get('is_auto_block')}")
            
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
