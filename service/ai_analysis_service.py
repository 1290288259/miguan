# -*- coding: utf-8 -*-
"""
AI分析服务
对接Ollama本地大模型(deepseek-r1:7b)进行流量日志分析
"""

import requests
import json
import logging
import re
import threading
from typing import Dict, Optional
from service.ai_config_service import AIConfigService

# 配置日志
logger = logging.getLogger(__name__)

class AIAnalysisService:
    """
    AI分析服务类
    负责调用AI API进行日志分析
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
    def init_model(cls, app=None):
        """
        初始化AI模型
        检查Ollama服务状态，如果未启动则尝试启动，并预加载模型
        """
        import subprocess
        import time
        import socket

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
                
                # 仅针对本地Ollama服务进行自动启动尝试
                if provider == 'ollama' and ('localhost' in api_url or '127.0.0.1' in api_url):
                    port = 11434 # 默认端口
                    try:
                        # 尝试从URL中解析端口
                        from urllib.parse import urlparse
                        parsed = urlparse(api_url)
                        if parsed.port:
                            port = parsed.port
                    except:
                        pass

                    # 1. 检查端口是否开放
                    def is_port_open(host, port):
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(1)
                        try:
                            s.connect((host, port))
                            s.close()
                            return True
                        except:
                            return False

                    ollama_ready = False
                    if not is_port_open("localhost", port):
                        print(f"Ollama服务(端口{port})未运行，正在尝试启动...")
                        try:
                            # Windows下尝试启动ollama serve
                            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                            
                            # 等待服务启动
                            print("正在等待Ollama服务就绪...")
                            for _ in range(20):  # 最多等待20秒
                                if is_port_open("localhost", port):
                                    print("Ollama服务已启动")
                                    ollama_ready = True
                                    break
                                time.sleep(1)
                        except Exception as e:
                            print(f"启动Ollama服务失败: {str(e)}")
                    else:
                        ollama_ready = True

                    if ollama_ready:
                        # 2. 预加载模型
                        print(f"正在预加载模型 {model_name}...")
                        try:
                            # 发送一个简单的请求来触发模型加载
                            payload = {
                                "model": model_name,
                                "prompt": "hi", 
                                "stream": False,
                                "keep_alive": "1h"
                            }
                            requests.post(api_url, json=payload, timeout=60)
                            print(f"模型 {model_name} 预加载完成")
                        except Exception as e:
                            print(f"模型预加载请求发送失败 (可能是超时，模型仍在后台加载): {str(e)}")
                    else:
                        print("Ollama服务无法启动，AI分析功能可能不可用")
                else:
                    print(f"当前AI配置 ({provider} - {model_name}) 不需要本地自动启动检查")
            
            except Exception as e:
                print(f"初始化AI模型失败: {e}")
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
        """
        try:
            # 获取配置
            config = cls.get_active_config()
            
            # 构造Prompt
            prompt = cls._build_prompt(log_data)
            
            # 调用API
            response_text = cls._call_ai_api(prompt, config)
            
            if not response_text:
                return {
                    "ai_attack_type": "Unknown",
                    "ai_confidence": 0.0,
                    "ai_analysis_result": "AI分析失败: 无法连接到模型或无响应"
                }
            
            # 解析结果
            result = cls._parse_response(response_text)
            return result
            
        except Exception as e:
            logger.error(f"AI分析过程中出错: {str(e)}")
            return {
                "ai_attack_type": "Error",
                "ai_confidence": 0.0,
                "ai_analysis_result": f"AI分析出错: {str(e)}"
            }
    
    @classmethod
    def _build_prompt(cls, log_data: Dict) -> str:
        """
        构造分析Prompt
        """
        raw_log = log_data.get('raw_log', '')
        protocol = log_data.get('protocol', 'Unknown')
        request_path = log_data.get('request_path', '')
        payload = log_data.get('payload', '')
        
        prompt = f"""
你是一个网络安全专家，请分析以下蜜罐捕获的流量日志，判断其是否为恶意攻击。

日志信息:
- 协议: {protocol}
- 请求路径: {request_path}
- 载荷/内容: {payload if payload else raw_log}
- 原始日志: {raw_log}

请按照以下JSON格式返回结果，不要包含思考过程或其他废话，只要JSON：
{{
    "attack_type": "攻击类型(如: SQL注入, XSS, 暴力破解, 扫描, 正常流量, 未知)",
    "confidence": 0.0-1.0之间的置信度数值,
    "analysis": "简短的分析理由(中文)"
}}
"""
        return prompt
    
    @classmethod
    def _call_ai_api(cls, prompt: str, config: Dict) -> Optional[str]:
        """
        调用AI API
        """
        api_url = config['api_url']
        model_name = config['model_name']
        provider = config['provider']
        api_key = config['api_key']
        
        try:
            headers = {}
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
                
            if provider == 'ollama':
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
            
            # TODO: 支持其他提供商 (如OpenAI)
            # elif provider == 'openai':
            #     ...
            
            else:
                # 默认尝试Ollama格式
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")

            logger.error(f"API返回错误: {response.status_code} - {response.text}")
            return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"连接AI API失败: {str(e)}")
            return None
    
    @classmethod
    def _parse_response(cls, response_text: str) -> Dict[str, any]:
        """
        解析模型返回的JSON文本
        """
        try:
            # 移除可能的 <think> 标签内容
            clean_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                return {
                    "ai_attack_type": data.get("attack_type", "Unknown"),
                    "ai_confidence": float(data.get("confidence", 0.0)),
                    "ai_analysis_result": data.get("analysis", "无详细分析")
                }
            else:
                logger.warning(f"无法从模型响应中提取JSON: {response_text}")
                return {
                    "ai_attack_type": "Unknown",
                    "ai_confidence": 0.0,
                    "ai_analysis_result": f"解析失败，原始响应: {clean_text[:100]}..."
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return {
                "ai_attack_type": "Unknown",
                "ai_confidence": 0.0,
                "ai_analysis_result": "模型返回格式错误"
            }
