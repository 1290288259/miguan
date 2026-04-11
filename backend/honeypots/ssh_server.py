# -*- coding: utf-8 -*-
"""
SSH 蜜罐服务器 (基于 Paramiko)
模拟 SSH 协议握手，捕获攻击者用户名和密码
"""

import socket
import threading
import sys
import os
# Ensure src directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import paramiko
from datetime import datetime
from utils.time_utils import get_beijing_time
import time

# 配置
HOST = '0.0.0.0'
PORT = 2222
API_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

# 生成或加载 Host Key
HOST_KEY = paramiko.RSAKey.generate(2048)

def log_attack(attacker_ip, attacker_port, payload, attack_type="SSH登录", details=None):
    """
    记录攻击日志到后端 API
    """
    try:
        print(f"[{get_beijing_time()}] 攻击来自 {attacker_ip}:{attacker_port} - {attack_type} - {payload}")
        
        # 构造日志数据
        log_data = {
            "honeypot_port": PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": f"Captured {attack_type}: {payload}",
            "payload": payload,
            "protocol": "SSH",
            "attack_type": attack_type,
            "attack_description": details if details else f"SSH login attempt with {payload}"
        }
        
        # 发送 HTTP 请求给后端
        requests.post(API_URL, json=log_data)
        
    except Exception as e:
        print(f"日志记录失败: {e}")

class HoneypotServer(paramiko.ServerInterface):
    """
    SSH 蜜罐服务接口
    """
    def __init__(self, client_ip, client_port):
        self.client_ip = client_ip
        self.client_port = client_port
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        """
        捕获密码认证尝试
        """
        payload = f"Username: {username}, Password: {password}"
        log_attack(
            self.client_ip, 
            self.client_port, 
            payload, 
            attack_type="SSH登录",
            details=f"尝试登录用户: {username}"
        )
        # 始终返回验证失败，诱导攻击者尝试更多密码
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """
        捕获公钥认证尝试
        """
        hex_key = key.get_base64()
        payload = f"Username: {username}, Key: {hex_key[:30]}..."
        log_attack(
            self.client_ip,
            self.client_port,
            payload,
            attack_type="SSH公钥扫描",
            details=f"尝试公钥认证: {username}"
        )
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        """
        返回允许的认证方式
        """
        return 'password,publickey'

def handle_connection(client_socket, addr):
    """
    处理单个 SSH 连接
    """
    ip, port = addr
    print(f"[{get_beijing_time()}] 新连接: {ip}:{port}")
    
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        
        server = HoneypotServer(ip, port)
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            print(f"[*] SSH 协商失败")
            return

        # 等待连接结束（通常会在认证失败多次后断开）
        channel = transport.accept(20)
        if channel is None:
            # 没有建立通道（预期的，因为我们拒绝了所有认证）
            pass
        else:
            channel.close()
            
    except Exception as e:
        print(f"[!] 处理连接异常: {e}")
    finally:
        try:
            transport.close()
        except:
            pass
        client_socket.close()
        print(f"[{get_beijing_time()}] 连接关闭: {ip}:{port}")

def start_server(port):
    """
    启动 TCP 监听
    """
    global PORT
    PORT = port
    
    # 设置 paramiko 日志
    # paramiko.util.log_to_file('paramiko.log')
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((HOST, PORT))
        sock.listen(100)
        print(f"[*] SSH 蜜罐 (Paramiko版) 正在监听 {HOST}:{PORT}")
        
        while True:
            client, addr = sock.accept()
            t = threading.Thread(target=handle_connection, args=(client, addr))
            t.daemon = True
            t.start()
            
    except Exception as e:
        print(f"[!] 启动失败: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    # 从命令行参数获取端口
    port = 2222
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("端口必须是整数")
            sys.exit(1)
            
    start_server(port)
