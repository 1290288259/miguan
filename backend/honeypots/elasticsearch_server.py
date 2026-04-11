# -*- coding: utf-8 -*-
"""
Elasticsearch 蜜罐服务器
模拟 Elasticsearch API (HTTP) 协议响应，捕获无授权利用企图
"""

import http.server
import socketserver
import json
import threading
import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.time_utils import get_beijing_time

HOST = '0.0.0.0'
PORT = 9200
API_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

def log_attack(attacker_ip, attacker_port, payload):
    """
    记录攻击日志并上报后端（纯数据采集，不做攻击分类）
    """
    try:
        print(f"[{get_beijing_time()}] 攻击来自 {attacker_ip}:{attacker_port} - {payload}")
        log_data = {
            "honeypot_port": PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": f"Elasticsearch交互: {payload}",
            "payload": payload,
            "protocol": "HTTP (Elasticsearch)",
        }
        requests.post(API_URL, json=log_data)
    except Exception as e:
        print(f"日志记录失败: {e}")

class ElasticHandler(http.server.BaseHTTPRequestHandler):
    
    server_version = "Elasticsearch/7.10.2"
    
    def log_message(self, format, *args):
        # 禁用默认的日志输出到标准错误流
        pass

    def get_client_ip(self):
        return self.client_address[0]
        
    def get_client_port(self):
        return self.client_address[1]

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def _route_and_respond(self, method, path):
        attacker_ip = self.get_client_ip()
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore') if content_length > 0 else ""
        
        # 不论请求什么路径，都直接在这里统一记录日志
        payload = f"{method} {path}"
        if body:
            payload += f" - Data: {body[:500]}"
            
        log_attack(attacker_ip, self.get_client_port(), payload)

        if method == "GET":
            info_json = {
                "name" : "es-node-1",
                "cluster_name" : "elasticsearch",
                "cluster_uuid" : "zD_8_hDqR0-1g7Hj52_wQn",
                "version" : {
                    "number" : "7.10.2",
                    "build_flavor" : "default",
                    "build_type" : "docker",
                    "build_hash" : "747e1cc71def077253878a59143c1f785afa92b9",
                    "build_date" : "2021-01-13T00:42:12.435326Z",
                    "build_snapshot" : False,
                    "lucene_version" : "8.7.0",
                    "minimum_wire_compatibility_version" : "6.8.0",
                    "minimum_index_compatibility_version" : "6.0.0-beta1"
                },
                "tagline" : "You Know, for Search"
            }
            
            if path == "/":
                self._set_headers()
                self.wfile.write(json.dumps(info_json).encode())
            elif "_search" in path:
                self._set_headers()
                self.wfile.write(b'{"took":1,"timed_out":false,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0},"hits":{"total":{"value":0,"relation":"eq"},"max_score":null,"hits":[]}}')
            elif "_cat" in path:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"green open .kibana_1       xyz 1 0 1 0 4.5kb 4.5kb\n")
            else:
                self._set_headers(404)
                self.wfile.write(b'{"error":"IndexNotFoundException[no such index]"}')

        elif method == "POST":
            self._set_headers(201)
            response = {
                "_index": "vuln_test",
                "_type": "_doc",
                "_id": "1",
                "_version": 1,
                "result": "created",
                "_shards": {
                    "total": 2,
                    "successful": 1,
                    "failed": 0
                },
                "_seq_no": 0,
                "_primary_term": 1
            }
            self.wfile.write(json.dumps(response).encode())

        elif method == "PUT":
            self._set_headers(403)
            self.wfile.write(b'{"error":"Forbidden","status":403}')
            
        else:
            # DELETE, HEAD, OPTIONS 等通通拦截并返回 405
            self._set_headers(405)
            self.wfile.write(b'{"error":"Method Not Allowed"}')

    def do_GET(self):
        self._route_and_respond("GET", self.path)

    def do_POST(self):
        self._route_and_respond("POST", self.path)

    def do_PUT(self):
        self._route_and_respond("PUT", self.path)
        
    def do_OPTIONS(self):
        self._route_and_respond("OPTIONS", self.path)
        
    def do_HEAD(self):
        self._route_and_respond("HEAD", self.path)
        
    def do_DELETE(self):
        self._route_and_respond("DELETE", self.path)

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def start_server(port):
    global PORT
    PORT = port
    server = ThreadingHTTPServer((HOST, PORT), ElasticHandler)
    print(f"[{get_beijing_time()}] Elasticsearch Honeypot 监听于 {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"服务异常: {e}")
    finally:
        server.server_close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_server(int(sys.argv[1]))
    else:
        start_server(PORT)
