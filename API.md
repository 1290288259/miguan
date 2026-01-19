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
  "status": "success|error",
  "message": "响应消息（可选）",
  "data": "响应数据（可选）"
}
```

## 错误响应

当请求失败时，API会返回相应的HTTP状态码和错误信息：

- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## API 接口列表

### 1. 问候接口

获取简单的问候信息。

**请求方式**: `GET`

**请求URL**: `/api/hello`

**请求参数**: 无

**响应示例**:
```json
{
  "message": "你好！欢迎使用Flask标准框架",
  "status": "success"
}
```

---

### 2. 获取单个用户信息

根据用户ID获取用户信息。

**请求方式**: `GET`

**请求URL**: `/api/user/{user_id}`

**路径参数**:
- `user_id` (int): 用户ID

**响应示例**:
```json
{
  "user": {
    "name": "张三",
    "email": "zhangsan@example.com",
    "age": 25
  },
  "status": "success"
}
```

**错误响应**:
```json
{
  "message": "用户不存在",
  "status": "error"
}
```

---

### 3. 获取所有用户信息

获取所有用户的信息列表。

**请求方式**: `GET`

**请求URL**: `/api/users`

**请求参数**: 无

**响应示例**:
```json
{
  "users": [
    {
      "id": 1,
      "name": "张三",
      "email": "zhangsan@example.com",
      "age": 25
    },
    {
      "id": 2,
      "name": "李四",
      "email": "lisi@example.com",
      "age": 30
    },
    {
      "id": 3,
      "name": "王五",
      "email": "wangwu@example.com",
      "age": 28
    }
  ],
  "count": 3,
  "status": "success"
}
```

---

### 4. 创建用户

创建一个新的用户。

**请求方式**: `POST`

**请求URL**: `/api/user`

**请求头**:
- `Content-Type: application/json`

**请求体**:
```json
{
  "name": "赵六",
  "email": "zhaoliu@example.com",
  "age": 35
}
```

**请求参数**:
- `name` (string, 必需): 用户姓名
- `email` (string, 必需): 用户邮箱
- `age` (int, 可选): 用户年龄

**响应示例**:
```json
{
  "user": {
    "id": 4,
    "name": "赵六",
    "email": "zhaoliu@example.com",
    "age": 35
  },
  "message": "用户创建成功",
  "status": "success"
}
```

**错误响应**:
```json
{
  "message": "缺少必需字段",
  "status": "error"
}
```

---

### 5. 更新用户信息

更新指定用户的信息。

**请求方式**: `PUT`

**请求URL**: `/api/user/{user_id}`

**路径参数**:
- `user_id` (int): 用户ID

**请求头**:
- `Content-Type: application/json`

**请求体**:
```json
{
  "name": "张三三",
  "email": "zhangsansan@example.com",
  "age": 26
}
```

**请求参数**:
- `name` (string, 可选): 用户姓名
- `email` (string, 可选): 用户邮箱
- `age` (int, 可选): 用户年龄

**响应示例**:
```json
{
  "user": {
    "name": "张三三",
    "email": "zhangsansan@example.com",
    "age": 26
  },
  "message": "用户信息更新成功",
  "status": "success"
}
```

**错误响应**:
```json
{
  "message": "用户不存在",
  "status": "error"
}
```

---

### 6. 删除用户

删除指定的用户。

**请求方式**: `DELETE`

**请求URL**: `/api/user/{user_id}`

**路径参数**:
- `user_id` (int): 用户ID

**响应示例**:
```json
{
  "message": "用户删除成功",
  "status": "success"
}
```

**错误响应**:
```json
{
  "message": "用户不存在",
  "status": "error"
}
```

---

### 7. 文件上传

上传文件到服务器。

**请求方式**: `POST`

**请求URL**: `/api/upload`

**请求头**:
- `Content-Type: multipart/form-data`

**请求参数**:
- `file` (file, 必需): 要上传的文件

**响应示例**:
```json
{
  "message": "文件上传成功",
  "filename": "example.jpg",
  "file_path": "uploads/example.jpg",
  "status": "success"
}
```

**错误响应**:
```json
{
  "message": "没有文件被上传",
  "status": "error"
}
```

---

## 使用示例

### JavaScript (使用fetch API)

```javascript
// 获取所有用户
fetch('http://localhost:5000/api/users')
  .then(response => response.json())
  .then(data => console.log(data));

// 创建新用户
fetch('http://localhost:5000/api/user', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: '新用户',
    email: 'newuser@example.com',
    age: 25
  })
})
  .then(response => response.json())
  .then(data => console.log(data));

// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### Python (使用requests库)

```python
import requests

# 获取所有用户
response = requests.get('http://localhost:5000/api/users')
print(response.json())

# 创建新用户
user_data = {
    'name': '新用户',
    'email': 'newuser@example.com',
    'age': 25
}
response = requests.post('http://localhost:5000/api/user', json=user_data)
print(response.json())

# 上传文件
files = {'file': open('example.jpg', 'rb')}
response = requests.post('http://localhost:5000/api/upload', files=files)
print(response.json())
```

---

## 注意事项

1. 所有API接口都支持跨域请求(CORS)
2. 文件上传大小限制为16MB
3. 上传的文件保存在服务器的`uploads`目录下
4. 用户数据目前是模拟数据，重启服务器后会重置
5. 在生产环境中，应该实现数据库持久化和用户认证