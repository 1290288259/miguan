# -*- coding: utf-8 -*-
"""
最简WebSocket测试：
1. 客户端连接 /ws
2. HTTP 调用一个会触发 socketio.emit 的测试端点
3. 验证客户端是否收到事件
"""

import socketio
import time
import requests
import sys
import io
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:5000"
received = []

sio = socketio.Client(logger=True, engineio_logger=True)


@sio.on("new_attack", namespace="/ws")
def on_attack(data):
    print(f"  >>> RECEIVED EVENT: {data}")
    received.append(data)


@sio.on("connect", namespace="/ws")
def on_connect():
    print("[OK] Connected to /ws")


@sio.on("disconnect", namespace="/ws")
def on_disconnect():
    print("[OK] Disconnected from /ws")


@sio.on("connect_error", namespace="/ws")
def on_error(data):
    print(f"[ERR] Connection error: {data}")


# 也监听默认命名空间的所有事件
@sio.on("*")
def catch_all(event, data):
    print(f"  >>> DEFAULT NS event={event}, data={data}")


@sio.on("*", namespace="/ws")
def catch_all_ws(event, data):
    print(f"  >>> /ws NS event={event}, data={data}")


print("=" * 60)
print("  Simple WebSocket Test (with full logging)")
print("=" * 60)

print("\n[Step 1] Connecting...")
try:
    sio.connect(
        BASE, namespaces=["/ws"], transports=["polling", "websocket"], wait_timeout=10
    )
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

time.sleep(2)
print(f"\n[Step 2] Connected. SID={sio.sid}")
print(f"  Transport: {sio.transport()}")

print("\n[Step 3] Sending 1 test attack...")
data = {
    "honeypot_port": 8888,
    "attacker_ip": "1.2.3.4",
    "attacker_port": 55555,
    "protocol": "HTTP",
    "request_path": "/ws-test",
    "raw_log": "GET /api/?id=1 UNION SELECT password FROM users-- HTTP/1.1\r\nHost: target\r\nUser-Agent: sqlmap/1.5",
    "payload": "1 UNION SELECT password FROM users--",
    "user_agent": "sqlmap/1.5",
}
r = requests.post(f"{BASE}/api/logs/internal/upload", json=data, timeout=10)
print(f"  HTTP response: {r.status_code} -> {r.json()}")

print("\n[Step 4] Waiting 5 seconds for event...")
time.sleep(5)

print(f"\n[Step 5] Received {len(received)} events")
for ev in received:
    print(f"  -> {ev}")

sio.disconnect()
time.sleep(1)

if len(received) > 0:
    print("\n=== PASS: WebSocket push works! ===")
else:
    print("\n=== FAIL: No events received ===")
