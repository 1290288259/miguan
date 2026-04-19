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

def log_attack(attacker_ip, attacker_port, payload):
    """
    记录原始捕获数据到后端 API（不做攻击分类，由后端 log_service 统一处理）
    """
    try:
        print(f"[{get_beijing_time()}] 捕获数据 {attacker_ip}:{attacker_port} - {payload}")
        
        # 构造日志数据（仅包含原始捕获信息，不含分类字段）
        log_data = {
            "honeypot_port": PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": f"FTP交互: {payload}",
            "payload": payload,
            "protocol": "FTP"
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
            if not command:
                continue

            cmd_upper = command.upper()
            
            if cmd_upper.startswith("USER"):
                username = command[5:].strip()
                client_socket.send(b"331 Please specify the password.\r\n")
                log_attack(ip, port, f"Command: {command}")
                
            elif cmd_upper.startswith("PASS"):
                password = command[5:].strip()
                payload = f"Username: {username}, Password: {password}"
                log_attack(ip, port, payload)
                # False success
                client_socket.send(b"230 Login successful.\r\n")
                
            elif cmd_upper.startswith("SYST"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"215 UNIX Type: L8\r\n")
                
            elif cmd_upper.startswith("FEAT"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"211-Features:\r\n EPRT\r\n EPSV\r\n MDTM\r\n PASV\r\n REST STREAM\r\n SIZE\r\n TVFS\r\n211 End\r\n")
                
            elif cmd_upper.startswith("PWD"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b'257 "/root" is the current directory\r\n')
                
            elif cmd_upper.startswith("TYPE"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"200 Switching to Binary mode.\r\n")
                
            elif cmd_upper.startswith("PASV") or cmd_upper.startswith("PORT"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"502 Illegal PORT command.\r\n") # Keep it simple, deny active/passive data channels
                
            elif cmd_upper.startswith("LIST") or cmd_upper.startswith("NLST"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"150 Here comes the directory listing.\r\n226 Directory send OK.\r\n")
                
            elif cmd_upper.startswith("QUIT"):
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"221 Goodbye.\r\n")
                break
                
            else:
                log_attack(ip, port, f"Command: {command}")
                client_socket.send(b"500 Unknown command.\r\n")
                
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
