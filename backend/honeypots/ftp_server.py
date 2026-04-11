# -*- coding: utf-8 -*-
"""
FTP 蜜罐服务器
模拟 FTP 协议握手，捕获攻击者用户名和密码
"""

import socket
import threading
import sys
import os
# Ensure src directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime
from utils.time_utils import get_beijing_time
import time

# 配置
HOST = '0.0.0.0'
PORT = 21
API_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

def log_attack(attacker_ip, attacker_port, payload, attack_type="FTP登录", details=None):
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
            "protocol": "FTP",
            "attack_type": attack_type,
            "attack_description": details if details else f"FTP login attempt with {payload}"
        }
        
        # 发送 HTTP 请求给后端
        requests.post(API_URL, json=log_data)
        
    except Exception as e:
        print(f"日志记录失败: {e}")

def handle_client(client_socket, addr):
    ip, port = addr
    print(f"[{get_beijing_time()}] 新连接: {ip}:{port}")
    
    try:
        # 发送欢迎消息
        client_socket.send(b"220 (vsFTPd 3.0.3)\r\n")
        
        username = ""
        password = ""
        
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
                
            command = data.decode('utf-8', errors='ignore').strip()
            
            if command.upper().startswith("USER"):
                username = command[5:].strip()
                client_socket.send(b"331 Please specify the password.\r\n")
                
            elif command.upper().startswith("PASS"):
                password = command[5:].strip()
                
                # 记录捕获的凭证
                payload = f"Username: {username}, Password: {password}"
                log_attack(ip, port, payload, details=f"尝试登录用户: {username}")
                
                # 始终返回登录失败
                client_socket.send(b"530 Login incorrect.\r\n")
                
            elif command.upper().startswith("QUIT"):
                client_socket.send(b"221 Goodbye.\r\n")
                break
            else:
                # 其他命令，要求先登录
                client_socket.send(b"530 Please login with USER and PASS.\r\n")
                
    except Exception as e:
        print(f"[!] 连接处理异常: {e}")
    finally:
        client_socket.close()
        print(f"[{get_beijing_time()}] 连接关闭: {ip}:{port}")

def start_server(port):
    """
    启动 TCP 监听
    """
    global PORT
    PORT = port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((HOST, PORT))
        sock.listen(100)
        print(f"[*] FTP 蜜罐正在监听 {HOST}:{PORT}")
        
        while True:
            client, addr = sock.accept()
            t = threading.Thread(target=handle_client, args=(client, addr))
            t.daemon = True
            t.start()
            
    except Exception as e:
        print(f"[!] 启动失败: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    # 从命令行参数获取端口
    port = 21
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("端口必须是整数")
            sys.exit(1)
            
    start_server(port)
