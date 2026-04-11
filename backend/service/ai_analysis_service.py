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
    def get_all_active_configs(cls):
        """
        获取所有激活的配置列表
        """
        try:
            configs = AIConfigService.get_all_active_configs()
            result = []
            for config in configs:
                # 返回包含id的字典，以便后续识别
                result.append({
                    "id": config.id,
                    "api_url": config.api_url,
                    "model_name": config.model_name,
                    "provider": config.provider,
                    "api_key": config.api_key,
                    "is_auto_block": config.is_auto_block
                })
            return result
        except Exception as e:
            logger.error(f"获取所有AI配置失败: {e}")
            return []

    @classmethod
    def init_model(cls, app=None):
        """
        初始化AI模型
        启动后台分析任务队列Workers（每个激活的模型一个Worker）
        """
        # 启动队列处理Workers
        if app:
            cls.start_workers(app)

    _worker_thread = False  # 改为False表示未启动，或者作为状态标志
    _running_workers = {}   # 存储正在运行的Worker信息: {config_id: {'thread': thread, 'stop_flag': Event}}

    @classmethod
    def start_workers(cls, app):
        """启动/刷新后台处理线程池"""
        cls.refresh_workers(app)

    @classmethod
    def refresh_workers(cls, app):
        """根据当前激活的配置刷新Worker线程"""
        # 解决current_app在线程中无法使用的问题
        # 如果传入的是LocalProxy，需要获取真实对象
        from werkzeug.local import LocalProxy
        real_app = app
        if isinstance(app, LocalProxy):
            real_app = app._get_current_object()

        # 获取所有激活的配置
        with real_app.app_context():
            configs = cls.get_all_active_configs()
        
        if not configs:
            # 如果没有配置，且没有默认Worker运行中，则启动默认Worker
            # 这里简化逻辑：如果没有配置，就不启动任何Worker，或者保留默认逻辑
            # 但考虑到多模型，最好是只运行已激活的。
            # 如果没有任何激活配置，可能需要警告
            if not cls._running_workers:
                 print("未找到激活的AI配置，且无运行中的Worker")
            # 这里的默认配置逻辑可能需要调整，暂时保留原有逻辑的变体：
            # 如果数据库真没配置，可以不启动，等待用户配置。
            pass

        active_config_ids = set()
        
        # 1. 启动新激活的配置对应的Worker
        for config in configs:
            # config 是字典
            config_id = config.get('id')
            active_config_ids.add(config_id)
            
            if config_id not in cls._running_workers:
                print(f"正在启动 AI Worker: {config.get('model_name')} (ID: {config_id})")
                stop_event = threading.Event()
                
                # 捕获循环变量
                def create_worker(cfg_copy, worker_id, stop_evt):
                    def worker_loop():
                        model_name = cfg_copy.get('model_name', 'Unknown')
                        print(f"AI Worker-{worker_id} ({model_name}) 已启动")
                        while not stop_evt.is_set():
                            # 获取任务，阻塞等待
                            try:
                                # 使用timeout以便能够响应停止信号
                                try:
                                    task = cls._task_queue.get(timeout=2)
                                except: # queue.Empty
                                    continue
                                
                                if task is None:
                                    break
                                
                                log_id, log_data = task
                                
                                # 为每个任务创建新的应用上下文
                                with real_app.app_context():
                                    try:
                                        cls._process_single_log(log_id, log_data, cfg_copy)
                                    except Exception as e:
                                        logger.error(f"Worker-{worker_id} 处理日志 {log_id} 失败: {e}")
                                        print(f"Worker-{worker_id} 处理日志 {log_id} 失败: {e}")
                                    finally:
                                        # 标记任务完成
                                        cls._task_queue.task_done()
                                        
                            except Exception as e:
                                logger.error(f"Worker-{worker_id} 循环异常: {e}")
                                time.sleep(1) # 防止死循环刷屏
                        print(f"AI Worker-{worker_id} ({model_name}) 已停止")

                    t = threading.Thread(target=worker_loop, daemon=True)
                    t.start()
                    return t

                thread = create_worker(config, config_id, stop_event)
                cls._running_workers[config_id] = {
                    'thread': thread,
                    'stop_flag': stop_event,
                    'model_name': config.get('model_name')
                }
        
        # 2. 停止不再激活的配置对应的Worker
        # 注意：要在循环外修改字典，先收集要删除的ID
        to_remove = []
        for config_id, worker_info in cls._running_workers.items():
            if config_id not in active_config_ids:
                print(f"正在停止 AI Worker: {worker_info['model_name']} (ID: {config_id})")
                worker_info['stop_flag'].set()
                # 不需要join，让它自然结束
                to_remove.append(config_id)
        
        for config_id in to_remove:
            del cls._running_workers[config_id]

        cls._worker_thread = True # 标记服务已初始化

    @classmethod
    def add_task(cls, log_id, log_data):
        """添加分析任务到队列"""
        cls._task_queue.put((log_id, log_data))
        qsize = cls._task_queue.qsize()
        if qsize > 10:
            logger.warning(f"AI分析队列堆积: {qsize} 个任务等待中")

    @classmethod
    def _process_single_log(cls, log_id, log_data_dict, config=None):
        """
        处理单条日志的AI分析。
        
        作为多级识别引擎的第三级（AI深度分析），在正则匹配和暴力破解检测之后，
        AI大模型进行深度综合分析，最终敲定并记录完整的攻击描述与威胁等级。
        """
        try:
            # 重新获取日志对象
            log_entry = Log.query.get(log_id)
            if not log_entry:
                logger.warning(f"日志 ID {log_id} 不存在，跳过分析")
                return
            
            # 暴力破解已由系统引擎确定，AI直接确认一致，无需重复分析
            if log_entry.attack_type == '暴力破解':
                ai_result = {
                    'ai_attack_type': '暴力破解',
                    'ai_confidence': 100.0,
                    'ai_analysis_result': '本系统已经确定判定此流量为暴力破解行为，AI确认一致（置信度100%）'
                }
            else:
                ai_result = cls.analyze_log(log_data_dict, config)
            
            # 更新AI分析字段
            ai_attack_type = ai_result.get('ai_attack_type')
            log_entry.ai_attack_type = ai_attack_type
            log_entry.ai_confidence = ai_result.get('ai_confidence')
            log_entry.ai_analysis_result = ai_result.get('ai_analysis_result')
            
            # 记录使用的模型名称
            if config:
                log_entry.ai_model_name = config.get('model_name')
            
            # ============================================================
            # AI最终敲定：将AI分析结果补充到主记录的攻击描述中
            # 如果前两级引擎（正则+频次）未识别出攻击，但AI识别出了，
            # 则用AI的判断更新主记录的 attack_type 和 threat_level
            # ============================================================
            ai_analysis_text = ai_result.get('ai_analysis_result', '')
            ai_confidence = float(ai_result.get('ai_confidence', 0.0))
            
            # 归一化 AI 判定结果
            safe_types = ['normal', 'page visit', 'safe', 'unknown', '正常流量', '正常']
            ai_type_lower = ai_attack_type.lower() if ai_attack_type else 'unknown'
            ai_is_malicious = ai_type_lower not in safe_types
            
            # AI高置信度判定为恶意，但前两级引擎未识别出攻击时：以AI结果更新主记录
            if ai_is_malicious and ai_confidence >= 0.7 and not log_entry.is_malicious:
                log_entry.attack_type = ai_attack_type
                log_entry.is_malicious = True
                # AI判定的威胁等级映射
                if ai_confidence >= 0.9:
                    log_entry.threat_level = 'high'
                elif ai_confidence >= 0.7:
                    log_entry.threat_level = 'medium'
                
                ai_desc = f"AI深度分析判定: {ai_attack_type} (置信度 {ai_confidence:.0%})"
                if log_entry.attack_description:
                    log_entry.attack_description += f" | {ai_desc}"
                else:
                    log_entry.attack_description = ai_desc
                    
                # 同步记录恶意IP（AI发现的新恶意流量）
                try:
                    from service.malicious_ip_service import MaliciousIPService
                    MaliciousIPService.record_malicious_ip(
                        ip_address=log_entry.attacker_ip,
                        attack_type=log_entry.attack_type,
                        threat_level=log_entry.threat_level,
                        source_honeypot_id=log_entry.honeypot_id,
                        notes=f"AI分析发现 - 日志 ID: {log_entry.id}",
                    )
                except Exception as e:
                    logger.error(f"AI分析后记录恶意IP失败: {e}")
            
            # 无论如何，将AI分析摘要追加到攻击描述中（便于审计）
            if ai_analysis_text and ai_attack_type not in ['Error', None]:
                ai_summary = f"[AI分析] {ai_analysis_text[:200]}"
                if log_entry.attack_description:
                    if '[AI分析]' not in log_entry.attack_description:
                        log_entry.attack_description += f" | {ai_summary}"
                else:
                    log_entry.attack_description = ai_summary
            
            # 计算一致性判断
            rule_is_malicious = log_entry.is_malicious
            rule_attack_type = log_entry.attack_type
            
            if rule_attack_type and rule_attack_type.lower() == '正常流量' and not ai_is_malicious:
                log_entry.ai_rule_match_consistency = '一致'
            elif rule_is_malicious == ai_is_malicious:
                log_entry.ai_rule_match_consistency = '一致'
            else:
                log_entry.ai_rule_match_consistency = '不一致'
            
            db.session.commit()
            model_info = f"[{config.get('model_name')}]" if config else ""
            print(f"日志 ID {log_id} AI分析完成 {model_info}: {ai_attack_type}, 一致性: {log_entry.ai_rule_match_consistency}")
            
        except Exception as e:
            logger.error(f"处理日志 {log_id} 过程出错: {str(e)}")
            db.session.rollback()

    @classmethod
    def analyze_log(cls, log_data: Dict, config: Dict = None) -> Dict[str, any]:
        """
        分析日志内容
        使用 TrafficAnalysisAgent 进行分析
        """
        try:
            # 获取配置 (如果没有传入，则获取默认激活配置 - 兼容旧调用)
            if config is None:
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
