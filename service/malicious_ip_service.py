# -*- coding: utf-8 -*-
"""
恶意IP服务
处理恶意IP的记录、封禁和解封逻辑
"""

import platform
import subprocess
import json
from datetime import datetime
from utils.time_utils import get_beijing_time
from model.malicious_ip_model import MaliciousIP
from database import db
from utils.ip_utils import get_ip_location

class MaliciousIPService:
    """
    恶意IP服务类
    """
    
    @staticmethod
    def record_malicious_ip(ip_address: str, attack_type: str = None, 
                          threat_level: str = 'medium', source_honeypot_id: int = None,
                          notes: str = None) -> MaliciousIP:
        """
        记录恶意IP
        如果IP已存在，更新其信息；如果不存在，创建新记录
        """
        try:
            # 获取IP地理位置信息
            location, isp = get_ip_location(ip_address)
            
            malicious_ip = MaliciousIP.query.filter_by(ip_address=ip_address).first()
            
            if malicious_ip:
                # 更新现有记录
                malicious_ip.last_seen = get_beijing_time()
                malicious_ip.attack_count += 1
                
                # 如果位置信息缺失，则更新
                if not malicious_ip.location or malicious_ip.location == "未知":
                    malicious_ip.location = location
                if not malicious_ip.isp:
                    malicious_ip.isp = isp
                
                # 更新攻击类型列表
                current_types = []
                if malicious_ip.attack_types:
                    try:
                        current_types = json.loads(malicious_ip.attack_types)
                    except:
                        current_types = []
                
                if attack_type and attack_type not in current_types:
                    current_types.append(attack_type)
                    malicious_ip.attack_types = json.dumps(current_types)
                
                # 更新威胁等级（如果新的等级更高）
                levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                current_level_val = levels.get(malicious_ip.threat_level, 0)
                new_level_val = levels.get(threat_level, 0)
                
                if new_level_val > current_level_val:
                    malicious_ip.threat_level = threat_level
                
                # 更新来源蜜罐列表
                if source_honeypot_id:
                    current_honeypots = []
                    if malicious_ip.source_honeypots:
                        try:
                            current_honeypots = json.loads(malicious_ip.source_honeypots)
                        except:
                            current_honeypots = []
                    
                    if source_honeypot_id not in current_honeypots:
                        current_honeypots.append(source_honeypot_id)
                        malicious_ip.source_honeypots = json.dumps(current_honeypots)
                
                if notes:
                    malicious_ip.notes = (malicious_ip.notes or "") + f" | {notes}"
                    
            else:
                # 创建新记录
                attack_types_json = json.dumps([attack_type]) if attack_type else json.dumps([])
                source_honeypots_json = json.dumps([source_honeypot_id]) if source_honeypot_id else json.dumps([])
                
                malicious_ip = MaliciousIP(
                    ip_address=ip_address,
                    attack_types=attack_types_json,
                    threat_level=threat_level,
                    source_honeypots=source_honeypots_json,
                    notes=notes,
                    location=location,
                    isp=isp
                )
                db.session.add(malicious_ip)
            
            db.session.commit()
            return malicious_ip
            
        except Exception as e:
            db.session.rollback()
            print(f"记录恶意IP时出错: {str(e)}")
            return None

    @staticmethod
    def block_ip(ip_address: str, reason: str = None, duration: int = None, block_until: str = None) -> dict:
        """
        封禁IP
        根据操作系统自动检测并调用相应的防火墙命令进行封禁
        Windows: netsh advfirewall firewall
        Linux: iptables
        """
        try:
            # 1. 检查IP是否已存在且已封禁
            malicious_ip = MaliciousIP.query.filter_by(ip_address=ip_address).first()
            if not malicious_ip:
                # 如果不存在，先创建记录（虽然一般是从列表操作，但也可能直接封禁）
                # 这里假设必须先有记录
                return {'success': False, 'message': '未找到该IP记录，请先添加或等待其攻击被记录'}
            
            if malicious_ip.is_blocked:
                return {'success': False, 'message': '该IP已被封禁，无需重复操作'}

            # 2. 检测操作系统
            system_platform = platform.system()
            success = False
            error_msg = ""
            
            print(f"正在执行IP封禁操作，目标IP: {ip_address}, 操作系统: {system_platform}")

            # 3. 根据系统执行封禁命令
            if system_platform == "Windows":
                # Windows防火墙命令
                # 规则名称: Block_IP_{ip}
                rule_name = f"Block_IP_{ip_address}"
                
                # 检查并删除可能存在的旧规则，避免重复
                check_cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                subprocess.run(check_cmd, shell=True, capture_output=True)
                
                # 添加封禁规则
                # dir=in: 入站流量
                # action=block: 阻止
                # remoteip={ip}: 远程IP
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip_address}'
                
                try:
                    # Windows下执行命令 (需要管理员权限)
                    # 尝试指定编码为gbk以捕获中文输出
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
                    
                    # 检查返回码
                    if result.returncode == 0:
                        success = True
                        print(f"Windows防火墙规则添加成功: {rule_name}")
                    else:
                        # 尝试从stderr或stdout获取错误信息
                        err = result.stderr.strip() if result.stderr else result.stdout.strip()
                        error_msg = f"Windows封禁失败: {err}"
                        print(error_msg)
                        
                        # 如果是因为需要提权，给出提示
                        if "提升" in error_msg or "Run as administrator" in error_msg:
                            error_msg += " (请尝试以管理员权限运行后端服务)"
                            
                except Exception as e:
                    error_msg = f"执行Windows命令异常: {str(e)}"
                    print(error_msg)

            elif system_platform == "Linux":
                # Linux iptables命令
                # 使用 -I INPUT 1 插入到第一条，确保优先级最高
                
                # 检查是否已存在规则
                check_cmd = ['iptables', '-C', 'INPUT', '-s', ip_address, '-j', 'DROP']
                try:
                    check_result = subprocess.run(check_cmd, capture_output=True)
                    if check_result.returncode == 0:
                        # 规则已存在
                        success = True
                        print(f"Linux iptables规则已存在: {ip_address}")
                    else:
                        # 添加规则
                        cmd = ['iptables', '-I', 'INPUT', '1', '-s', ip_address, '-j', 'DROP']
                        # Linux下执行命令 (需要root权限)
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            success = True
                            print(f"Linux iptables规则添加成功: {ip_address}")
                        else:
                            error_msg = f"Linux封禁失败 (请确保以root运行): {result.stderr.strip()}"
                            print(error_msg)
                except Exception as e:
                    error_msg = f"执行Linux命令异常: {str(e)}"
                    print(error_msg)
            
            else:
                error_msg = f"不支持的操作系统: {system_platform}"
                print(error_msg)

            # 4. 更新数据库状态
            if success:
                malicious_ip.is_blocked = True
                malicious_ip.blocked_time = get_beijing_time()
                malicious_ip.block_reason = reason
                
                # 处理封禁时长/截止时间
                if block_until:
                    try:
                        # 尝试解析前端传来的时间字符串
                        # 前端通常传来 ISO 格式或者 YYYY-MM-DD HH:MM:SS
                        # 这里简单处理，假设是标准格式
                        if isinstance(block_until, str):
                            # 如果包含T，可能是ISO格式
                            if 'T' in block_until:
                                from dateutil import parser
                                dt = parser.parse(block_until)
                                # 转换为本地时间或者直接存储（取决于数据库时区设置，这里假设是naive datetime）
                                # 由于 get_beijing_time 返回的是 naive datetime，这里也保持一致
                                malicious_ip.block_until = dt.replace(tzinfo=None)
                            else:
                                malicious_ip.block_until = datetime.strptime(block_until, "%Y-%m-%d %H:%M:%S")
                        else:
                            malicious_ip.block_until = block_until
                    except Exception as e:
                        print(f"解析封禁截止时间失败: {e}")
                        pass
                elif duration:
                    # 如果只传了duration（秒），则计算截止时间
                    from datetime import timedelta
                    malicious_ip.block_until = get_beijing_time() + timedelta(seconds=duration)
                
                db.session.commit()
                return {'success': True, 'message': f'IP {ip_address} 已成功封禁'}
            else:
                return {'success': False, 'message': error_msg}

        except Exception as e:
            db.session.rollback()
            print(f"封禁操作发生未捕获异常: {str(e)}")
            return {'success': False, 'message': f'封禁操作异常: {str(e)}'}

    @staticmethod
    def unblock_ip(ip_address: str) -> dict:
        """
        解封IP
        根据操作系统自动检测并调用相应的防火墙命令进行解封
        """
        try:
            # 1. 检查IP是否已封禁
            malicious_ip = MaliciousIP.query.filter_by(ip_address=ip_address).first()
            if not malicious_ip:
                return {'success': False, 'message': '未找到该IP记录'}
            
            if not malicious_ip.is_blocked:
                return {'success': False, 'message': '该IP未被封禁，无需解封'}

            # 2. 检测操作系统
            system_platform = platform.system()
            success = False
            error_msg = ""
            
            print(f"正在执行IP解封操作，目标IP: {ip_address}, 操作系统: {system_platform}")

            # 3. 根据系统执行解封命令
            if system_platform == "Windows":
                # Windows防火墙命令
                # 删除规则: netsh advfirewall firewall delete rule name="Block_IP_{ip}"
                rule_name = f"Block_IP_{ip_address}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    # Windows delete rule 如果规则不存在会报错，但也算解封成功（或者没封）
                    # 只要不出现权限错误等严重错误，都视为成功
                    if result.returncode == 0 or "没有与指定标准匹配的规则" in result.stdout or "No rules match" in result.stdout:
                        success = True
                        print(f"Windows防火墙规则删除成功: {rule_name}")
                    else:
                        error_msg = f"Windows解封失败: {result.stderr.strip()}"
                        print(error_msg)
                except Exception as e:
                    error_msg = f"执行Windows命令出错: {str(e)}"
                    print(error_msg)

            elif system_platform == "Linux":
                # Linux iptables命令
                # 删除规则: iptables -D INPUT -s {ip} -j DROP
                cmd = ['iptables', '-D', 'INPUT', '-s', ip_address, '-j', 'DROP']
                
                try:
                    # 首先检查规则是否存在，如果不存在则直接视为成功
                    check_cmd = ['iptables', '-C', 'INPUT', '-s', ip_address, '-j', 'DROP']
                    check_result = subprocess.run(check_cmd, capture_output=True)
                    
                    if check_result.returncode != 0:
                        # 规则不存在，直接视为解封成功
                        success = True
                        print(f"Linux iptables规则不存在，无需删除: {ip_address}")
                    else:
                        # 执行删除
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            success = True
                            print(f"Linux iptables规则删除成功: {ip_address}")
                        else:
                            error_msg = f"Linux解封失败: {result.stderr.strip()}"
                            print(error_msg)
                except Exception as e:
                    error_msg = f"执行Linux命令出错: {str(e)}"
                    print(error_msg)
            
            else:
                error_msg = f"不支持的操作系统: {system_platform}"
                print(error_msg)

            # 4. 更新数据库状态
            if success:
                malicious_ip.is_blocked = False
                malicious_ip.blocked_time = None
                malicious_ip.block_reason = None
                malicious_ip.block_until = None
                db.session.commit()
                return {'success': True, 'message': f'IP {ip_address} 已成功解封'}
            else:
                return {'success': False, 'message': error_msg}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'解封操作异常: {str(e)}'}

    @staticmethod
    def check_expired_blocks(app):
        """
        检查并解封已过期的IP
        需要传入app实例以获取应用上下文
        """
        try:
            with app.app_context():
                current_time = get_beijing_time()
                # 查询所有已封禁且到期时间小于当前时间的IP
                expired_ips = MaliciousIP.query.filter(
                    MaliciousIP.is_blocked == True,
                    MaliciousIP.block_until != None,
                    MaliciousIP.block_until < current_time
                ).all()
                
                if expired_ips:
                    print(f"检测到 {len(expired_ips)} 个过期的封禁IP，开始自动解封...")
                    for ip in expired_ips:
                        print(f"正在自动解封过期IP: {ip.ip_address} (到期时间: {ip.block_until})")
                        # 必须在应用上下文中执行解封逻辑
                        # MaliciousIPService.unblock_ip 内部会提交事务，这里不需要手动commit
                        # 但是 unblock_ip 是静态方法，且内部没有 app_context 管理，所以需要确保在上下文中调用
                        # 由于我们已经在 with app.app_context() 中，这应该没问题
                        # 注意：unblock_ip 可能会提交事务，导致 expired_ips 列表失效，但这只是简单的对象列表，应该没事
                        # 为了安全起见，我们还是重新获取或者只取需要的字段
                        MaliciousIPService.unblock_ip(ip.ip_address)
                        
        except Exception as e:
            print(f"检查过期封禁IP时出错: {str(e)}")

    @staticmethod
    def get_malicious_ips(page: int = 1, per_page: int = 20, 
                         is_blocked: bool = None, threat_level: str = None, 
                         keyword: str = None) -> tuple:
        """
        分页获取恶意IP列表
        """
        try:
            query = MaliciousIP.query
            
            if is_blocked is not None:
                query = query.filter(MaliciousIP.is_blocked == is_blocked)
                
            if threat_level:
                query = query.filter(MaliciousIP.threat_level == threat_level)
                
            if keyword:
                query = query.filter(
                    MaliciousIP.ip_address.like(f'%{keyword}%') |
                    MaliciousIP.notes.like(f'%{keyword}%') |
                    MaliciousIP.location.like(f'%{keyword}%')
                )
            
            # 按最后活动时间倒序
            query = query.order_by(MaliciousIP.last_seen.desc())
            
            total = query.count()
            offset = (page - 1) * per_page
            items = query.offset(offset).limit(per_page).all()
            
            return [item.to_dict() for item in items], {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            print(f"查询恶意IP列表出错: {str(e)}")
            return [], {'error': str(e)}
