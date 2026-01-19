# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库和初始化数据表
"""

import pymysql
from config import Config

def create_database():
    """
    创建数据库
    如果数据库不存在，则创建它
    """
    # 数据库连接配置
    host = 'localhost'
    user = 'root'
    password = '123456'
    database = 'bishe'
    
    try:
        # 连接MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        # 创建游标对象
        cursor = connection.cursor()
        
        # 检查数据库是否存在
        cursor.execute(f"SHOW DATABASES LIKE '{database}'")
        result = cursor.fetchone()
        
        # 如果数据库不存在，则创建它
        if not result:
            cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 '{database}' 创建成功！")
        else:
            print(f"数据库 '{database}' 已存在！")
        
        # 关闭游标和连接
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"创建数据库时出错: {e}")
        return False

if __name__ == "__main__":
    # 创建数据库
    if create_database():
        print("数据库初始化完成！")
    else:
        print("数据库初始化失败！")