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

import werkzeug.serving
werkzeug.serving.WSGIRequestHandler.version_string = lambda self: 'App-webs/'

app = Flask(__name__)

# 配置参数
HONEYPOT_PORT = 8888
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

def log_attack(attacker_ip, attacker_port, payload, request_path="/"):
    """
    记录原始请求数据并上报后端，不做任何攻击分类判断。
    攻击类型识别由后端规则引擎统一处理。
    """
    try:
        # 获取完整的 URL 或查询参数
        full_url = request.url
        query_string = request.query_string.decode('utf-8')
        path_with_query = f"{request_path}?{query_string}" if query_string else request_path
        
        # 提取 Body
        try:
            body = request.get_data(as_text=True)
            body_content = f"\\nData: {body}" if body else ""
        except:
            body_content = ""
            
        real_raw_log = f"{request.remote_addr} - - [{get_beijing_time().strftime('%d/%b/%Y:%H:%M:%S +0800')}] \"{request.method} {path_with_query} HTTP/1.1\" - {request.headers.get('User-Agent', '')}{body_content}"
        
        log_data = {
            "honeypot_port": HONEYPOT_PORT,
            "attacker_ip": attacker_ip,
            "attacker_port": attacker_port,
            "raw_log": real_raw_log,
            "payload": payload,
            "protocol": "HTTP",
            "request_path": path_with_query,
            "user_agent": request.headers.get('User-Agent'),
        }
        # 发送日志到内部API
        requests.post(API_URL, json=log_data, timeout=2)
        logger.info(f"Log sent: {log_data}")
    except Exception as e:
        logger.error(f"Failed to send log: {e}")

@app.before_request
def log_all_traffic():
    """
    无论什么流量（正常请求、404、405等），都在此统一拦截并记录
    """
    attacker_ip = request.remote_addr
    attacker_port = request.environ.get('REMOTE_PORT', 0)
    
    # 构造 path_with_query 保证 payload 也能看到完整的 url
    query_string = request.query_string.decode('utf-8')
    path_with_query = f"{request.path}?{query_string}" if query_string else request.path

    # 针对登录接口特殊提取 payload
    if request.path == '/login' and request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        payload = f"Username: {username}, Password: {password}"
    else:
        # 其他接口如果是 POST/PUT，提取 body 中的部分内容作为 payload
        try:
            body = request.get_data(as_text=True)
            payload = f"{request.method} {path_with_query} - Data: {body[:500]}" if body else f"{request.method} {path_with_query}"
        except:
            payload = f"{request.method} {path_with_query}"
            
    log_attack(attacker_ip, attacker_port, payload, request.path)

@app.route('/', methods=['GET'])
def index():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    # 模拟登录成功，跳转到控制台
    return render_template_string("""
        <script>
            window.location.href = '/dashboard';
        </script>
    """)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Hikvision Dashboard</title></head>
        <body style="background-color: #f0f0f0; font-family: Arial;">
            <h2>System Dashboard</h2>
            <p>Loading video streams... Error: Connection to camera lost.</p>
        </body>
        </html>
    """)

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Page not found", "status": 404}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "status": 405}), 405

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Internal server error", "status": 500}), 500

@app.after_request
def add_server_header(response):
    response.headers['Server'] = 'nginx/1.18.0 (Ubuntu)'
    return response

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
