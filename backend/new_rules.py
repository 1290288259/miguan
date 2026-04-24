# -*- coding: utf-8 -*-
"""
新版正则匹配规则定义（独立文件，供 init_data.py 引用）
设计原则：
  1. 关键字匹配 —— 识别到特征关键字即判定为对应漏洞
  2. 规则间关键字互斥，避免一条日志匹配多条规则
  3. 命令注入等不使用 ; | & 等过于宽泛的符号
"""

RULES = [
    # ===== 1. SQL注入 =====
    {
        "name": "SQL注入检测",
        "attack_type": "SQL注入",
        "regex_pattern": (
            r"(?i)("
            r"\bselect\b"
            r"|\bunion\b"
            r"|\binsert\s+into\b"
            r"|\bupdate\b.*\bset\b"
            r"|\bdelete\s+from\b"
            r"|\bdrop\s+table\b"
            r"|\balter\s+table\b"
            r"|\btruncate\b"
            r"|\binformation_schema\b"
            r"|\bsleep\s*\("
            r"|\bbenchmark\s*\("
            r"|\bwaitfor\s+delay\b"
            r"|\bxp_cmdshell\b"
            r"|\bload_file\s*\("
            r"|\boutfile\b"
            r"|\bdumpfile\b"
            r"|\bgroup_concat\s*\("
            r"|\bhaving\b"
            r"|\border\s+by\b"
            r"|\b1\s*=\s*1\b"
            r"|\bor\s+['\d]+=\s*['\d]+"
            r")"
        ),
        "threat_level": "high",
        "description": "SQL注入检测: 匹配SQL关键字如select、union、drop table、sleep()等",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 1,
        "auto_block": True,
        "block_duration": 24,
    },
    # ===== 2. XSS =====
    {
        "name": "XSS攻击检测",
        "attack_type": "XSS",
        "regex_pattern": (
            r"(?i)("
            r"<\s*script[\s>]"
            r"|<\s*/\s*script\s*>"
            r"|\bjavascript\s*:"
            r"|\bon(error|load|mouseover|click|focus|blur|submit|change)\s*="
            r"|\balert\s*\("
            r"|\bprompt\s*\("
            r"|\bconfirm\s*\("
            r"|\bdocument\s*\.\s*cookie\b"
            r"|\bdocument\s*\.\s*write\b"
            r"|<\s*iframe[\s>]"
            r"|<\s*svg[\s>]"
            r"|<\s*embed[\s>]"
            r"|<\s*object[\s>]"
            r"|\bString\s*\.\s*fromCharCode\b"
            r"|%3[Cc]\s*script"
            r")"
        ),
        "threat_level": "medium",
        "description": "XSS检测: 匹配script标签、事件属性(onXxx=)、javascript:伪协议、DOM操作等",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 2,
        "auto_block": False,
        "block_duration": 0,
    },
    # ===== 3. 目录遍历 =====
    {
        "name": "目录遍历检测",
        "attack_type": "目录遍历",
        "regex_pattern": (
            r"(?i)("
            r"(?:\.\.[/\\]){2,}"
            r"|/etc/passwd"
            r"|/etc/shadow"
            r"|/etc/hosts"
            r"|\bboot\.ini\b"
            r"|\bwin\.ini\b"
            r"|/proc/self"
            r"|%2e%2e[%2f/]"
            r")"
        ),
        "threat_level": "medium",
        "description": "目录遍历检测: 匹配../路径穿越、/etc/passwd等系统敏感文件路径",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 3,
        "auto_block": False,
        "block_duration": 0,
    },
    # ===== 4. 命令注入 =====
    {
        "name": "命令注入攻击",
        "attack_type": "命令注入",
        "regex_pattern": (
            r"(?i)("
            r"\bwhoami\b"
            r"|\buname\b"
            r"|\bifconfig\b"
            r"|\bipconfig\b"
            r"|\bnetstat\b"
            r"|\btraceroute\b"
            r"|\bnslookup\b"
            r"|\bcat\s+/etc/"
            r"|\brm\s+-rf\b"
            r"|\bchmod\s+[0-7]{3}\b"
            r"|\bbash\s+-[ci]\b"
            r"|\bnc\s+-[elp]\b"
            r"|\bping\s+-[nc]\b"
            r"|\bpython\s+-c\b"
            r"|\bperl\s+-e\b"
            r"|\bruby\s+-e\b"
            r"|\bcmd\s+/c\b"
            r"|\bpowershell\s+-"
            r")"
        ),
        "threat_level": "high",
        "description": "命令注入检测: 匹配whoami、uname、ifconfig等系统命令关键字，不使用;|&等宽泛符号",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 4,
        "auto_block": True,
        "block_duration": 24,
    },
    # ===== 5. WebShell =====
    {
        "name": "WebShell 上传/访问",
        "attack_type": "WebShell",
        "regex_pattern": (
            r"(?i)("
            r"\beval\s*\("
            r"|\bassert\s*\("
            r"|\bpassthru\s*\("
            r"|\bshell_exec\s*\("
            r"|\bpopen\s*\("
            r"|\bproc_open\s*\("
            r"|\bbase64_decode\s*\("
            r"|<\?php\b"
            r"|\b(?:antsword|behinder|godzilla|ice_scorpion|weevely|c99|r57|b374k)\b"
            r"|\$_(?:GET|POST|REQUEST|COOKIE)\s*\["
            r")"
        ),
        "threat_level": "high",
        "description": "WebShell检测: 匹配eval()、passthru()、<?php、蚁剑/冰蝎/哥斯拉等WebShell工具指纹",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 5,
        "auto_block": True,
        "block_duration": 168,
    },
    # ===== 6. RCE远程代码执行 =====
    {
        "name": "远程代码执行(RCE)",
        "attack_type": "RCE",
        "regex_pattern": (
            r"(?i)("
            r"\$\{jndi:"
            r"|\bjava\.lang\.Runtime\b"
            r"|\bProcessBuilder\b"
            r"|\blog4shell\b"
            r"|\bspring4shell\b"
            r"|\bognl\b"
            r"|\bClassLoader\b"
            r"|\"@type\"\s*:\s*\""
            r"|\bautoType\b"
            r"|\bRuntime\s*\.\s*getRuntime\b"
            r")"
        ),
        "threat_level": "high",
        "description": "RCE检测: 匹配${jndi:、Runtime、ProcessBuilder、log4shell、OGNL等远程代码执行特征",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 6,
        "auto_block": True,
        "block_duration": 168,
    },
    # ===== 7. 文件包含 =====
    {
        "name": "文件包含",
        "attack_type": "文件包含",
        "regex_pattern": (
            r"(?i)("
            r"php://filter"
            r"|php://input"
            r"|php://data"
            r"|data://text"
            r"|expect://\w+"
            r"|phar://"
            r"|zip://.*#"
            r")"
        ),
        "threat_level": "high",
        "description": "文件包含检测: 匹配php://filter、php://input、phar://等PHP伪协议",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 7,
        "auto_block": True,
        "block_duration": 24,
    },
    # ===== 8. SSRF =====
    {
        "name": "SSRF尝试",
        "attack_type": "SSRF",
        "regex_pattern": (
            r"(?i)("
            r"169\.254\.169\.254"
            r"|metadata\.google\.internal"
            r"|\bgopher://"
            r"|\bdict://"
            r"|\bsftp://"
            r"|\btftp://"
            r"|/latest/meta-data/"
            r")"
        ),
        "threat_level": "medium",
        "description": "SSRF检测: 匹配169.254.169.254云元数据、gopher://、dict://等危险协议",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 8,
        "auto_block": False,
        "block_duration": 0,
    },
    # ===== 9. 扫描探测 =====
    {
        "name": "扫描探测",
        "attack_type": "扫描探测",
        "regex_pattern": (
            r"(?i)\b("
            r"nmap|masscan|zmap|sqlmap|nikto"
            r"|dirbuster|gobuster|wfuzz|ffuf"
            r"|nessus|openvas|qualys|nexpose"
            r"|burpsuite|zaproxy|zap"
            r"|acunetix|awvs|appscan|arachni|w3af"
            r"|shodan|censys|fofa|zoomeye"
            r"|whatweb|wappalyzer"
            r"|zgrab|nuclei|httpx|subfinder"
            r")\b"
        ),
        "threat_level": "low",
        "description": "扫描探测检测: 匹配nmap、sqlmap、burpsuite、shodan等安全扫描工具名称",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 9,
        "auto_block": False,
        "block_duration": 0,
    },
    # ===== 10. 暴力破解 =====
    {
        "name": "暴力破解",
        "attack_type": "暴力破解",
        "regex_pattern": (
            r"(?i)("
            r"Failed\s+password\s+for\b"
            r"|\bauthentication\s+failure\b"
            r"|\bInvalid\s+user\b"
            r"|\bLOGIN\s+FAILED\b"
            r"|\bAccess\s+denied\b"
            r"|\btoo\s+many\s+failures\b"
            r"|\bmax\s+login\s+attempts\b"
            r")"
        ),
        "threat_level": "medium",
        "description": "暴力破解辅助检测: 匹配Failed password、LOGIN FAILED等认证失败日志(主判定由频次引擎处理)",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 10,
        "auto_block": False,
        "block_duration": 0,
    },
    # ===== 11. XXE =====
    {
        "name": "XXE外部实体注入",
        "attack_type": "XXE",
        "regex_pattern": (
            r"(?i)("
            r"<!ENTITY"
            r"|<!DOCTYPE[^>]*\[.*<!ENTITY"
            r"|xmlns:xi\s*=\s*[\"']http://www\.w3\.org/2001/XInclude"
            r"|<xi:include\b"
            r")"
        ),
        "threat_level": "high",
        "description": "XXE检测: 匹配<!ENTITY外部实体声明、XInclude注入",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 11,
        "auto_block": True,
        "block_duration": 24,
    },
    # ===== 12. LDAP注入 =====
    {
        "name": "LDAP注入检测",
        "attack_type": "LDAP注入",
        "regex_pattern": (
            r"(?i)("
            r"\bobjectClass\s*="
            r"|\bldaps?://"
            r"|\buserPassword\s*="
            r"|\badminAccountName\b"
            r"|\(\|?\(\s*\w+=\*\s*\)"
            r")"
        ),
        "threat_level": "high",
        "description": "LDAP注入检测: 匹配objectClass=、ldap://、userPassword=等LDAP特征",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 12,
        "auto_block": True,
        "block_duration": 24,
    },
    # ===== 13. 反序列化攻击 =====
    {
        "name": "反序列化攻击",
        "attack_type": "反序列化",
        "regex_pattern": (
            r"(?i)("
            r"aced\s*0005"
            r"|rO0AB[a-zA-Z0-9+/=]"
            r"|\bObjectInputStream\b"
            r"|\breadObject\b"
            r"|\bysoserial\b"
            r"|\bmarshalsec\b"
            r"|\bunserialize\s*\("
            r"|O:\d+:\"[a-zA-Z]"
            r"|a:\d+:\{[si]:\d+"
            r")"
        ),
        "threat_level": "high",
        "description": "反序列化检测: 匹配aced0005、rO0AB、ysoserial、unserialize()等序列化攻击特征",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 13,
        "auto_block": True,
        "block_duration": 168,
    },
    # ===== 14. CRLF注入 =====
    {
        "name": "CRLF注入检测",
        "attack_type": "CRLF注入",
        "regex_pattern": (
            r"(?i)("
            r"%0[dD]%0[aA]"
            r"|\\r\\n\s*(?:Set-Cookie|Location|Content-Type|HTTP/)"
            r"|\r?\n\s*(?:Set-Cookie|Location|Content-Type)\s*:"
            r")"
        ),
        "threat_level": "medium",
        "description": "CRLF注入检测: 匹配%0d%0a URL编码换行符及HTTP响应头注入",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 14,
        "auto_block": False,
        "block_duration": 0,
    },
    # ===== 15. 信息泄露 =====
    {
        "name": "信息泄露探测",
        "attack_type": "信息泄露",
        "regex_pattern": (
            r"(?i)("
            r"/\.git[/\s?]"
            r"|/\.svn[/\s?]"
            r"|/\.env[\s?]"
            r"|/\.htaccess[\s?]"
            r"|/\.htpasswd[\s?]"
            r"|/\.DS_Store[\s?]"
            r"|\bphpinfo\s*\("
            r"|/wp-config\.php\b"
            r"|/server-status\b"
            r"|/server-info\b"
            r"|/actuator[/\s?]"
            r"|/swagger[/\s?]"
            r"|\.(?:bak|old|swp|copy|dist)\b"
            r")"
        ),
        "threat_level": "low",
        "description": "信息泄露检测: 匹配.git/.env/.htaccess/phpinfo/wp-config等敏感文件路径",
        "match_field": "raw_log",
        "is_enabled": True,
        "priority": 15,
        "auto_block": False,
        "block_duration": 0,
    },
]
