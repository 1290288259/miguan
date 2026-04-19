# -*- coding: utf-8 -*-
"""
蜜罐服务
统一管理蜜罐进程的启动、停止、健康检查和状态同步。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import os
import subprocess
import sys
import time

import psutil

from database import db
from model.honeypot_model import Honeypot


@dataclass
class HoneypotRuntime:
    honeypot_id: int
    pid: int
    process: Optional[subprocess.Popen] = None
    script_path: Optional[str] = None


# key: honeypot_id, value: HoneypotRuntime
running_honeypots: Dict[int, HoneypotRuntime] = {}


class HoneypotService:
    STATUS_RUNNING = 'running'
    STATUS_STOPPED = 'stopped'

    SCRIPT_MAP = {
        'SSH': 'ssh_server.py',
        'HTTP': 'hikvision_http_server.py',
        'FTP': 'ftp_server.py',
        'REDIS': 'redis_server.py',
        'MYSQL': 'mysql_server.py'
    }

    @staticmethod
    def _get_backend_root() -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def _get_honeypot_scripts_dir(cls) -> str:
        return os.path.join(cls._get_backend_root(), 'honeypots')

    @classmethod
    def _resolve_script_path(cls, hp_type: str) -> Optional[str]:
        script_name = cls.SCRIPT_MAP.get((hp_type or '').upper())
        if not script_name:
            return None
        return os.path.join(cls._get_honeypot_scripts_dir(), script_name)

    @classmethod
    def _build_command(cls, hp: Honeypot) -> Optional[List[str]]:
        script_path = cls._resolve_script_path(hp.type)
        if not script_path:
            return None
        return [sys.executable, script_path, str(hp.port)]

    @staticmethod
    def _is_pid_alive(pid: Optional[int]) -> bool:
        return bool(pid) and psutil.pid_exists(pid)

    @classmethod
    def _process_matches_honeypot(cls, process: psutil.Process, hp: Honeypot) -> bool:
        try:
            cmdline = [part.lower() for part in process.cmdline()]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

        script_path = cls._resolve_script_path(hp.type)
        if not script_path:
            return False

        script_name = os.path.basename(script_path).lower()
        port = str(hp.port)
        
        script_match = any(script_name in part for part in cmdline)
        port_match = port in cmdline
        return script_match and port_match

    @staticmethod
    def _is_listening_on_port(process: psutil.Process, port: int) -> bool:
        try:
            # 同样需要检查所有的子进程，有的框架/蜜罐会 fork 出工作进程来监听端口
            processes_to_check = [process] + process.children(recursive=True)
            for p in processes_to_check:
                try:
                    for conn in p.net_connections(kind='inet'):
                        if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.laddr.port == port:
                            return True
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
        return False

    @classmethod
    def _inspect_honeypot_process(cls, hp: Honeypot) -> Dict:
        pid = hp.pid
        if not cls._is_pid_alive(pid):
            return {
                'is_running': False,
                'pid': None,
                'healthy': False,
                'reason': 'pid_not_found',
            }

        try:
            process = psutil.Process(pid)
            if not cls._process_matches_honeypot(process, hp):
                return {
                    'is_running': False,
                    'pid': None,
                    'healthy': False,
                    'reason': 'process_mismatch',
                }

            is_healthy = cls._is_listening_on_port(process, hp.port)
            return {
                'is_running': True,
                'pid': pid,
                'healthy': is_healthy,
                'reason': 'ok' if is_healthy else 'port_not_listening',
                'process': process,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return {
                'is_running': False,
                'pid': None,
                'healthy': False,
                'reason': 'process_unavailable',
            }

    @classmethod
    def _register_runtime(
        cls,
        hp: Honeypot,
        process: Optional[subprocess.Popen] = None,
        pid: Optional[int] = None,
    ) -> None:
        runtime_pid = pid if pid is not None else getattr(process, 'pid', None)
        if not runtime_pid:
            return

        running_honeypots[hp.id] = HoneypotRuntime(
            honeypot_id=hp.id,
            pid=runtime_pid,
            process=process,
            script_path=cls._resolve_script_path(hp.type),
        )

    @staticmethod
    def _unregister_runtime(hp_id: int) -> None:
        running_honeypots.pop(hp_id, None)

    @classmethod
    def _sync_honeypot_status(cls, hp: Honeypot, commit: bool = False) -> Dict:
        inspection = cls._inspect_honeypot_process(hp)
        actual_status = cls.STATUS_RUNNING if inspection['is_running'] else cls.STATUS_STOPPED
        actual_pid = inspection['pid']

        changed = hp.status != actual_status or hp.pid != actual_pid
        if changed:
            hp.status = actual_status
            hp.pid = actual_pid
            if commit:
                db.session.commit()

        if inspection['is_running'] and actual_pid:
            cls._register_runtime(hp, pid=actual_pid)
        else:
            cls._unregister_runtime(hp.id)

        return {
            'honeypot_id': hp.id,
            'status': actual_status,
            'pid': actual_pid,
            'healthy': inspection['healthy'],
            'reason': inspection['reason'],
            'changed': changed,
        }

    @classmethod
    def _sync_honeypots_status(cls, honeypots: List[Honeypot]) -> Dict[int, Dict]:
        results: Dict[int, Dict] = {}
        has_changes = False

        for hp in honeypots:
            result = cls._sync_honeypot_status(hp, commit=False)
            results[hp.id] = result
            has_changes = has_changes or result['changed']

        if has_changes:
            db.session.commit()

        return results

    @classmethod
    def health_check(cls, hp_id: int) -> Dict:
        hp = Honeypot.query.get(hp_id)
        if not hp:
            return {'error': '蜜罐不存在'}
        return cls._sync_honeypot_status(hp, commit=True)

    @classmethod
    def sync_all_statuses(cls) -> None:
        honeypots = Honeypot.query.all()
        cls._sync_honeypots_status(honeypots)

    @staticmethod
    def get_honeypots(
        page: int = 1,
        per_page: int = 20,
        type: str = None,
        status: str = None,
        keyword: str = None,
    ) -> Tuple[List[Dict], Dict]:
        try:
            HoneypotService.sync_all_statuses()

            query = Honeypot.query

            if type:
                query = query.filter(Honeypot.type == type)

            if status:
                query = query.filter(Honeypot.status == status)

            if keyword:
                query = query.filter(
                    Honeypot.name.like(f'%{keyword}%')
                    | Honeypot.description.like(f'%{keyword}%')
                    | Honeypot.ip_address.like(f'%{keyword}%')
                )

            total = query.count()
            offset = (page - 1) * per_page
            honeypots = query.offset(offset).limit(per_page).all()

            hp_list = [hp.to_dict() for hp in honeypots]
            pagination = {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_prev': page > 1,
                'has_next': page * per_page < total,
            }
            return hp_list, pagination

        except Exception as e:
            print(f"查询蜜罐时发生错误: {str(e)}")
            return [], {'error': str(e)}

    @staticmethod
    def get_honeypot_by_id(hp_id: int) -> Optional[Dict]:
        try:
            hp = Honeypot.query.get(hp_id)
            if not hp:
                return None

            HoneypotService._sync_honeypot_status(hp, commit=True)
            return hp.to_dict()
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
                status=HoneypotService.STATUS_STOPPED,
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

            HoneypotService._sync_honeypot_status(hp, commit=True)
            if hp.status == HoneypotService.STATUS_RUNNING:
                return {'error': '请先停止蜜罐，再修改配置信息'}

            if 'name' in data:
                hp.name = data['name']
            if 'type' in data:
                hp.type = data['type']
            if 'port' in data:
                hp.port = data['port']
            if 'description' in data:
                hp.description = data['description']
            if 'ip_address' in data:
                hp.ip_address = data['ip_address']
            if 'config' in data:
                hp.config = data['config']

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

            HoneypotService._sync_honeypot_status(hp, commit=True)
            if hp.status == HoneypotService.STATUS_RUNNING:
                stop_result = HoneypotService.stop_honeypot(hp_id)
                if 'error' in stop_result:
                    return stop_result

            db.session.delete(hp)
            db.session.commit()
            HoneypotService._unregister_runtime(hp_id)
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

            status_info = HoneypotService._sync_honeypot_status(hp, commit=True)
            if status_info['status'] == HoneypotService.STATUS_RUNNING:
                return {
                    'message': f'蜜罐 {hp.name} 已在运行中',
                    'pid': hp.pid,
                    'healthy': status_info['healthy'],
                }

            script_path = HoneypotService._resolve_script_path(hp.type)
            if not script_path:
                return {'error': f'暂不支持 {hp.type} 类型的蜜罐自动启动'}

            if not os.path.exists(script_path):
                return {'error': f'找不到蜜罐脚本: {script_path}'}

            cmd = HoneypotService._build_command(hp)
            
            # 移除 Werkzeug 相关环境变量，防止子进程被当成 reload 子进程
            env = os.environ.copy()
            env.pop('WERKZEUG_RUN_MAIN', None)
            env.pop('WERKZEUG_SERVER_FD', None)
            
            process = subprocess.Popen(
                cmd,
                cwd=HoneypotService._get_backend_root(),
                env=env,
            )

            HoneypotService._register_runtime(hp, process=process)
            hp.status = HoneypotService.STATUS_RUNNING
            hp.pid = process.pid
            db.session.commit()

            # 启动后稍作等待然后做一次同步，避免进程秒退但数据库仍显示运行中。
            time.sleep(1.0)
            status_info = HoneypotService._sync_honeypot_status(hp, commit=True)
            if status_info['status'] != HoneypotService.STATUS_RUNNING:
                return {'error': f'蜜罐 {hp.name} 启动失败，可能是端口冲突或配置错误，请检查端口是否被占用'}

            return {
                'message': f'蜜罐 {hp.name} 已启动',
                'pid': hp.pid,
                'healthy': status_info['healthy'],
            }
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}

    @staticmethod
    def stop_honeypot(hp_id: int) -> Dict:
        try:
            hp = Honeypot.query.get(hp_id)
            if not hp:
                return {'error': '蜜罐不存在'}

            HoneypotService._sync_honeypot_status(hp, commit=True)
            target_pid = hp.pid

            if not target_pid:
                hp.status = HoneypotService.STATUS_STOPPED
                hp.pid = None
                db.session.commit()
                HoneypotService._unregister_runtime(hp.id)
                return {'message': f'蜜罐 {hp.name} 已停止'}

            try:
                process = psutil.Process(target_pid)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass

            HoneypotService._unregister_runtime(hp.id)
            hp.status = HoneypotService.STATUS_STOPPED
            hp.pid = None
            db.session.commit()

            return {'message': f'蜜罐 {hp.name} 已停止'}
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}

    @staticmethod
    def init_honeypots():
        """
        初始化蜜罐服务。
        服务启动时统一同步数据库状态，并为仍在运行的蜜罐恢复运行时登记。
        """
        try:
            HoneypotService.sync_all_statuses()
            running = Honeypot.query.filter_by(status=HoneypotService.STATUS_RUNNING).all()
            print(f"已同步蜜罐状态，当前共有 {len(running)} 个蜜罐运行中。")
        except Exception as e:
            print(f"初始化蜜罐服务出错: {e}")
