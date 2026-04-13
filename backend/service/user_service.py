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
from model.module_model import Module, UserModule

# ... (omitted)

def create_user(username, password, role=2, phone=None, email=None, module_ids=None):
    """
    创建新用户
    
    参数:
        username: 用户名
        password: 密码
        role: 用户角色权限，默认为2（普通用户），1为管理员
        phone: 手机号
        email: 邮箱
        module_ids: 模块ID列表
        
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
            
        # 分配模块权限
        if module_ids:
            for mid in module_ids:
                um = UserModule(user_id=new_user.id, module_id=mid)
                db.session.add(um)
        else:
            # 如果未指定模块，根据角色分配默认模块
            default_modules = []
            if role == 1:
                # 管理员拥有所有模块
                default_modules = Module.query.all()
            elif role == 2:
                # 普通用户拥有基础模块
                # 这里根据路径或名称筛选
                default_modules = Module.query.filter(Module.path.in_(['/', '/log-query', '/malicious-ip-management'])).all()
            
            for mod in default_modules:
                um = UserModule(user_id=new_user.id, module_id=mod.id)
                db.session.add(um)
        
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

        # 获取用户模块列表
        user_modules = UserModule.query.filter_by(user_id=user.id).all()
        module_ids = [um.module_id for um in user_modules]
        modules = Module.query.filter(Module.id.in_(module_ids)).all()
        data['modules'] = [m.to_dict() for m in modules]
            
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

def get_all_permissions():
    """
    获取所有权限列表
    
    返回:
        dict: 权限列表（按角色分组）
    """
    try:
        permissions = Permission.query.all()
        
        # 按角色分组
        role_permissions = {}
        for p in permissions:
            if p.role not in role_permissions:
                role_permissions[p.role] = []
            role_permissions[p.role].append(p.to_dict())
            
        return {
            'success': True,
            'data': role_permissions
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}

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
        
        # 验证用户是否存在
        if not user:
            return {
                'success': False,
                'message': '用户名或密码错误'
            }
            
        now = datetime.datetime.utcnow()

        # 检查账户是否已被锁定
        if user.locked_until and user.locked_until > now:
            minutes_left = int((user.locked_until - now).total_seconds() / 60) + 1
            return {
                'success': False,
                'message': f'由于连续多次尝试失败，账户已被锁定，请在 {minutes_left} 分钟后再试'
            }

        # 如果密码不正确
        if user.password != hashed_password:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            
            # 如果达到5次，则锁定账户15分钟
            if user.failed_login_attempts >= 5:
                user.locked_until = now + datetime.timedelta(minutes=15)
                db.session.commit()
                return {
                    'success': False,
                    'message': '密码错误次数过多，您的账户已被锁定 15 分钟'
                }
            
            db.session.commit()
            remaining_attempts = 5 - user.failed_login_attempts
            return {
                'success': False,
                'message': f'用户名或密码错误，还有 {remaining_attempts} 次尝试机会'
            }
            
        # 登录成功，重置失败次数和锁定时间
        if (user.failed_login_attempts and user.failed_login_attempts > 0) or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
        
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

        # 获取用户模块列表
        user_modules = UserModule.query.filter_by(user_id=user.id).all()
        module_ids = [um.module_id for um in user_modules]
        modules = Module.query.filter(Module.id.in_(module_ids)).all()
        modules_data = [m.to_dict() for m in modules]

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
                'permissions': permissions_data,
                'modules': modules_data
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

def get_user_list(page=1, size=10, keyword=None, role=None):
    """
    获取用户列表（分页）
    
    参数:
        page: 页码
        size: 每页数量
        keyword: 搜索关键词（用户名/手机/邮箱）
        role: 角色ID
        
    返回:
        dict: 包含用户列表和分页信息的字典
    """
    try:
        query = User.query
        
        # 关联查询用户信息
        query = query.outerjoin(UserInfo, User.id == UserInfo.user_id)
        
        # 关键词搜索
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                (User.username.like(keyword_pattern)) | 
                (UserInfo.phone.like(keyword_pattern)) | 
                (UserInfo.email.like(keyword_pattern))
            )
            
        # 角色筛选
        if role is not None and role != '':
            query = query.filter(User.role == role)
            
        # 分页
        pagination = query.paginate(page=page, per_page=size, error_out=False)
        
        users = []
        for user in pagination.items:
            user_data = user.to_dict()
            # 获取扩展信息
            user_info = UserInfo.query.filter_by(user_id=user.id).first()
            if user_info:
                user_data['phone'] = user_info.phone
                user_data['email'] = user_info.email
            else:
                user_data['phone'] = None
                user_data['email'] = None
                
            # 获取用户模块权限
            user_modules = UserModule.query.filter_by(user_id=user.id).all()
            module_ids = [um.module_id for um in user_modules]
            modules = Module.query.filter(Module.id.in_(module_ids)).all()
            user_data['modules'] = [m.to_dict() for m in modules]
            
            users.append(user_data)
            
        return {
            'success': True,
            'data': {
                'items': users,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}

def delete_user(user_id):
    """
    删除用户
    
    参数:
        user_id: 用户ID
        
    返回:
        dict: 操作结果
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}
            
        # 删除关联的用户信息
        UserInfo.query.filter_by(user_id=user_id).delete()
        UserModule.query.filter_by(user_id=user_id).delete()
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return {'success': True, 'message': '用户删除成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'删除失败: {str(e)}'}

def admin_update_user(user_id, username=None, password=None, role=None, phone=None, email=None, module_ids=None):
    """
    管理员更新用户信息
    
    参数:
        user_id: 用户ID
        username: 用户名
        password: 新密码 (直接重置，无需旧密码)
        role: 角色
        phone: 手机号
        email: 邮箱
        module_ids: 模块ID列表
        
    返回:
        dict: 操作结果
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}
            
        # 更新基础信息
        if username:
            # 检查用户名是否重复
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != int(user_id):
                return {'success': False, 'message': '用户名已存在'}
            user.username = username
            
        if password:
            sha256_hash = hashlib.sha256()
            sha256_hash.update(password.encode('utf-8'))
            user.password = sha256_hash.hexdigest()
            
        if role is not None:
            user.role = role
            
        # 更新扩展信息
        user_info = UserInfo.query.filter_by(user_id=user_id).first()
        if not user_info:
            user_info = UserInfo(user_id=user_id)
            db.session.add(user_info)
            
        if phone is not None:
            user_info.phone = phone
        if email is not None:
            user_info.email = email
            
        # 更新模块权限
        if module_ids is not None:
            # 删除旧权限
            UserModule.query.filter_by(user_id=user_id).delete()
            # 添加新权限
            for mid in module_ids:
                um = UserModule(user_id=user_id, module_id=mid)
                db.session.add(um)
            
        db.session.commit()
        
        return {'success': True, 'message': '用户信息更新成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'更新失败: {str(e)}'}

def get_all_modules():
    """
    获取所有模块列表
    
    返回:
        dict: 模块列表
    """
    try:
        modules = Module.query.all()
        return {
            'success': True,
            'data': [m.to_dict() for m in modules]
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}