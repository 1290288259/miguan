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

def handle_client(client_socket, addr):
    ip, port = addr
    print(f"[{get_beijing_time()}] MySQL 新连接: {ip}:{port}")
    try:
        # 发送握手包 (带版本号 5.7.31-0ubuntu0.18.04.1)
        version = b"5.7.31-0ubuntu0.18.04.1\x00"
        payload = b'\x0a' + version + b'\x0b\x00\x00\x00\x45\x36\x2a\x24\x46\x24\x6d\x69\x00\xff\xff\x08\x02\x00\x0f\x80\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x15\x21\x37\x3a\x1b\x17\x2b\x62\x1d\x07\x02\x32\x00\x6d\x79\x73\x71\x6c\x5f\x6e\x61\x74\x69\x76\x65\x5f\x70\x61\x73\x73\x77\x6f\x72\x64\x00'
        header = struct.pack('<I', len(payload))[:3] + b'\x00'
        client_socket.send(header + payload)

        # 接收认证包
        auth_data = client_socket.recv(1024)
        if not auth_data:
            return
            
        # 简单提取 username (通常在第36个字节之后)
        try:
            idx = 36
            while idx < len(auth_data) and auth_data[idx] != 0:
                idx += 1
            username = auth_data[36:idx].decode('utf-8', errors='ignore')
            log_attack(ip, port, f"Username: {username}, Password: [Hash]")
        except:
            log_attack(ip, port, f"Auth Packet Received: {auth_data.hex()[:50]}")

        # False Success: 返回 OK Packet
        ok_packet = b'\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00'
        client_socket.send(ok_packet)
        
        # Empty Shell: 循环接收 SQL 语句
        while True:
            cmd_data = client_socket.recv(4096)
            if not cmd_data:
                break
            
            # 第一字节是包长度，第四字节是序列号，第五字节是命令类型
            if len(cmd_data) > 4:
                cmd_type = cmd_data[4]
                if cmd_type == 0x03: # COM_QUERY
                    sql_query = cmd_data[5:].decode('utf-8', errors='ignore')
                    log_attack(ip, port, f"Command: {sql_query}")
                    
                    # 返回空的 Result Set 或 OK Packet 骗过扫描器
                    # 这里直接返回 OK packet 模拟执行成功但无数据返回
                    ok_resp = b'\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00'
                    client_socket.send(ok_resp)
                elif cmd_type == 0x01: # COM_QUIT
                    break
                else:
                    # 记录未知的包类型
                    log_attack(ip, port, f"Packet Type: {hex(cmd_type)}, Data: {cmd_data[5:].hex()[:50]}")
                    ok_resp = b'\x07\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00'
                    client_socket.send(ok_resp)

    except Exception as e:
        print(f"[!] MySQL 异常: {e}")
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
