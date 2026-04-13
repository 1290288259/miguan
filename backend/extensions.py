# -*- coding: utf-8 -*-
"""
Flask 扩展实例集中管理模块

将 SocketIO 等全局扩展实例在此处创建，
避免在 app.py 中创建后被 werkzeug reloader 重新加载导致实例不一致。

其他模块（如 log_service.py）应从此处导入 socketio，而非从 app.py 导入。
"""

from flask_socketio import SocketIO

# 全局唯一的 SocketIO 实例
# 在 app.py 的 create_app() 中调用 socketio.init_app(app) 进行初始化
socketio = SocketIO()
