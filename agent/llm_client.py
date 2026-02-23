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
        self.api_url = config.get('api_url', "http://localhost:11434/api/generate")
        self.model_name = config.get('model_name', "deepseek-r1:7b")
        self.provider = config.get('provider', 'ollama')
        self.api_key = config.get('api_key', '')

    def call_api(self, prompt: str) -> Optional[str]:
        """
        调用 LLM API
        """
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"
                
            # 准备请求数据
            if self.provider == 'ollama':
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            elif self.provider == 'openai':
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a cybersecurity expert. Output JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1
                }
            else:
                # 默认尝试Ollama格式
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }

            # 发送请求函数
            def send_request(url):
                return requests.post(url, json=payload, headers=headers, timeout=60)

            # 第一次尝试
            try:
                response = send_request(self.api_url)
                response.raise_for_status()
                return self._extract_content(response.json())
                
            except requests.exceptions.RequestException as e:
                # 记录初次失败
                logger.warning(f"第一次连接尝试失败: {str(e)}")
                
                # 如果是本地Ollama且连接失败，尝试启动服务
                if self.provider == 'ollama' and ('localhost' in self.api_url or '127.0.0.1' in self.api_url):
                    logger.info("检测到本地Ollama连接失败，尝试自动启动服务...")
                    if self.ensure_local_ollama_started(self.api_url, self.model_name):
                         # 服务启动后重试
                        try:
                            response = send_request(self.api_url)
                            response.raise_for_status()
                            return self._extract_content(response.json())
                        except Exception as retry_e:
                            logger.error(f"重试失败: {str(retry_e)}")

            # 智能重试逻辑：处理 404 或连接失败 (尝试不同的 endpoint)
            new_url = None
            if self.provider == 'openai' and 'chat/completions' not in self.api_url:
                base = self.api_url.rstrip('/')
                new_url = f"{base}/chat/completions"
            elif self.provider == 'ollama' and 'api/generate' not in self.api_url:
                base = self.api_url.rstrip('/')
                new_url = f"{base}/api/generate"
            
            if new_url:
                try:
                    response = send_request(new_url)
                    response.raise_for_status()
                    return self._extract_content(response.json())
                except:
                    pass
            
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
        检查并尝试启动本地Ollama服务
        """
        # 仅针对本地地址
        if not ('localhost' in api_url or '127.0.0.1' in api_url):
            return True

        port = 11434 # 默认端口
        try:
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

        # 检查进程是否存在
        def is_process_running(process_name):
            try:
                if os.name == 'nt':
                    # Windows
                    output = subprocess.check_output(f"tasklist | findstr {process_name}", shell=True)
                    return process_name in str(output)
                else:
                    # Linux/Mac
                    output = subprocess.check_output(f"pgrep -f {process_name}", shell=True)
                    return True
            except:
                return False

        if is_port_open("localhost", port):
            # 端口已开，直接进行预加载
            pass
        else:
            # 端口未开，加锁尝试启动
            with cls._start_lock:
                # 二次检查
                if not is_port_open("localhost", port):
                    logger.info(f"Ollama服务(端口{port})未运行")
                    print(f"Ollama服务(端口{port})未运行")
                    
                    # 检查是否已在运行但未就绪
                    if is_process_running("ollama.exe") or is_process_running("ollama_app.exe"):
                         logger.info("检测到Ollama进程已存在，可能正在启动中...")
                         print("检测到Ollama进程已存在，可能正在启动中...")
                    else:
                        # 尝试启动
                        if not shutil.which("ollama"):
                            logger.error("未找到ollama命令，请确保已安装Ollama并添加到环境变量")
                            print("未找到ollama命令，请确保已安装Ollama并添加到环境变量")
                            return False

                        logger.info("正在尝试启动Ollama服务...")
                        print("正在尝试启动Ollama服务...")
                        try:
                            # Windows下尝试启动ollama serve
                            # 使用 CREATE_NEW_CONSOLE
                            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        except Exception as e:
                            logger.error(f"启动Ollama服务失败: {str(e)}")
                            print(f"启动Ollama服务失败: {str(e)}")
                            return False
                    
                    # 等待服务启动 (增加等待时间到30秒)
                    logger.info("正在等待Ollama服务就绪...")
                    print("正在等待Ollama服务就绪...")
                    started = False
                    for _ in range(30):  
                        if is_port_open("localhost", port):
                            logger.info("Ollama服务已启动")
                            print("Ollama服务已启动")
                            started = True
                            break
                        time.sleep(1)
                    
                    if not started:
                        logger.error("等待Ollama服务启动超时")
                        print("等待Ollama服务启动超时")
                        return False

        # 2. 预加载模型
        logger.info(f"正在预加载模型 {model_name}...")
        try:
            # 发送一个简单的请求来触发模型加载
            payload = {
                "model": model_name,
                "prompt": "hi", 
                "stream": False,
                "keep_alive": "1h"
            }
            # 增加超时时间，因为初次加载模型可能很慢
            requests.post(api_url, json=payload, timeout=120)
            logger.info(f"模型 {model_name} 预加载完成")
            return True
        except Exception as e:
            logger.error(f"模型预加载请求发送失败: {str(e)}")
            # 虽然预加载失败，但服务可能已经启动，返回True尝试继续使用
            return True

    @classmethod
    def stop_local_ollama(cls):
        """
        停止本地Ollama服务
        """
        import subprocess
        import os
        
        try:
            # 仅针对Windows环境
            if os.name == 'nt':
                # 尝试强制终止 ollama.exe 和 ollama app.exe
                # 使用 taskkill /F /IM <process_name>
                subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
                subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe"], capture_output=True)
                logger.info("已尝试停止本地Ollama服务")
                print("已尝试停止本地Ollama服务")
            else:
                # Linux/Mac环境 (假设)
                subprocess.run(["pkill", "ollama"], capture_output=True)
                logger.info("已尝试停止本地Ollama服务")
                
            return True
        except Exception as e:
            logger.error(f"停止Ollama服务失败: {str(e)}")
            print(f"停止Ollama服务失败: {str(e)}")
            return False
