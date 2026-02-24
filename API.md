# Flask API 接口文档

本文档描述了Flask后端API接口的使用方法。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

## 通用响应格式

所有API响应都遵循以下格式：

```json
{
  "code": 200, // 200表示成功，非200表示失败
  "message": "响应消息（可选）",
  "data": "响应数据（可选）"
}
```

## 认证方式

大多数接口需要JWT认证。在请求头中添加：
`Authorization: Bearer <access_token>`

## API 接口列表

### 1. 用户认证

#### 1.1 用户登录

- **URL**: `/api/user/login`
- **Method**: `POST`
- **Body**:
```json
{
    "username": "administrator",
    "password": "password"
}
```

#### 1.2 用户注册

- **URL**: `/api/user/register`
- **Method**: `POST`
- **Body**:
```json
{
    "username": "newuser",
    "password": "password",
    "role": 2 // 1: 管理员, 2: 普通用户
}
```

### 2. AI 配置管理

#### 2.1 获取所有配置

- **URL**: `/api/ai-config/`
- **Method**: `GET`
- **Auth**: Required

#### 2.2 创建配置

- **URL**: `/api/ai-config/`
- **Method**: `POST`
- **Auth**: Required
- **Body**:
```json
{
    "name": "DeepSeek-V3",
    "api_url": "https://api.deepseek.com",
    "model_name": "deepseek-chat",
    "api_key": "sk-...",
    "provider": "DeepSeek",
    "is_auto_block": false
}
```

#### 2.3 更新配置

- **URL**: `/api/ai-config/<config_id>`
- **Method**: `PUT`
- **Auth**: Required
- **Body**: 同创建配置

#### 2.4 删除配置

- **URL**: `/api/ai-config/<config_id>`
- **Method**: `DELETE`
- **Auth**: Required

#### 2.5 激活配置

- **URL**: `/api/ai-config/<config_id>/activate`
- **Method**: `POST`
- **Auth**: Required

#### 2.6 禁用配置

- **URL**: `/api/ai-config/<config_id>/deactivate`
- **Method**: `POST`
- **Auth**: Required

#### 2.7 测试配置

- **URL**: `/api/ai-config/<config_id>/test`
- **Method**: `POST`
- **Auth**: Required

### 3. 日志查询

#### 3.1 获取日志列表

- **URL**: `/api/logs/`
- **Method**: `GET`
- **Auth**: Required
- **Params**:
  - `page`: 页码
  - `per_page`: 每页数量
  - `start_time`: 开始时间
  - `end_time`: 结束时间

### 4. 蜜罐管理

#### 4.1 获取蜜罐列表

- **URL**: `/api/honeypots/`
- **Method**: `GET`
- **Auth**: Required

### 5. 恶意IP管理

#### 5.1 获取恶意IP列表

- **URL**: `/api/malicious-ips/`
- **Method**: `GET`
- **Auth**: Required

#### 5.2 封禁IP

- **URL**: `/api/malicious-ips/block`
- **Method**: `POST`
- **Auth**: Required
- **Body**:
```json
{
    "ip_address": "1.2.3.4",
    "reason": "恶意攻击",
    "duration": 24 // 封禁时长（小时）
}
```
