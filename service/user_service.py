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
from sqlalchemy.exc import IntegrityError
from model.user_model import User
from model.user_info_model import UserInfo
from model.permission_model import Permission

def create_user(username, password, role=2, phone=None, email=None):
    """
    创建新用户
    
    参数:
        username: 用户名
        password: 密码
        role: 用户角色权限，默认为2（普通用户），1为管理员
        phone: 手机号
        email: 邮箱
        
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
        # 刷新以获取ID
        db.session.flush()
        
        # 创建用户信息
        if phone or email:
            user_info = UserInfo(
                user_id=new_user.id,
                phone=phone,
                email=email
            )
            db.session.add(user_info)
        
        # 提交事务
        db.session.commit()
        
        # 返回成功结果
        return {
            'success': True,
            'message': '用户注册成功',
            'user_id': new_user.id
        }
    except IntegrityError:
        # 发生完整性错误（如用户名已存在）时回滚事务
        db.session.rollback()
        return {
            'success': False,
            'message': '用户注册失败: 该用户名已被注册'
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

def get_user_detail(user_id):
    """
    获取用户详细信息（包含基础信息和扩展信息）
    
    参数:
        user_id: 用户ID
        
    返回:
        dict: 包含操作结果的字典
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}
            
        # 获取扩展信息
        user_info = UserInfo.query.filter_by(user_id=user_id).first()
        
        # 基础信息
        data = user.to_dict()
        
        # 添加扩展信息
        if user_info:
            data['phone'] = user_info.phone
            data['email'] = user_info.email
        else:
            data['phone'] = None
            data['email'] = None
            
        # 获取权限列表
        permissions = Permission.query.filter_by(role=user.role).all()
        data['permissions'] = [p.to_dict() for p in permissions]
            
        return {
            'success': True,
            'data': data
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}

def update_user_detail(user_id, phone=None, email=None, password=None, old_password=None):
    """
    更新用户详细信息
    
    参数:
        user_id: 用户ID
        phone: 手机号
        email: 邮箱
        password: 新密码
        old_password: 旧密码
        
    返回:
        dict: 包含操作结果的字典
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}
            
        # 如果需要修改密码
        if password:
            if not old_password:
                return {'success': False, 'message': '修改密码需要提供旧密码'}
            
            # 验证旧密码
            sha256_hash = hashlib.sha256()
            sha256_hash.update(old_password.encode('utf-8'))
            hashed_old_password = sha256_hash.hexdigest()
            
            if user.password != hashed_old_password:
                return {'success': False, 'message': '旧密码错误'}
                
            # 更新密码
            sha256_hash_new = hashlib.sha256()
            sha256_hash_new.update(password.encode('utf-8'))
            user.password = sha256_hash_new.hexdigest()
            
        # 查找或创建扩展信息
        user_info = UserInfo.query.filter_by(user_id=user_id).first()
        if not user_info:
            user_info = UserInfo(user_id=user_id)
            db.session.add(user_info)
            
        # 更新字段
        if phone is not None:
            user_info.phone = phone
        if email is not None:
            user_info.email = email
            
        db.session.commit()
        
        return {
            'success': True,
            'message': '用户信息更新成功'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'更新失败: {str(e)}'}

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
        
        # 获取权限列表
        permissions = Permission.query.filter_by(role=user.role).all()
        permissions_data = [p.to_dict() for p in permissions]

        # 返回成功结果，包含令牌和用户信息
        return {
            'success': True,
            'message': '登录成功',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'permissions': permissions_data
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