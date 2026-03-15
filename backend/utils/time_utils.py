# -*- coding: utf-8 -*-
"""
时间工具类
处理时间相关的辅助函数
"""

from datetime import datetime, timedelta

def get_beijing_time():
    """
    获取当前北京时间 (UTC+8)
    返回不带时区信息的 naive datetime 对象，方便存入数据库
    """
    return datetime.utcnow() + timedelta(hours=8)
