# 项目开发规范 (Project Rules)

你是一个资深的 Python 全栈专家，请在开发本 **基于低交互蜜罐的恶意流量检测和防御系统** 时严格遵循如下规则：

## 一、核心开发原则
- **代码质量**：严格遵循 **SOLID、DRY (Don't Repeat Yourself)、KISS (Keep It Simple, Stupid)** 原则。
- **安全优先**：遵循 **OWASP Top 10** 安全最佳实践（特别是 SQL 注入防护、XSS 防护、敏感数据加密）。
- **架构分层**：严格遵守 **Controller-Service-Model** 分层架构，禁止跨层调用。
- **注释规范**：所有关键逻辑、类、方法必须包含 **中文注释** 和 **Docstrings**。
- **类型安全**：Python 代码必须使用 Type Hints (`typing`)，前端使用 TypeScript。

---

## 二、技术栈规范
### 1. 后端 (Backend)
- **语言**：Python 3.8+
- **Web 框架**：Flask
- **ORM**：SQLAlchemy
- **数据库**：MySQL
- **AI 模型**：Ollama (DeepSeek-R1) / OpenAI (远程调用) (也可通过 API 方式接入 OpenAI 等主流模型)
- **依赖管理**：`requirements.txt` + `venv`

### 2. 前端 (Frontend)
- **框架**：Vue 3 (Composition API)
- **语言**：TypeScript
- **构建工具**：Vite
- **UI 组件库**：Element Plus
- **HTTP 客户端**：Axios

---

## 三、后端架构设计规范
### 1. 分层职责
| 层级 | 目录 | 职责 | 约束条件 |
| :--- | :--- | :--- | :--- |
| **Route (Controller)** | `src/route/` | 处理 HTTP 请求/响应，参数解析，权限校验 | - **禁止**包含复杂业务逻辑<br>- 仅调用 Service 层<br>- 返回统一的 JSON 格式 |
| **Service** | `src/service/` | 核心业务逻辑，事务管理，第三方服务调用 | - **禁止**直接操作 SQL（需通过 Model/ORM）<br>- 处理异常并返回明确结果 |
| **Model** | `src/model/` | 数据库模型定义，基础数据操作 | - 继承 `db.Model`<br>- 定义表结构、关系及基础 CRUD 方法 |
| **Utils** | `src/utils/` | 通用工具函数 | - 无状态，纯函数为主 |

### 2. 代码示例规范

#### (1) Model 层 (`src/model/user_model.py`)
```python
from database import db
from datetime import datetime

class User(db.Model):
    """
    用户模型类
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    # 密码必须存储哈希值，禁止明文
    password_hash = db.Column(db.String(128), nullable=False, comment='密码哈希')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
```

#### (2) Service 层 (`src/service/user_service.py`)
```python
from model.user_model import User
from database import db
from typing import Dict, Optional

class UserService:
    """
    用户服务类：处理用户注册、登录等逻辑
    """
    
    @staticmethod
    def create_user(username: str, password_plain: str) -> Dict:
        """
        创建新用户
        
        Args:
            username (str): 用户名
            password_plain (str): 明文密码
            
        Returns:
            Dict: 操作结果
        """
        # 1. 校验是否存在
        if User.query.filter_by(username=username).first():
            return {'success': False, 'message': '用户已存在'}
            
        # 2. 密码加密 (示例，实际应使用加盐哈希)
        # password_hash = generate_password_hash(password_plain) 
        
        # 3. 入库
        new_user = User(username=username, password_hash='hashed_value')
        try:
            db.session.add(new_user)
            db.session.commit()
            return {'success': True, 'message': '注册成功', 'data': new_user.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
```

#### (3) Route 层 (`src/route/user_route.py`)
```python
from flask import Blueprint, request, jsonify
from service.user_service import UserService

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400
        
    result = UserService.create_user(username, password)
    
    if result['success']:
        return jsonify({'code': 200, 'msg': '成功', 'data': result['data']})
    else:
        return jsonify({'code': 500, 'msg': result['message']}), 500
```

---

## 四、前端开发规范
### 1. 组件风格
- 使用 **Vue 3 Composition API** (`<script setup lang="ts">`)。
- 严格遵循 **ESLint** 和 **Prettier** 格式化规则。

### 2. 代码示例 (`src/views/Login.vue`)
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const username = ref('')
const password = ref('')
const userStore = useUserStore()

const handleLogin = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  try {
    await userStore.login(username.value, password.value)
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error('登录失败: ' + error.message)
  }
}
</script>

<template>
  <div class="login-container">
    <el-input v-model="username" placeholder="用户名" />
    <el-input v-model="password" type="password" placeholder="密码" />
    <el-button type="primary" @click="handleLogin">登录</el-button>
  </div>
</template>
```

---

## 五、通用规范
1. **异常处理**：后端必须捕获所有未处理异常，防止服务崩溃，并记录错误日志。
2. **日志记录**：关键操作（登录、攻击检测、封禁）必须写入日志文件或数据库。
3. **环境配置**：敏感信息（数据库密码、API Key）禁止硬编码，需使用环境变量或配置文件。
4. **Git 提交**：Commit Message 需清晰描述变更内容（如 `feat: 添加恶意IP自动封禁功能`）。

## 六、特殊业务规则
1. **蜜罐管理**：蜜罐进程需独立管理，确保主服务崩溃不影响蜜罐运行。
2. **AI 分析**：大模型调用需使用异步队列（如 Queue + Threading），避免阻塞 HTTP 请求。
3. **IP 封禁**：调用底层防火墙命令（iptables/netsh）时需进行操作系统判断和权限校验。

## 七、现有模块与系统架构
当前的后端服务架构已分为以下主要模块：

### 1. 核心业务 API 模块 (Routes / Services / Models)
- **User (用户权限)**：处理用户登录、认证与权限校验 (`user_route`, `user_service`, `user_model`, `user_info_model`, `permission_model`, `module_model`)
- **Dashboard (数据大屏)**：展示实时攻击概览及统计数据 (`dashboard_route`, `dashboard_service`, `attack_stats_model`)
- **Honeypot (蜜罐后台)**：管理蜜罐部署状态及节点信息 (`honeypot_route`, `honeypot_service`, `honeypot_model`)
- **Log (日志审计)**：系统交互日志与攻击日志记录 (`log_route`, `log_service`, `log_model`)
- **Malicious IP (恶意拦截)**：记录攻击源与下发封禁指令 (`malicious_ip_route`, `malicious_ip_service`, `malicious_ip_model`, `block_history_model`)
- **Match Rule (规则引擎)**：管理预期的流量与攻击匹配特征 (`match_rule_route`, `match_rule_service`, `match_rule_model`)
- **AI Config (大模型配置)**：LLM 接口的参数化配置与状态调用 (`ai_config_route`, `ai_config_service`, `ai_config_model`)

### 2. 蜜罐组件实现 (`src/backend/honeypots/`)
- `ftp_server.py`: 低交互 FTP 模拟器，主要针对爆破和未授权访问。
- `ssh_server.py`: 低交互 SSH 模拟器，捕获登录尝试与恶意命令。
- `hikvision_http_server.py`: 模拟海康威视等 IoT 设备的 Web 服务漏洞环境。

### 3. Agent 与智能响应模块 (`src/backend/agent/`)
- **Core Agent**: AI 代理调度核心。
- **Skills**: 下游执行功能组件 (如 `block_ip_skill`, `decoder_skill`, `log_query_skill`)。


## 八、代码重载
后端代码修改之后必须重新启动后端进程