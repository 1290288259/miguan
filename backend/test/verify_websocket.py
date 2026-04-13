# -*- coding: utf-8 -*-
"""
WebSocket推送链路验证脚本
验证后端推送的攻击事件是否能被客户端正确接收
"""

import socketio
import time
import requests
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sio = socketio.Client()
received = []


@sio.on("new_attack", namespace="/ws")
def on_attack(data):
    received.append(data)
    log_id = data.get("log_id")
    ip = data.get("source_ip")
    lng = data.get("longitude")
    lat = data.get("latitude")
    atype = data.get("attack_type")
    threat = data.get("threat_level")
    print(
        f"  [WS] log_id={log_id}, ip={ip}, type={atype}, threat={threat}, lng={lng}, lat={lat}"
    )


@sio.on("connect", namespace="/ws")
def on_connect():
    print("[WS] Connected to /ws namespace")


@sio.on("disconnect", namespace="/ws")
def on_disconnect():
    print("[WS] Disconnected")


@sio.on("connect_error", namespace="/ws")
def on_connect_error(data):
    print(f"[WS] Connection error: {data}")


print("=" * 60)
print("  WebSocket Push Verification Test")
print("=" * 60)

# 连接
print("\n[1] Connecting to WebSocket...")
try:
    sio.connect(
        "http://127.0.0.1:5000", namespaces=["/ws"], transports=["websocket", "polling"]
    )
except Exception as e:
    print(f"  FAIL: Cannot connect - {e}")
    sys.exit(1)

time.sleep(1)

# 发送3条测试攻击
test_ips = ["8.8.8.8", "114.114.114.114", "133.243.3.1"]
print(f"\n[2] Sending {len(test_ips)} test attacks via HTTP...")
for i, ip in enumerate(test_ips):
    data = {
        "honeypot_port": 8888,
        "attacker_ip": ip,
        "attacker_port": 50000 + i,
        "protocol": "HTTP",
        "request_path": "/test/ws-verify",
        "raw_log": "GET /api/user?id=select --+ HTTP/1.1\r\nHost: test\r\nUser-Agent: sqlmap/1.5.2",
        "payload": "select --+",
        "user_agent": "sqlmap/1.5.2",
    }
    r = requests.post(
        "http://127.0.0.1:5000/api/logs/internal/upload", json=data, timeout=5
    )
    status = "OK" if r.json().get("success") else "FAIL"
    print(f"  [{i + 1}] POST {ip} -> {status}")
    time.sleep(0.5)

# 等待WS事件到达
print("\n[3] Waiting 3 seconds for WebSocket events...")
time.sleep(3)

sio.disconnect()

# 验证结果
print("\n" + "=" * 60)
print(f"  RESULT: Received {len(received)} / {len(test_ips)} WebSocket events")
print("=" * 60)

pass_count = 0
total_checks = 4

# Check 1: 是否收到了事件
if len(received) >= len(test_ips):
    print(f"  [PASS] Event delivery: {len(received)}/{len(test_ips)}")
    pass_count += 1
else:
    print(f"  [FAIL] Event delivery: only {len(received)}/{len(test_ips)}")

# Check 2: 是否有经纬度
has_coords = sum(
    1
    for r in received
    if r.get("longitude") is not None and r.get("latitude") is not None
)
if has_coords == len(received) and len(received) > 0:
    print(f"  [PASS] Coordinates present: {has_coords}/{len(received)}")
    pass_count += 1
else:
    print(f"  [FAIL] Coordinates present: {has_coords}/{len(received)}")

# Check 3: attack_type 是否为 SQL注入
sql_injection = sum(1 for r in received if "SQL" in str(r.get("attack_type", "")))
if sql_injection == len(received) and len(received) > 0:
    print(f"  [PASS] Attack type (SQL): {sql_injection}/{len(received)}")
    pass_count += 1
else:
    print(f"  [FAIL] Attack type (SQL): {sql_injection}/{len(received)}")

# Check 4: threat_level 不为空
has_threat = sum(1 for r in received if r.get("threat_level"))
if has_threat == len(received) and len(received) > 0:
    print(f"  [PASS] Threat level present: {has_threat}/{len(received)}")
    pass_count += 1
else:
    print(f"  [FAIL] Threat level present: {has_threat}/{len(received)}")

print(f"\n  Overall: {pass_count}/{total_checks} checks passed")
if pass_count == total_checks:
    print("  === ALL CHECKS PASSED ===")
else:
    print("  === SOME CHECKS FAILED ===")
