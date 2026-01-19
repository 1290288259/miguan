# -*- coding: utf-8 -*-
"""
蜜罐服务
处理蜜罐相关的业务逻辑，包括启动、停止蜜罐进程
"""

from model.honeypot_model import Honeypot
from database import db
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess
import sys
import os
import signal
import psutil

# 用于存储运行中的蜜罐进程
# key: honeypot_id, value: subprocess.Popen object
running_honeypots = {}

class HoneypotService:
    """
    蜜罐服务类
    提供蜜罐的增删改查及启停功能
    """
    
    @staticmethod
    def get_honeypots(page: int = 1, per_page: int = 20, type: str = None, 
                      status: str = None, keyword: str = None) -> Tuple[List[Dict], Dict]:
        """
        分页查询蜜罐
        """
        try:
            query = Honeypot.query
            
            if type:
                query = query.filter(Honeypot.type == type)
            
            if status:
                query = query.filter(Honeypot.status == status)
                
            if keyword:
                query = query.filter(
                    Honeypot.name.like(f'%{keyword}%') |
                    Honeypot.description.like(f'%{keyword}%') |
                    Honeypot.ip_address.like(f'%{keyword}%')
                )
            
            total = query.count()
            offset = (page - 1) * per_page
            honeypots = query.offset(offset).limit(per_page).all()
            
            # 更新内存中的状态到数据库显示（可选，或者直接信任数据库状态）
            # 这里我们简单检查一下进程是否还活着
            for hp in honeypots:
                if hp.id in running_honeypots:
                    proc = running_honeypots[hp.id]
                    if proc.poll() is not None:
                        # 进程已结束
                        del running_honeypots[hp.id]
                        hp.status = 'stopped'
                        db.session.commit()
            
            hp_list = [hp.to_dict() for hp in honeypots]
            
            pagination = {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_prev': page > 1,
                'has_next': page * per_page < total
            }
            
            return hp_list, pagination
            
        except Exception as e:
            print(f"查询蜜罐时发生错误: {str(e)}")
            return [], {'error': str(e)}

    @staticmethod
    def get_honeypot_by_id(hp_id: int) -> Optional[Dict]:
        try:
            hp = Honeypot.query.get(hp_id)
            if hp:
                return hp.to_dict()
            return None
        except Exception as e:
            print(f"查询蜜罐详情错误: {e}")
            return None

    @staticmethod
    def create_honeypot(data: Dict) -> Dict:
        try:
            hp = Honeypot(
                name=data.get('name'),
                type=data.get('type'),
                port=data.get('port'),
                ip_address=data.get('ip_address', '0.0.0.0'),
                description=data.get('description'),
                config=data.get('config'),
                status='stopped'
            )
            db.session.add(hp)
            db.session.commit()
            return {'id': hp.id, 'message': '蜜罐创建成功'}
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}

    @staticmethod
    def update_honeypot(hp_id: int, data: Dict) -> Dict:
        try:
            hp = Honeypot.query.get(hp_id)
            if not hp:
                return {'error': '蜜罐不存在'}
            
            if 'name' in data: hp.name = data['name']
            if 'type' in data: hp.type = data['type']
            if 'port' in data: hp.port = data['port']
            if 'description' in data: hp.description = data['description']
            
            db.session.commit()
            return {'message': '蜜罐更新成功'}
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}

    @staticmethod
    def delete_honeypot(hp_id: int) -> Dict:
        try:
            hp = Honeypot.query.get(hp_id)
            if not hp:
                return {'error': '蜜罐不存在'}
            
            # 如果正在运行，先停止
            if hp.id in running_honeypots or hp.status == 'running':
                HoneypotService.stop_honeypot(hp_id)
            
            db.session.delete(hp)
            db.session.commit()
            return {'message': '蜜罐删除成功'}
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}

    @staticmethod
    def start_honeypot(hp_id: int) -> Dict:
        try:
            hp = Honeypot.query.get(hp_id)
            if not hp:
                return {'error': '蜜罐不存在'}
            
            if hp.status == 'running' and hp.id in running_honeypots:
                return {'error': '蜜罐已经在运行中'}
            
            # 确定脚本路径
            script_path = None
            if hp.type.upper() == 'SSH':
                script_path = os.path.join(os.getcwd(), 'honeypots', 'ssh_server.py')
            else:
                return {'error': f'暂不支持 {hp.type} 类型的蜜罐自动启动'}
            
            if not os.path.exists(script_path):
                return {'error': f'找不到蜜罐脚本: {script_path}'}
            
            # 启动进程
            # 使用 python 解释器运行脚本，并传入端口参数
            cmd = [sys.executable, script_path, str(hp.port)]
            
            # Windows下使用creationflags=subprocess.CREATE_NEW_CONSOLE可以避免子进程随主进程退出（可选）
            # 这里为了简单管理，作为子进程运行
            process = subprocess.Popen(
                cmd,
                cwd=os.getcwd(),
                # stdout=subprocess.PIPE, 
                # stderr=subprocess.PIPE
                # 不捕获输出，直接输出到控制台或者后续重定向到日志文件
            )
            
            running_honeypots[hp.id] = process
            hp.status = 'running'
            db.session.commit()
            
            return {'message': f'蜜罐 {hp.name} 已启动', 'pid': process.pid}
            
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def stop_honeypot(hp_id: int) -> Dict:
        try:
            hp = Honeypot.query.get(hp_id)
            if not hp:
                return {'error': '蜜罐不存在'}
            
            if hp.id in running_honeypots:
                proc = running_honeypots[hp.id]
                # 终止进程
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                
                del running_honeypots[hp.id]
            
            # 即使进程不在内存字典中（例如重启后），也要尝试更新数据库状态
            hp.status = 'stopped'
            db.session.commit()
            
            return {'message': f'蜜罐 {hp.name} 已停止'}
            
        except Exception as e:
            return {'error': str(e)}
