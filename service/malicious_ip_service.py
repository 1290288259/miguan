# -*- coding: utf-8 -*-
"""
恶意IP服务
处理恶意IP的记录、封禁和解封逻辑
"""

import platform
import subprocess
import json
from datetime import datetime
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
                malicious_ip.last_seen = datetime.utcnow()
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
    def block_ip(ip_address: str, reason: str = None, duration: int = None) -> dict:
        """
        封禁IP
        根据操作系统执行相应的封禁命令
        """
        try:
            malicious_ip = MaliciousIP.query.filter_by(ip_address=ip_address).first()
            if not malicious_ip:
                return {'success': False, 'message': '未找到该IP记录'}
            
            if malicious_ip.is_blocked:
                return {'success': False, 'message': '该IP已被封禁'}

            system = platform.system()
            success = False
            error_msg = ""

            if system == "Windows":
                # Windows防火墙命令
                # netsh advfirewall firewall add rule name="Block IP {ip}" dir=in action=block remoteip={ip}
                rule_name = f"Block_IP_{ip_address}"
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip_address}'
                try:
                    # 使用 subprocess.run 执行命令，需要管理员权限运行程序
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        success = True
                    else:
                        error_msg = f"Windows封禁失败: {result.stderr}"
                except Exception as e:
                    error_msg = f"执行Windows命令出错: {str(e)}"

            elif system == "Linux":
                # Linux iptables命令
                # iptables -A INPUT -s {ip} -j DROP
                cmd = ['iptables', '-A', 'INPUT', '-s', ip_address, '-j', 'DROP']
                try:
                    # 需要root权限
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        success = True
                    else:
                        error_msg = f"Linux封禁失败: {result.stderr}"
                except Exception as e:
                    error_msg = f"执行Linux命令出错: {str(e)}"
            
            else:
                error_msg = f"不支持的操作系统: {system}"

            if success:
                malicious_ip.is_blocked = True
                malicious_ip.blocked_time = datetime.utcnow()
                malicious_ip.block_reason = reason
                if duration:
                    # 这里暂不实现自动解封调度，仅记录期限
                    # malicious_ip.block_until = ... 
                    pass
                db.session.commit()
                return {'success': True, 'message': f'IP {ip_address} 已成功封禁'}
            else:
                return {'success': False, 'message': error_msg}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'封禁操作异常: {str(e)}'}

    @staticmethod
    def unblock_ip(ip_address: str) -> dict:
        """
        解封IP
        """
        try:
            malicious_ip = MaliciousIP.query.filter_by(ip_address=ip_address).first()
            if not malicious_ip:
                return {'success': False, 'message': '未找到该IP记录'}
            
            if not malicious_ip.is_blocked:
                return {'success': False, 'message': '该IP未被封禁'}

            system = platform.system()
            success = False
            error_msg = ""

            if system == "Windows":
                # Windows防火墙命令
                # netsh advfirewall firewall delete rule name="Block IP {ip}"
                rule_name = f"Block_IP_{ip_address}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    # Windows delete rule 如果规则不存在会报错，但也算解封成功（或者没封）
                    # 但这里我们根据数据库状态是已封禁，所以应该存在
                    if result.returncode == 0 or "没有与指定标准匹配的规则" in result.stdout:
                        success = True
                    else:
                        error_msg = f"Windows解封失败: {result.stderr}"
                except Exception as e:
                    error_msg = f"执行Windows命令出错: {str(e)}"

            elif system == "Linux":
                # Linux iptables命令
                # iptables -D INPUT -s {ip} -j DROP
                cmd = ['iptables', '-D', 'INPUT', '-s', ip_address, '-j', 'DROP']
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        success = True
                    else:
                        error_msg = f"Linux解封失败: {result.stderr}"
                except Exception as e:
                    error_msg = f"执行Linux命令出错: {str(e)}"
            
            else:
                error_msg = f"不支持的操作系统: {system}"

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
