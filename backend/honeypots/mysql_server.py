# -*- coding: utf-8 -*-
"""
MySQL 蜜罐服务器
模拟 MySQL 握手协议，捕获攻击者用户名和哈希密码
"""

import socket
import threading
import sys
import os
import requests
import struct

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.time_utils import get_beijing_time

HOST = '0.0.0.0'
PORT = 3307
API_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

def log_attack(attacker_ip, attacker_port, payload):
    """
    上报原始捕获数据到后端，不做任何攻击分类
    """
    try:
        print(f"[{get_beijing_time()}] 捕获来自 {attacker_ip}:{attacker_port} - {payload}")
        log_data = {
            "honeypot_port": PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": f"MySQL交互: {payload}",
            "payload": payload,
            "protocol": "MySQL"
        }
        requests.post(API_URL, json=log_data)
    except Exception as e:
        print(f"日志记录失败: {e}")

def create_mysql_handshake_packet():
    # 模拟 MySQL 5.7+ 服务端握手包
    protocol_version = b'\x0a'
    server_version = b'5.7.35\x00'
    connection_id = struct.pack('<I', 1337)
    salt1 = b'12345678\x00'
    server_capabilities = b'\xff\xff'
    server_language = b'\x08'
    server_status = b'\x02\x00'
    ext_capabilities = b'\xcf\xc1'
    auth_plugin_length = b'\x15'
    reserved = b'\x00' * 10
    salt2 = b'abcdefghi\x00\x00\x00'
    auth_plugin_name = b'mysql_native_password\x00'
    
    payload = protocol_version + server_version + connection_id + salt1 + \
              server_capabilities + server_language + server_status + \
              ext_capabilities + auth_plugin_length + reserved + salt2 + auth_plugin_name
              
    packet_length = struct.pack('<I', len(payload))[0:3]
    sequence_id = b'\x00'
    
    return packet_length + sequence_id + payload

def handle_client(client_socket, addr):
    ip, client_port = addr
    print(f"[{get_beijing_time()}] MySQL 新连接: {ip}:{client_port}")
    
    try:
        client_socket.sendall(create_mysql_handshake_packet())
        
        # 接收客户端登录请求 (Client Authentication Packet)
        data = client_socket.recv(1024)
        if not data:
            client_socket.close()
            return
            
        # 解析数据包（跳过包头长度序列号，简单的特征匹配）
        payload_data = data[4:]
        
        # 提取用户名（在包的不同偏移位置可能存在 null 结尾字符串）
        clean_payload = ""
        try:
            # 简化版：通过寻找非空字符块粗略提取 username
            parts = payload_data.split(b'\x00')
            username = ""
            for p in parts:
                if len(p) > 2 and p.isalnum():
                    username = p.decode('utf-8', errors='ignore')
                    break
            
            if username:
                clean_payload = f"Username: {username}"
            else:
                clean_payload = f"Raw Data: {data[:100]}"
        except Exception:
            clean_payload = f"Raw Data (Err): {data[:100]}"
            
        log_attack(ip, client_port, clean_payload)
        
        # 返回 Access Denied 或直接断开连接
        error_packet = b"\x17\x00\x00\x02\xff\x15\x04#28000Access denied for user"
        client_socket.sendall(error_packet)
        
    except Exception as e:
        print(f"[!] MySQL 连接处理异常: {e}")
    finally:
        client_socket.close()

def start_server(port):
    global PORT
    PORT = port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[{get_beijing_time()}] MySQL Honeypot 监听于 {HOST}:{PORT}")
    
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
