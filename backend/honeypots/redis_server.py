# -*- coding: utf-8 -*-
"""
Redis 蜜罐服务器
模拟 Redis 协议，捕获攻击者命令
"""

import socket
import threading
import sys
import os
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.time_utils import get_beijing_time

HOST = '0.0.0.0'
PORT = 6379
API_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

def log_attack(attacker_ip, attacker_port, payload, attack_type="Redis未授权访问", details=None):
    try:
        print(f"[{get_beijing_time()}] 攻击来自 {attacker_ip}:{attacker_port} - {attack_type} - {payload}")
        log_data = {
            "honeypot_port": PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": f"Captured {attack_type}: {payload}",
            "payload": payload,
            "protocol": "Redis",
            "attack_type": attack_type,
            "attack_description": details if details else f"Redis command execution attempt: {payload}"
        }
        requests.post(API_URL, json=log_data)
    except Exception as e:
        print(f"日志记录失败: {e}")

def handle_client(client_socket, addr):
    ip, client_port = addr
    print(f"[{get_beijing_time()}] Redis 新连接: {ip}:{client_port}")
    
    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
                
            # 解析简单的 Redis 请求
            payload = data.decode('utf-8', errors='ignore').strip()
            # 简化记录，把特殊字符替换掉方便查看
            clean_payload = repr(payload)
            
            log_attack(ip, client_port, clean_payload, details=f"执行 Redis 命令: {clean_payload}")
            
            # 返回标准的 Redis 错误信息或伪造信息
            response = b"-ERR unknown command\r\n"
            if "INFO" in payload.upper():
                response = b"$111\r\n# Server\r\nredis_version:5.0.14\r\nos:Linux 3.10.0-1127.el7.x86_64 x86_64\r\ntcp_port:6379\r\nrole:master\r\n"
            elif "PING" in payload.upper():
                response = b"+PONG\r\n"
            elif "SET" in payload.upper() or "CONFIG" in payload.upper():
                response = b"+OK\r\n"
                
            client_socket.send(response)
                
    except Exception as e:
        print(f"[!] Redis 连接处理异常: {e}")
    finally:
        client_socket.close()

def start_server(port):
    global PORT
    PORT = port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[{get_beijing_time()}] Redis Honeypot 监听于 {HOST}:{PORT}")
    
    while True:
        try:
            client, addr = server.accept()
            client_handler = threading.Thread(target=handle_client, args=(client, addr))
            client_handler.daemon = True
            client_handler.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"服务异常: {e}")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_server(int(sys.argv[1]))
    else:
        start_server(PORT)
