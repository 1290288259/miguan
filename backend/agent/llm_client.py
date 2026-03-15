# -*- coding: utf-8 -*-
import requests
import json
import logging
import re
import threading
import socket
import time
import shutil
import os
import subprocess
from urllib.parse import urlparse
from typing import Dict, Optional, Any

# 配置日志
logger = logging.getLogger(__name__)

class LLMClient:
    """
    LLM 客户端
    负责与 AI 模型 API 进行通信，包含本地 Ollama 服务的管理
    """
    
    _start_lock = threading.Lock()
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 直接使用配置中的完整 URL，不再拼接
        self.api_url = config.get('api_url')
        self.model_name = config.get('model_name')
        self.provider = config.get('provider')
        self.api_key = config.get('api_key', '')
        
        if not self.api_url:
            # 如果没有配置 URL，提供一个默认值，但建议配置中必须包含完整 URL
            self.api_url = "http://localhost:11434/api/generate"
            logger.warning("未配置 API URL，使用默认值: http://localhost:11434/api/generate")
        else:
            # 规范化 URL: 根据 provider 自动补全 endpoint
            # 这不是为了判断环境，而是为了容错，防止用户只填写了 Base URL
            self.api_url = self.api_url.rstrip('/')
            
            if self.provider == 'openai':
                # OpenAI 兼容接口通常以 /chat/completions 结尾
                if not self.api_url.endswith('/chat/completions'):
                    # 如果以 /v1 结尾，直接追加
                    if self.api_url.endswith('/v1'):
                        self.api_url += '/chat/completions'
                    else:
                        # 否则尝试追加 (用户可能只填了域名)
                        self.api_url += '/v1/chat/completions'
                    logger.info(f"自动补全 OpenAI URL 为: {self.api_url}")
            
            elif self.provider == 'ollama':
                # Ollama 接口通常以 /api/generate 结尾
                if not self.api_url.endswith('/api/generate') and not self.api_url.endswith('/api/chat'):
                    self.api_url += '/api/generate'
                    logger.info(f"自动补全 Ollama URL 为: {self.api_url}")

    def call_api(self, prompt: str) -> Optional[str]:
        """
        调用 LLM API
        """
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"
                
            # 准备请求数据
            # 根据 provider 决定请求体格式，但 URL 直接使用配置的
            if self.provider == 'openai':
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a cybersecurity expert. Output JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1
                }
            else:
                # 默认为 Ollama 格式
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }

            # 发送请求
            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                return self._extract_content(response.json())
                
            except requests.exceptions.RequestException as e:
                logger.error(f"连接 AI 模型失败: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"LLM 客户端未知错误: {str(e)}")
            return None

    def _extract_content(self, result: Dict) -> str:
        """从 API 响应中提取内容"""
        if self.provider == 'ollama':
            return result.get('response', '')
        elif self.provider == 'openai':
            choices = result.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content', '')
        
        # 尝试通用解析
        if 'response' in result:
            return result['response']
        elif 'choices' in result:
             return result['choices'][0]['message']['content']
             
        return json.dumps(result)

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析模型返回的JSON文本
        """
        try:
            if not response_text:
                return {}
                
            # 移除可能的 <think> 标签内容 (DeepSeek R1 特性)
            clean_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                logger.warning(f"无法从模型响应中提取JSON: {response_text}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return {}

    @classmethod
    def ensure_local_ollama_started(cls, api_url, model_name):
        """
        已弃用: 不再自动管理本地 Ollama 服务
        """
        return True

    @classmethod
    def stop_local_ollama(cls):
        """
        已弃用: 不再自动管理本地 Ollama 服务
        """
        return True
