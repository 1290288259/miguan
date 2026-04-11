from flask import Flask, request, render_template_string, jsonify
import requests
import datetime
import logging
import sys
import os
import time

# Ensure src directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.time_utils import get_beijing_time

# Configure logging to use Beijing time
logging.Formatter.converter = lambda *args: get_beijing_time().timetuple()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置参数
HONEYPOT_PORT = 9090
API_URL = "http://127.0.0.1:5000/api/logs/internal/upload"

# 海康威视登录页面模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Hikvision IP Camera - Login</title>
    <style>
        body {
            background-color: #333;
            color: #fff;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background-color: #444;
            padding: 30px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            width: 300px;
            text-align: center;
        }
        .logo {
            color: #d71418;
            font-weight: bold;
            font-size: 24px;
            margin-bottom: 20px;
            display: block;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #666;
            background-color: #555;
            color: #fff;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #d71418;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #b01014;
        }
        .footer {
            margin-top: 20px;
            font-size: 12px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <span class="logo">HIKVISION</span>
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="User Name" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="footer">
            &copy; Hikvision Digital Technology Co., Ltd. All Rights Reserved.
        </div>
    </div>
</body>
</html>
"""

def log_attack(attacker_ip, attacker_port, payload, attack_type="Web Login", request_path="/"):
    try:
        log_data = {
            "honeypot_port": HONEYPOT_PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": f"Login attempt: {payload}",
            "payload": payload,
            "protocol": "HTTP",
            "attack_type": attack_type,
            "request_path": request_path,
            "user_agent": request.headers.get('User-Agent'),
            "attack_description": "捕获到Web登录凭证"
        }
        # 发送日志到内部API
        requests.post(API_URL, json=log_data, timeout=2)
        logger.info(f"Log sent: {log_data}")
    except Exception as e:
        logger.error(f"Failed to send log: {e}")

@app.route('/', methods=['GET'])
def index():
    # 记录访问日志
    attacker_ip = request.remote_addr
    attacker_port = request.environ.get('REMOTE_PORT', 0)
    log_attack(attacker_ip, attacker_port, "Page Visit", "正常流量", "/")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    attacker_ip = request.remote_addr
    attacker_port = request.environ.get('REMOTE_PORT', 0)
    
    # 构造 Payload
    payload = f"Username: {username}, Password: {password}"
    
    # 记录攻击日志
    log_attack(attacker_ip, attacker_port, payload, "暴力破解", "/login")
    
    # 始终返回登录失败
    return render_template_string("""
        <script>
            alert('Login failed: Invalid username or password.');
            window.location.href = '/';
        </script>
    """)

if __name__ == '__main__':
    # 从命令行参数读取端口，与 ssh_server.py 和 ftp_server.py 保持一致
    # honeypot_service.py 启动时会传入端口参数：cmd = [sys.executable, script_path, str(hp.port)]
    if len(sys.argv) > 1:
        try:
            HONEYPOT_PORT = int(sys.argv[1])
        except ValueError:
            logger.error(f"端口参数无效: {sys.argv[1]}，使用默认端口 {HONEYPOT_PORT}")
    logger.info(f"Hikvision HTTP Honeypot listening on port {HONEYPOT_PORT}")
    app.run(host='0.0.0.0', port=HONEYPOT_PORT, debug=False)
