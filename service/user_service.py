# -*- coding: utf-8 -*-
"""
用户服务
处理用户相关的业务逻辑
"""

import hashlib
import jwt
import datetime
from flask import current_app
from database import db
from model.user_model import User

def create_user(username, password, role=2):
    """
    创建新用户
    
    参数:
        username: 用户名
        password: 密码
        role: 用户角色权限，默认为2（普通用户），1为管理员
        
    返回:
        dict: 包含操作结果的字典
    """
    try:
        # 使用SHA256对密码进行加密
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password.encode('utf-8'))
        hashed_password = sha256_hash.hexdigest()
        
        # 创建新用户对象
        new_user = User(
            username=username,
            password=hashed_password,
            role=role
        )
        
        # 将用户添加到数据库会话
        db.session.add(new_user)
        
        # 提交事务
        db.session.commit()
        
        # 返回成功结果
        return {
            'success': True,
            'message': '用户注册成功',
            'user_id': new_user.id
        }
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        
        # 返回错误结果
        return {
            'success': False,
            'message': f'用户注册失败: {str(e)}'
        }

def create_admin_user(username, password):
    """
    创建管理员用户
    
    参数:
        username: 管理员用户名
        password: 管理员密码
        
    返回:
        dict: 包含操作结果的字典
    """
    return create_user(username, password, role=1)

def login_user(username, password):
    """
    用户登录验证
    
    参数:
        username: 用户名
        password: 密码
        
    返回:
        dict: 包含登录结果的字典，包含JWT令牌
    """
    try:
        # 使用SHA256对密码进行加密
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password.encode('utf-8'))
        hashed_password = sha256_hash.hexdigest()
        
        # 查询用户
        user = User.query.filter_by(username=username).first()
        
        # 验证用户是否存在和密码是否正确
        if not user or user.password != hashed_password:
            return {
                'success': False,
                'message': '用户名或密码错误'
            }
        
        # 生成JWT访问令牌
        access_token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
            'iat': datetime.datetime.utcnow()
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        # 生成JWT刷新令牌
        refresh_token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES']),
            'iat': datetime.datetime.utcnow()
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        # 返回成功结果，包含令牌和用户信息
        return {
            'success': True,
            'message': '登录成功',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }
    except Exception as e:
        # 返回错误结果
        return {
            'success': False,
            'message': f'登录失败: {str(e)}'
        }

def verify_jwt_token(token):
    """
    验证JWT令牌
    
    参数:
        token: JWT令牌
        
    返回:
        dict: 包含验证结果的字典
    """
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        
        # 返回解码后的载荷
        return {
            'success': True,
            'payload': payload
        }
    except jwt.ExpiredSignatureError:
        # 令牌已过期
        return {
            'success': False,
            'message': '令牌已过期'
        }
    except jwt.InvalidTokenError:
        # 令牌无效
        return {
            'success': False,
            'message': '令牌无效'
        }