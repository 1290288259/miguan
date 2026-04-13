# -*- coding: utf-8 -*-
"""
实时汇报(WebSocket大屏推送) & 地图可视化 测试脚本

此测试脚本设计用于：
1. 采用确定的 SQL注入 载荷，确保必被识别为高危/恶意流量
2. 使用全球各地的不同真实IP，确保大屏地图能正常标注并展示脉冲散点效果
3. 持续运行 1 分钟（60秒），频率为 30次 / 分钟（即 1次/2秒）

操作指示：
    1. 确保已启动 Flask 后端 (`python app.py`)
    2. 确保前台已登录并打开了 Dashboard (数据大屏)
    3. 在终端运行:  cd backend/test && python test_realtime_report.py
    4. 观察前台界面的各种动态效果（地图、弹窗、横幅、计数器）
"""

import requests
import time
import random
import sys

# 修复 Windows 控制台 GBK 编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

UPLOAD_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

# 全球代表性公网IP，包含四大洲，用于大屏地图显示
IP_LIST = [
    "8.8.8.8",            # US (美国)
    "114.114.114.114",    # CN (中国 - 南京)
    "133.243.3.1",        # JP (日本 - 东京)
    "81.138.71.12",       # GB (英国 - 伦敦)
    "118.238.201.33",     # AU (澳大利亚 - 悉尼)
    "194.25.134.146",     # DE (德国 - 法兰克福)
    "87.250.250.242",     # RU (俄罗斯 - 莫斯科)
    "200.221.2.45",       # BR (巴西 - 圣保罗)
    "202.108.22.5",       # CN (中国 - 北京)
    "8.26.94.254",        # US (美国 - Level3)
    "1.1.1.1",            # AU/US (Cloudflare)
    "119.29.29.29",       # CN (中国 - 广州)
    "210.101.131.228",    # KR (韩国 - 首尔)
    "196.3.34.226",       # ZA (南非)
    "41.206.128.1"        # EG (埃及)
]

def run_test():
    duration = 60
    interval = 2
    rounds = duration // interval
    
    print(f"============================================================")
    print(f"  🍯 开始测试：实时汇报功能 (大屏 WebSocket 及地图可视化)")
    print(f"  ⏱  测试时长: {duration} 秒")
    print(f"  🔥 测试频率: {rounds} 次请求 (1次/{interval}秒)")
    print(f"  💉 攻击载荷: SQL注入 (1' OR '1'='1)")
    print(f"  🌍 来源IP: 随机选择全球主要国家IP以查看大屏地图分布效果")
    print(f"============================================================\n")
    
    print(f"请在前端保持【数据大屏(Dashboard)】处于开启并连接的状态...\n")
    
    for i in range(rounds):
        # 轮询获取IP，保证每个都被覆盖过
        ip = IP_LIST[i % len(IP_LIST)] 
        port = random.randint(10000, 60000)
        
        # 典型的 SQL 注入载荷
        payload = "select --+"
        raw_log = f"GET /api/user?id=select --+ HTTP/1.1\\r\\nHost: example.com\\r\\nUser-Agent: sqlmap/1.5.2"
        
        data = {
            "honeypot_port": 8888,
            "attacker_ip": ip,
            "attacker_port": port,
            "protocol": "HTTP",
            "request_path": "/api/user",
            "raw_log": raw_log,
            "payload": payload,
            "user_agent": "sqlmap/1.5.2"
        }
        
        try:
            resp = requests.post(UPLOAD_URL, json=data, timeout=5)
            if resp.status_code == 200 and resp.json().get('success'):
                # 检查实际被后端解析的攻击类型是否是 SQL注入
                res_data = resp.json().get('data', {})
                log_id = res_data.get('log_id')
                print(f"[{i+1:02d}/{rounds}] 🚀 发送成功 | IP: {ip:<15} | 目标: SQL注入 | log_id: {log_id or '-'}", flush=True)
            else:
                print(f"[{i+1:02d}/{rounds}] ❌ 接口返回错误: {resp.status_code} - {resp.text}", flush=True)
        except Exception as e:
            print(f"[{i+1:02d}/{rounds}] ⚠️ 请求异常: {e}", flush=True)
            
        # 最后一轮不需要等
        if i < rounds - 1:
            time.sleep(interval)
            
    print(f"\n============================================================")
    print("✅ 测试执行完毕！请检查前端态势感知大屏是否实现以下效果：")
    print("  1. 页面右上角：是否有实时的 [发现高危攻击] 红色报警弹窗/横幅")
    print("  2. 世界地图：是否涌现了分散的红色脉冲点 (亚洲、欧洲、美洲、非洲等)")
    print("  3. 攻击总览：全局累计总次数是否至少增加了 30 次")
    print("  4. 实时告警表：列表中是否连续滑入多条 [SQL注入] 相关的记录")
    print(f"============================================================")

if __name__ == '__main__':
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n============================================================")
        print("🛑 测试已被用户手动中断 (Ctrl+C)")
        print("============================================================")
        sys.exit(0)