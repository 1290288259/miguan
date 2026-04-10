# -*- coding: utf-8 -*-
"""
数据初始化脚本
用于插入默认数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from database import db
from model import user_model, honeypot_model, log_model, malicious_ip_model, match_rule_model, attack_stats_model, block_history_model, permission_model
from utils.time_utils import get_beijing_time

def init_data():
    """
    初始化数据
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    # 在应用上下文中操作数据
    with app.app_context():
        print("正在初始化数据...")
        
        # 创建默认管理员用户
        try:
            # 检查是否已有管理员用户
            admin_user = user_model.User.query.filter_by(username='administrator').first()
            if not admin_user:
                # 创建管理员用户
                admin_user = user_model.User(
                    username='administrator',
                    password='8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',  # 123456的SHA256值
                    role=1  # 管理员角色
                )
                db.session.add(admin_user)
                db.session.commit()
                print("已创建默认管理员用户: administrator/123456")
            else:
                print("管理员用户已存在")
        except Exception as e:
            print(f"创建管理员用户时出错: {e}")
            db.session.rollback()
        
        # 创建默认权限数据
        try:
            # 检查是否已有权限数据
            permission_count = permission_model.Permission.query.count()
            if permission_count == 0:
                # 创建管理员权限
                admin_permissions = [
                    {'role': 1, 'path': '/', 'description': '管理员-首页'},
                    {'role': 1, 'path': '/dashboard', 'description': '管理员-仪表盘'},
                    {'role': 1, 'path': '/logs', 'description': '管理员-日志管理'},
                    {'role': 1, 'path': '/honeypots', 'description': '管理员-蜜罐管理'},
                    {'role': 1, 'path': '/rules', 'description': '管理员-规则管理'},
                    {'role': 1, 'path': '/ips', 'description': '管理员-IP管理'},
                    {'role': 1, 'path': '/statistics', 'description': '管理员-统计分析'},
                    {'role': 1, 'path': '/users', 'description': '管理员-用户管理'},
                    {'role': 1, 'path': '/settings', 'description': '管理员-系统设置'},
                ]
                
                # 创建普通用户权限
                user_permissions = [
                    {'role': 2, 'path': '/', 'description': '用户-首页'},
                    {'role': 2, 'path': '/dashboard', 'description': '用户-仪表盘'},
                    {'role': 2, 'path': '/logs', 'description': '用户-日志查看'},
                    {'role': 2, 'path': '/statistics', 'description': '用户-统计分析'},
                ]
                
                # 添加所有权限
                for perm_data in admin_permissions + user_permissions:
                    permission = permission_model.Permission(**perm_data)
                    db.session.add(permission)
                
                db.session.commit()
                print("已创建默认权限数据")
            else:
                print("权限数据已存在")
        except Exception as e:
            print(f"创建权限数据时出错: {e}")
            db.session.rollback()
        
        # 创建示例蜜罐数据
        try:
            # 检查是否已有蜜罐数据
            honeypot_count = honeypot_model.Honeypot.query.count()
            if honeypot_count == 0:
                # 创建示例蜜罐
                honeypots = [
                    {
                        'name': 'SSH蜜罐',
                        'type': 'SSH',
                        'port': 2222,
                        'ip_address': '0.0.0.0',
                        'status': 'stopped',
                        'description': '模拟SSH服务的蜜罐，用于捕获SSH攻击'
                    },
                    {
                        'name': 'HTTP蜜罐',
                        'type': 'HTTP',
                        'port': 80,
                        'ip_address': '0.0.0.0',
                        'status': 'running',
                        'description': '模拟HTTP服务的蜜罐，用于捕获Web攻击'
                    },
                    {
                        'name': 'FTP蜜罐',
                        'type': 'FTP',
                        'port': 21,
                        'ip_address': '0.0.0.0',
                        'status': 'stopped',
                        'description': '模拟FTP服务的蜜罐，用于捕获FTP攻击'
                    }
                ]
                
                # 添加所有蜜罐
                for hp_data in honeypots:
                    honeypot = honeypot_model.Honeypot(**hp_data)
                    db.session.add(honeypot)
                
                db.session.commit()
                print("已创建示例蜜罐数据")
            else:
                print("蜜罐数据已存在")
        except Exception as e:
            print(f"创建蜜罐数据时出错: {e}")
            db.session.rollback()
        
        # 创建示例匹配规则（15大类，覆盖OWASP Top 10及常见网络攻击）
        try:
            rules = [
                # ===== 1. SQL注入（覆盖联合注入、盲注、堆叠注入、报错注入、编码绕过） =====
                {
                    'name': 'SQL注入检测',
                    'attack_type': 'SQL注入',
                    'regex_pattern': r"(?i)(union\s+(all\s+)?select|select\s+.+\s+from|insert\s+into|update\s+.+\s+set|delete\s+from|drop\s+(table|database)|truncate\s+table|alter\s+table|exec(\s+|\()|execute(\s+|\()|xp_cmdshell|sp_executesql|information_schema|into\s+(out|dump)file|load_file\s*\(|benchmark\s*\(|sleep\s*\(|waitfor\s+delay|having\s+\d|group\s+by.+having|'\s*(or|and)\s+['\d]|--\s*$|#\s*$|/\*.*\*/|0x[0-9a-f]+|char\s*\(|concat\s*\(|ascii\s*\(|substr\s*\(|hex\s*\(|unhex\s*\(|extractvalue\s*\(|updatexml\s*\(|floor\s*\(\s*rand)",
                    'threat_level': 'high',
                    'description': '检测SQL注入攻击，覆盖联合查询注入、布尔盲注、时间盲注、报错注入、堆叠查询、编码绕过等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 1,
                    'auto_block': True,
                    'block_duration': 24
                },
                # ===== 2. XSS（覆盖反射型、存储型、DOM型、SVG/MathML载体、事件处理器） =====
                {
                    'name': 'XSS攻击检测',
                    'attack_type': 'XSS',
                    'regex_pattern': r"(?i)(<script[\s>]|<\/script>|javascript\s*:|vbscript\s*:|on(load|error|click|mouseover|mouseout|mouseenter|mouseleave|mousedown|mouseup|focus|blur|change|submit|reset|select|keydown|keyup|keypress|dblclick|contextmenu|drag|drop|copy|paste|cut|input|invalid|search|wheel|scroll|touchstart|touchend|touchmove|animationstart|animationend|transitionend|hashchange|popstate)\s*=|<iframe|<embed|<object|<applet|<form\s|<img[^>]+onerror|<svg[^>]*on\w+=|<math|<marquee|<details[^>]*ontoggle|<video[^>]*on\w+=|<audio[^>]*on\w+=|<body[^>]*on\w+=|<input[^>]*on\w+=|<textarea[^>]*on\w+=|alert\s*\(|prompt\s*\(|confirm\s*\(|document\.(cookie|domain|write|location)|window\.(location|open|eval)|String\.fromCharCode|expression\s*\(|url\s*\(|data:text/html|<link[^>]*href\s*=\s*['\"]?javascript)",
                    'threat_level': 'medium',
                    'description': '检测跨站脚本攻击(XSS)，覆盖反射型、存储型、DOM型、事件处理器注入、SVG/MathML载体等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 2,
                    'auto_block': False,
                    'block_duration': 0
                },
                # ===== 3. 目录遍历（覆盖URL编码、双重编码、Unicode编码、敏感文件探测） =====
                {
                    'name': '目录遍历检测',
                    'attack_type': '目录遍历',
                    'regex_pattern': r"(?i)(\.\./|\.\.\\|%2e%2e(%2f|%5c|/|\\)|%252e%252e%252f|\.%2e/|%2e\./|\.\.%c0%af|\.\.%c1%9c|\.\.%255c|/etc/(passwd|shadow|hosts|group|sudoers|crontab|profile|bashrc|issue|hostname)|/proc/(self|version|cmdline|environ)|/var/log/|/windows/(win\.ini|system32|system\.ini)|boot\.ini|web\.config|\.htaccess|\.htpasswd|\.env|\.git/config|\.svn/entries|wp-config\.php|config\.(php|inc|yml|yaml|json|xml|ini))",
                    'threat_level': 'medium',
                    'description': '检测目录遍历攻击，覆盖URL编码绕过、双重编码、Unicode编码、敏感文件探测等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 3,
                    'auto_block': False,
                    'block_duration': 0
                },
                # ===== 4. 命令注入（覆盖管道符、反引号、变量替换、换行符编码） =====
                {
                    'name': '命令注入攻击',
                    'attack_type': '命令注入',
                    'regex_pattern': r"(?i)(;|\|{1,2}|&&|`|\$\(|\$\{|%0a|%0d|\r|\n|\x0a|\x0d)\s*(sudo|cat|tac|head|tail|more|less|nl|curl|wget|chmod|chown|chgrp|rm|mv|cp|mkdir|rmdir|bash|sh|csh|ksh|zsh|dash|perl|python[23]?|php|ruby|node|nc|ncat|netcat|nslookup|dig|host|ping|traceroute|ifconfig|ip\s|whoami|id|uname|hostname|pwd|ls|dir|find|grep|awk|sed|sort|kill|pkill|env|export|set|echo|printf|base64|xxd|od|rev|xargs|tee|touch|vi|vim|nano|crontab|at|scp|sftp|ssh|telnet|ftp|mail|sendmail|dpkg|rpm|yum|apt|pip|gem|npm)",
                    'threat_level': 'high',
                    'description': '检测命令注入攻击，覆盖管道符、反引号、变量替换、换行符编码、常见Linux/Windows命令注入',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 4,
                    'auto_block': True,
                    'block_duration': 24
                },
                # ===== 5. WebShell（覆盖PHP/JSP/ASP/Python各语言一句话木马、加密马、工具特征） =====
                {
                    'name': 'WebShell 上传/访问',
                    'attack_type': 'WebShell',
                    'regex_pattern': r"(?i)(eval\s*\(|assert\s*\(|system\s*\(|passthru\s*\(|shell_exec\s*\(|exec\s*\(|popen\s*\(|proc_open\s*\(|pcntl_exec\s*\(|call_user_func\s*\(|call_user_func_array\s*\(|create_function\s*\(|array_map\s*\(.*(system|exec|passthru)|preg_replace\s*\(.*/e|base64_decode\s*\(|gzinflate\s*\(|gzuncompress\s*\(|str_rot13\s*\(|move_uploaded_file\s*\(|\$_(GET|POST|REQUEST|COOKIE)\s*\[|Runtime\.getRuntime\(\)\.exec|ProcessBuilder|<%.*Runtime|\.getRuntime\(\)|os\.system\s*\(|os\.popen\s*\(|subprocess\.(call|run|Popen)|commands\.getoutput|\?cmd=|\?exec=|\?eval=|\?shell=|\?command=|c99|r57|b374k|weevely|webacoo|phpspy|antsword|behinder|godzilla|ice_scorpion)",
                    'threat_level': 'high',
                    'description': '检测WebShell木马后门，覆盖PHP/JSP/ASP/Python各语言一句话木马、加密马、冰蝎/蚁剑/哥斯拉等工具特征',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 5,
                    'auto_block': True,
                    'block_duration': 168
                },
                # ===== 6. RCE远程代码执行（覆盖Struts2/Log4j/Spring/Fastjson/ThinkPHP等） =====
                {
                    'name': '远程代码执行(RCE)',
                    'attack_type': 'RCE',
                    'regex_pattern': r"(?i)(ognl|#_memberAccess|class\.classLoader|java\.lang\.(Runtime|ProcessBuilder|Thread|ClassLoader)|javax\.script\.ScriptEngine|\$\{jndi:(ldap|rmi|dns|iiop)://|log4(j|shell)|CVE-20\d{2}|spring(4|cloud)?shell|\.class\.module\.classLoader|com\.sun\.rowset|java\.net\.URL|java\.io\.(File|InputStream|ObjectInputStream)|org\.apache\.(xalan|commons)|bcel|T\(java\.lang\.|SpEL|__import__|getattr|globals\(\)|compile\(|__builtins__|think\\\\app|think\\\\invokefunction|s2-0\d{2}|fastjson|parseObject|@type|autoType|com\.sun\.org)",
                    'threat_level': 'high',
                    'description': '检测远程代码执行(RCE)，覆盖Struts2 OGNL注入、Log4Shell、Spring4Shell、Fastjson反序列化、ThinkPHP RCE等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 6,
                    'auto_block': True,
                    'block_duration': 168
                },
                # ===== 7. 文件包含（覆盖PHP伪协议、空字节截断、多种参数名探测） =====
                {
                    'name': '文件包含',
                    'attack_type': '文件包含',
                    'regex_pattern': r"(?i)(\?(page|file|include|path|dir|document|folder|root|pg|style|template|action|lang|language|mod|module|load|read|content|layout|view|theme|skin|cat|src)=)\s*(http://|https://|ftp://|file://|php://filter|php://input|php://output|php://data|php://memory|php://temp|php://fd|data://text|expect://|zip://|phar://|glob://|rar://|ogg://|ssh2://|zlib://|\.\./|/etc/|/proc/|/var/|/tmp/|C:\\|%00|%2500)",
                    'threat_level': 'high',
                    'description': '检测本地/远程文件包含(LFI/RFI)，覆盖PHP伪协议、空字节截断、多种参数名探测',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 7,
                    'auto_block': True,
                    'block_duration': 24
                },
                # ===== 8. SSRF（覆盖内网IP、IPv6回环、云元数据接口、多种协议探测） =====
                {
                    'name': 'SSRF尝试',
                    'attack_type': 'SSRF',
                    'regex_pattern': r"(?i)(\?(url|link|src|source|target|dest|redirect|uri|path|continue|window|next|data|reference|site|html|val|validate|domain|callback|return|page|feed|host|port|to|out|view|dir|show|navigation|open|file|document|folder|pg|style|img|filename)=)\s*(https?://127\.|https?://localhost|https?://0\.0\.0\.0|https?://\[::1\]|https?://169\.254\.169\.254|https?://metadata\.(google|aws)|https?://100\.100\.100\.200|https?://10\.|https?://192\.168\.|https?://172\.(1[6-9]|2\d|3[01])\.|file://|gopher://|dict://|sftp://|tftp://|ldap://|jar://|netdoc://)",
                    'threat_level': 'medium',
                    'description': '检测服务器端请求伪造(SSRF)，覆盖内网IP、IPv6回环、云元数据接口(AWS/GCP/阿里云)、多种协议探测',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 8,
                    'auto_block': False,
                    'block_duration': 0
                },
                # ===== 9. 扫描探测（覆盖端口扫描、漏洞扫描、Web扫描、渗透框架、资产测绘） =====
                {
                    'name': '扫描探测',
                    'attack_type': '扫描探测',
                    'regex_pattern': r"(?i)(nmap|masscan|zmap|zgrab|nikto|sqlmap|w3af|nessus|openvas|dirbuster|dirb|gobuster|feroxbuster|ffuf|wfuzz|hydra|medusa|patator|hashcat|john|aircrack|metasploit|msfconsole|cobalt\s*strike|empire|mimikatz|bloodhound|responder|impacket|crackmapexec|evil-winrm|chisel|proxychains|Acunetix|BurpSuite|AppScan|WebInspect|Arachni|OWASP[_\s]ZAP|Nuclei|httpx|subfinder|amass|theHarvester|recon-ng|shodan|censys|fofa|zoomeye|WPScan|JoomScan|DroopeScan|CMSmap|XSStrike|tplmap|commix|NoSQLMap|SSTImap)",
                    'threat_level': 'low',
                    'description': '检测恶意扫描器探测行为，覆盖端口扫描、漏洞扫描、Web扫描、暴破工具、渗透框架、资产测绘平台等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 9,
                    'auto_block': False,
                    'block_duration': 0
                },
                # ===== 10. 暴力破解（覆盖SSH/FTP/HTTP/RDP/SMTP等多协议认证失败特征） =====
                {
                    'name': '暴力破解',
                    'attack_type': '暴力破解',
                    'regex_pattern': r"(?i)(Failed password|Invalid user|authentication fail(ure|ed)|incorrect password|login fail(ure|ed)|access denied|bad password|wrong password|invalid credentials|account locked|too many (failed |login )?attempts|maximum.*retries|brute.?force|credential.?stuffing|unauthorized|401\s+Unauthorized|403\s+Forbidden.*login|repeated login|multiple failed|INVALID_LOGIN|AUTH_FAILED|LOGIN_REJECTED|password mismatch|invalid token|session expired after multiple)",
                    'threat_level': 'medium',
                    'description': '检测密码暴力破解，覆盖SSH/FTP/HTTP/RDP/SMTP等多协议认证失败特征、账户锁定、凭证填充等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 10,
                    'auto_block': False,
                    'block_duration': 0
                },
                # ===== 11. XXE XML外部实体注入（新增） =====
                {
                    'name': 'XXE外部实体注入',
                    'attack_type': 'XXE',
                    'regex_pattern': r"(?i)(<!DOCTYPE[^>]*\[|<!ENTITY\s+|SYSTEM\s+['\"]?(https?://|file://|php://|expect://|gopher://|jar://|netdoc://|data:)|%\w+;|&#x?[0-9a-f]+;.*SYSTEM|PUBLIC\s+['\"][^'\"]*['\"]|<!ATTLIST|<!ELEMENT|<\?xml[^>]*encoding|xmlns:xi=|xi:include|xinclude|<!NOTATION|DTD\s+(URL|SYSTEM)|xml-stylesheet.*href\s*=\s*['\"]?(http|ftp|file|php|expect|data))",
                    'threat_level': 'high',
                    'description': '检测XML外部实体注入(XXE)，覆盖外部实体声明、参数实体、SSRF通道、文件读取、远程DTD加载等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 11,
                    'auto_block': True,
                    'block_duration': 24
                },
                # ===== 12. LDAP注入（新增） =====
                {
                    'name': 'LDAP注入检测',
                    'attack_type': 'LDAP注入',
                    'regex_pattern': r"(?i)(\)\s*\(|\(\s*\||\(\s*&|\*\s*\)|\)\s*\(\s*\||!\s*\(|\)\s*%26|\)\s*%7c|objectClass=\*|cn=\*|uid=\*|userPassword|memberOf|dn:|changetype:|ldap://|ldaps://|LDAP\s+injection|modify:\s*|add:\s*|delete:\s*|replace:\s*)",
                    'threat_level': 'high',
                    'description': '检测LDAP注入攻击，覆盖布尔型LDAP注入、通配符注入、LDAP协议探测、敏感属性查询等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 12,
                    'auto_block': True,
                    'block_duration': 24
                },
                # ===== 13. 反序列化攻击（新增） =====
                {
                    'name': '反序列化攻击',
                    'attack_type': '反序列化',
                    'regex_pattern': r"(?i)(aced0005|rO0AB|O:\d+:\"|a:\d+:\{|s:\d+:\"|java\.io\.ObjectInputStream|readObject\s*\(|readUnshared\s*\(|ObjectInputStream|ObjectOutputStream|java\.util\.HashMap|org\.apache\.(commons\.(collections|beanutils|io)|xalan)|com\.(sun|mchange)|bcel|javassist|net\.sf\.ehcache|groovy\.runtime|org\.codehaus|org\.springframework|ysoserial|marshalsec|jrmp|gadget.?chain|commons-collections|BeanComparator|InvokerTransformer|ChainedTransformer|ConstantTransformer|LazyMap|TiedMapEntry|BadAttributeValueExpException|__reduce__|pickle\.(loads|load)|yaml\.(unsafe_load|load)|Marshal\.(load|restore)|unserialize\s*\(|php://input.*unserialize)",
                    'threat_level': 'high',
                    'description': '检测反序列化攻击，覆盖Java/PHP/Python/Ruby反序列化漏洞利用链、ysoserial/marshalsec工具特征、Gadget链等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 13,
                    'auto_block': True,
                    'block_duration': 168
                },
                # ===== 14. CRLF注入/HTTP响应拆分（新增） =====
                {
                    'name': 'CRLF注入检测',
                    'attack_type': 'CRLF注入',
                    'regex_pattern': r"(?i)(%0d%0a|%0d|%0a|%0D%0A|\r\n|\x0d\x0a|%E5%98%8A%E5%98%8D|%c0%8d%c0%8a|\\r\\n)(Set-Cookie|Location|Content-Type|Content-Length|HTTP/\d|Host:|X-Forwarded|Transfer-Encoding|Connection:|Refresh:|X-XSS-Protection|Content-Security-Policy|Access-Control)|(%0d%0a|%0D%0A|\r\n){2}(<html|<script|HTTP/)",
                    'threat_level': 'medium',
                    'description': '检测CRLF注入/HTTP响应拆分攻击，覆盖换行符编码注入、HTTP头注入、Cookie注入、XSS联动等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 14,
                    'auto_block': False,
                    'block_duration': 0
                },
                # ========== 15. 敏感信息泄露探测（新增类别） ==========
                {
                    'name': '信息泄露探测',
                    'attack_type': '信息泄露',
                    'regex_pattern': r"(?i)(/(\.git|\.svn|\.hg|\.bzr|\.env|\.DS_Store|\.idea|\.vscode|\.settings|\.project|\.classpath|\.bak|\.swp|\.sav|\.old|\.orig|\.tmp|\.temp|\.log|\.sql|\.tar|\.gz|\.zip|\.rar|\.7z|\.dump|\.bkp|\.conf|\.cfg|\.config|\.properties|\.yml|\.yaml|\.toml|phpinfo|php_info|server-status|server-info|debug|trace|actuator|swagger|api-docs|graphql|console|adminer|phpmyadmin|phppgadmin|webdav|backup|database|db_backup|dump|export|sitemap\.xml|robots\.txt|crossdomain\.xml|\.well-known|xmlrpc\.php)(\s|/|\?|$))|(/wp-admin/install|/install\.php|/setup\.php|/config\.php\.bak|/web\.config\.bak|/application\.properties|/application\.yml|/WEB-INF/(web\.xml|classes|lib))",
                    'threat_level': 'low',
                    'description': '检测敏感信息泄露探测，覆盖版本控制目录、备份文件、配置文件、调试接口、管理后台、数据库备份等',
                    'match_field': 'raw_log',
                    'is_enabled': True,
                    'priority': 15,
                    'auto_block': False,
                    'block_duration': 0
                }
            ]
            
            # 使用更平滑的逻辑：如果不存在相同的攻击检测名则插入
            inserted_count = 0
            for rule_data in rules:
                existing_rule = match_rule_model.MatchRule.query.filter_by(name=rule_data['name']).first()
                if not existing_rule:
                    rule = match_rule_model.MatchRule(**rule_data)
                    db.session.add(rule)
                    inserted_count += 1
            
            if inserted_count > 0:
                db.session.commit()
                print(f"新增补充了 {inserted_count} 条攻击类型的匹配规则")
            else:
                print("匹配规则已完整存在，无需补充")
        except Exception as e:
            print(f"创建匹配规则时出错: {e}")
            db.session.rollback()
        
        # 创建示例日志数据
        try:
            # 检查是否已有日志数据
            log_count = log_model.Log.query.count()
            if log_count == 0:
                # 获取蜜罐数据
                ssh_honeypot = honeypot_model.Honeypot.query.filter_by(type='SSH').first()
                http_honeypot = honeypot_model.Honeypot.query.filter_by(type='HTTP').first()
                
                if ssh_honeypot and http_honeypot:
                    # 创建示例日志
                    from datetime import datetime, timedelta
                    import random
                    
                    # 生成随机IP地址
                    def random_ip():
                        return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    
                    # 创建示例日志数据
                    for i in range(50):
                        # 随机选择蜜罐
                        honeypot = random.choice([ssh_honeypot, http_honeypot])
                        
                        # 随机生成攻击时间
                        attack_time = get_beijing_time() - timedelta(hours=random.randint(1, 72))
                        
                        # 根据蜜罐类型生成不同的日志
                        if honeypot.type == 'SSH':
                            raw_log = f"Failed password for root from {random_ip()} port {random.randint(10000, 60000)} ssh2"
                            attack_type = random.choice(['暴力破解', '字典攻击', '凭证填充'])
                            protocol = 'SSH'
                            source_port = random.randint(10000, 60000)
                            target_port = 22
                        else:  # HTTP
                            raw_log = f"{random_ip()} - - [{attack_time.strftime('%d/%b/%Y:%H:%M:%S +0000')}] \"GET /admin.php?id=1' OR '1'='1 HTTP/1.1\" 200 1234"
                            attack_type = random.choice(['SQL注入', 'XSS', '目录遍历', '命令注入'])
                            protocol = 'HTTP'
                            source_port = random.randint(10000, 60000)
                            target_port = 80
                        
                        # 创建日志记录
                        log = log_model.Log(
                            honeypot_id=honeypot.id,
                            attacker_ip=random_ip(),
                            attack_time=attack_time,
                            raw_log=raw_log,
                            source_ip=random_ip(),
                            target_ip='192.168.1.100',
                            source_port=source_port,
                            target_port=target_port,
                            protocol=protocol,
                            user_agent=random.choice(['Mozilla/5.0', 'curl/7.68.0', 'python-requests/2.25.1']),
                            request_path=random.choice(['/admin.php', '/login.php', '/index.php', '/config.php']),
                            attack_type=attack_type,
                            attack_description=f"检测到{attack_type}攻击",
                            payload=random.choice(["' OR '1'='1", "<script>alert('XSS')</script>", "../../../etc/passwd"]),
                            threat_level=random.choice(['low', 'medium', 'high', 'critical']),
                            is_malicious=random.choice([True, False]),
                            is_blocked=random.choice([True, False]),
                            blocked_time=attack_time if random.choice([True, False]) else None,
                            notes=f"示例日志数据 {i+1}"
                        )
                        
                        db.session.add(log)
                    
                    db.session.commit()
                    print("已创建示例日志数据")
                else:
                    print("未找到蜜罐数据，跳过创建日志数据")
            else:
                print("日志数据已存在")
        except Exception as e:
            print(f"创建日志数据时出错: {e}")
            db.session.rollback()
        
        print("数据初始化完成！")

if __name__ == '__main__':
    init_data()