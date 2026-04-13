# -*- coding: utf-8 -*-
"""
诊断测试：对比两种emit方式
1. 直接从app.py的test endpoint emit (保证同一个socketio对象)
2. 通过 /api/logs/internal/upload 触发 log_service.py 中的 emit
"""

import socketio
import time
import requests
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:5000"
received_direct = []
received_upload = []

sio = socketio.Client()


@sio.on("new_attack", namespace="/ws")
def on_attack(data):
    source = data.get("source_ip", "")
    if source == "TEST_DIRECT_EMIT":
        received_direct.append(data)
        print(f"  >>> DIRECT emit received: {data.get('attack_description')}")
    else:
        received_upload.append(data)
        print(f"  >>> UPLOAD emit received: log_id={data.get('log_id')}, ip={source}")


@sio.on("connect", namespace="/ws")
def on_connect():
    print("[OK] Connected to /ws")


print("=" * 60)
print("  Diagnostic: Direct vs Upload emit comparison")
print("=" * 60)

# Step 1: Connect
print("\n[1] Connecting to /ws namespace...")
sio.connect(
    BASE, namespaces=["/ws"], transports=["polling", "websocket"], wait_timeout=10
)
time.sleep(2)

# Step 2: Direct emit test
print("\n[2] Testing DIRECT emit from app.py test endpoint...")
r = requests.get(f"{BASE}/api/test/ws-emit", timeout=5)
resp = r.json()
print(f"  HTTP: {r.status_code}, socketio_id in app.py = {resp.get('socketio_id')}")
time.sleep(2)

# Step 3: Upload emit test
print("\n[3] Testing UPLOAD -> log_service.py emit...")
data = {
    "honeypot_port": 8888,
    "attacker_ip": "1.2.3.4",
    "attacker_port": 55555,
    "protocol": "HTTP",
    "request_path": "/diag-test",
    "raw_log": "GET /?id=1 UNION SELECT password FROM users-- HTTP/1.1\r\nHost: t\r\nUser-Agent: sqlmap/1.5",
    "payload": "1 UNION SELECT password FROM users--",
    "user_agent": "sqlmap/1.5",
}
r2 = requests.post(f"{BASE}/api/logs/internal/upload", json=data, timeout=10)
print(f"  HTTP: {r2.status_code}, response: {r2.json()}")
time.sleep(3)

# Results
sio.disconnect()
time.sleep(1)

print("\n" + "=" * 60)
print(f"  Direct emit received:  {len(received_direct)} events")
print(f"  Upload emit received:  {len(received_upload)} events")
print("=" * 60)

if len(received_direct) > 0 and len(received_upload) == 0:
    print("\n  DIAGNOSIS: socketio object in log_service.py differs from app.py!")
    print("  ROOT CAUSE: 'from app import socketio' gets wrong instance.")
elif len(received_direct) == 0 and len(received_upload) == 0:
    print("\n  DIAGNOSIS: Both emit paths fail - transport or namespace issue.")
elif len(received_direct) > 0 and len(received_upload) > 0:
    print("\n  DIAGNOSIS: Both work! Issue was elsewhere.")
else:
    print("\n  DIAGNOSIS: Unexpected pattern - investigate further.")
