# 第一个规范 （必须遵守）
  当每次大的修改和功能的新增，如果与CLAUDE.md文件内容不一致了，需要把新增的功能或者修改功能的逻辑重新写入CLAUDE.md，确保CLAUDE.md文件为最新的。
  
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

| 业务模块 | Route 文件 | Service 文件 | Model 文件 | 职责说明 |
| :--- | :--- | :--- | :--- | :--- |
| **User (用户权限)** | `user_route.py` | `user_service.py` | `user_model.py`, `user_info_model.py`, `permission_model.py`, `module_model.py` | 注册、登录、JWT鉴权、用户管理、模块权限分配 |
| **Dashboard (数据大屏)** | `dashboard_route.py` | `dashboard_service.py` | `attack_stats_model.py` | 攻击趋势、类型分布、地图热力、总览统计（均需JWT） |
| **Honeypot (蜜罐管理)** | `honeypot_route.py` | `honeypot_service.py` | `honeypot_model.py` | 蜜罐CRUD、进程启停、健康检查、PID持久化 |
| **Log (日志审计)** | `log_route.py` | `log_service.py` | `log_model.py` | 日志查询、分页、导出CSV、内部上报（蜜罐使用） |
| **Malicious IP (恶意拦截)** | `malicious_ip_route.py` | `malicious_ip_service.py` | `malicious_ip_model.py`, `block_history_model.py` | 恶意IP列表、封禁/解封、防火墙命令下发 |
| **Match Rule (规则引擎)** | `match_rule_route.py` | `match_rule_service.py` | `match_rule_model.py` | 正则匹配规则管理、启停切换、自动封禁配置 |
| **AI Config (大模型配置)** | `ai_config_route.py` | `ai_config_service.py`, `ai_analysis_service.py` | `ai_config_model.py` | LLM参数化配置、激活/禁用、连通性测试 |
| **Test (测试接口)** | `test_route.py` | `test_service.py` | — | 内部功能测试，非生产接口 |

### 2. 完整 API 端点清单

#### /api/user — 用户管理
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| POST | `/api/user/register` | 无 | 用户注册 |
| POST | `/api/user/login` | 无 | 用户登录，返回 JWT |
| POST | `/api/user/create_admin` | 无 | 创建管理员（初始化用） |
| GET | `/api/user/me` | JWT | 获取当前用户信息 |
| PUT | `/api/user/me` | JWT | 更新当前用户信息（手机/邮箱/密码） |
| GET | `/api/user/list` | JWT + 管理员 | 分页获取用户列表 |
| POST | `/api/user/add` | JWT + 管理员 | 管理员新增用户 |
| PUT | `/api/user/<user_id>` | JWT + 管理员 | 管理员修改用户 |
| DELETE | `/api/user/<user_id>` | JWT + 管理员 | 管理员删除用户 |
| GET | `/api/user/permissions` | JWT + 管理员 | 获取所有权限列表 |
| GET | `/api/user/modules` | JWT | 获取所有模块列表 |

#### /api/dashboard — 数据大屏
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| GET | `/api/dashboard/trend` | JWT | 攻击趋势（支持 days/granularity 参数） |
| GET | `/api/dashboard/types` | JWT | 攻击类型统计分布 |
| GET | `/api/dashboard/map` | JWT | 攻击来源地图数据 |
| GET | `/api/dashboard/summary` | JWT | 总览统计（总攻击数、封禁数等） |

#### /api/honeypots — 蜜罐管理
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| GET | `/api/honeypots` | JWT | 分页查询蜜罐列表（支持 type/status/keyword） |
| POST | `/api/honeypots` | JWT | 创建新蜜罐 |
| PUT | `/api/honeypots/<hp_id>` | JWT | 更新蜜罐配置 |
| DELETE | `/api/honeypots/<hp_id>` | JWT | 删除蜜罐 |
| POST | `/api/honeypots/<hp_id>/start` | JWT | 启动蜜罐进程 |
| POST | `/api/honeypots/<hp_id>/stop` | JWT | 停止蜜罐进程 |
| GET | `/api/honeypots/<hp_id>/health` | JWT | 蜜罐健康检查 |

#### /api/logs — 日志审计
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| GET | `/api/logs` | JWT | 分页查询日志（支持多字段过滤） |
| GET | `/api/logs/export` | JWT | 导出日志为 CSV（含 BOM，支持 Excel） |
| GET | `/api/logs/<log_id>` | JWT | 根据 ID 获取单条日志 |
| GET | `/api/logs/attack-types` | JWT | 获取所有攻击类型枚举 |
| GET | `/api/logs/threat-levels` | JWT | 获取所有威胁等级枚举 |
| GET | `/api/logs/statistics` | JWT | 获取日志统计汇总 |
| POST | `/api/logs/internal/upload` | 无 | **内部接口**：蜜罐进程上报攻击日志 |

#### /api/malicious-ips — 恶意IP管理
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| GET | `/api/malicious-ips` | JWT | 分页查询恶意IP（支持 is_blocked/threat_level/keyword） |
| POST | `/api/malicious-ips/block` | JWT | 封禁指定IP（支持时长/截止时间） |
| POST | `/api/malicious-ips/unblock` | JWT | 解封指定IP |

#### /api/match-rules — 匹配规则引擎
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| GET | `/api/match-rules` | JWT | 分页查询规则 |
| GET | `/api/match-rules/<rule_id>` | JWT | 获取单条规则 |
| POST | `/api/match-rules` | JWT | 创建规则（正则+威胁等级+自动封禁配置） |
| PUT | `/api/match-rules/<rule_id>` | JWT | 更新规则 |
| DELETE | `/api/match-rules/<rule_id>` | JWT | 删除规则 |
| PUT | `/api/match-rules/<rule_id>/toggle` | JWT | 切换规则启用状态 |
| GET | `/api/match-rules/attack-types` | JWT | 获取攻击类型枚举 |
| GET | `/api/match-rules/threat-levels` | JWT | 获取威胁等级枚举 |

#### /api/ai-config — AI大模型配置
| 方法 | 路径 | 认证 | 说明 |
| :--- | :--- | :--- | :--- |
| GET | `/api/ai-config/` | JWT | 获取所有AI配置 |
| POST | `/api/ai-config/` | JWT | 创建AI配置（name/api_url/model_name必填） |
| PUT | `/api/ai-config/<config_id>` | JWT | 更新AI配置 |
| DELETE | `/api/ai-config/<config_id>` | JWT | 删除AI配置 |
| POST | `/api/ai-config/<config_id>/activate` | JWT | 激活配置（设为当前使用） |
| POST | `/api/ai-config/<config_id>/deactivate` | JWT | 禁用配置 |
| POST | `/api/ai-config/<config_id>/test` | JWT | 测试AI配置连通性 |

### 3. 数据库模型清单

共 12 个 Model 文件，对应以下数据库表：

| 模型文件 | 表名 | 说明 |
| :--- | :--- | :--- |
| `user_model.py` | `users` | 用户账号、密码哈希、角色（1管理员/2普通用户） |
| `user_info_model.py` | `user_infos` | 用户扩展信息（手机号、邮箱、头像等） |
| `permission_model.py` | `permissions` | 系统权限定义 |
| `module_model.py` | `modules` / `user_modules` | 系统模块定义及用户-模块关联 |
| `honeypot_model.py` | `honeypots` | 蜜罐配置（类型、端口、状态、`pid` 字段用于持久化进程） |
| `log_model.py` | `logs` | 攻击日志记录（来源IP、载荷、威胁等级、协议等） |
| `malicious_ip_model.py` | `malicious_ips` | 恶意IP列表（封禁状态、威胁等级、攻击次数） |
| `block_history_model.py` | `block_history` | 封禁/解封操作历史记录 |
| `attack_stats_model.py` | `attack_stats` | 攻击统计聚合数据（供 Dashboard 使用） |
| `match_rule_model.py` | `match_rules` | 流量匹配规则（正则表达式、自动封禁、优先级） |
| `ai_config_model.py` | `ai_configs` | AI大模型配置（API地址、模型名称、激活状态） |

> **重要**：`honeypot_model.py` 中包含 `pid` 字段（Integer, nullable），用于在服务重启后通过 `psutil` 检查蜜罐子进程是否仍然存活。

### 4. 蜜罐组件实现 (`backend/honeypots/`)

| 文件 | 协议 | 默认端口 | 捕获目标 |
| :--- | :--- | :--- | :--- |
| `ftp_server.py` | FTP | 2121 | 爆破攻击、未授权访问、文件上传尝试 |
| `ssh_server.py` | SSH | 2222 | 登录爆破、恶意命令执行（基于 Paramiko） |
| `hikvision_http_server.py` | HTTP | 可配置（读取 `sys.argv[1]`） | IoT/摄像头设备漏洞探测、Web 攻击 |
| `redis_server.py` | TCP/Redis | 6379 | Redis 未授权访问、SLAVEOF/CONFIG 命令利用 |
| `mysql_server.py` | TCP/MySQL | 3306 | 数据库弱口令爆破（捕获用户名、客户端版本） |

**蜜罐进程管理机制**：
- 所有蜜罐以**独立子进程**方式启动（`subprocess.Popen`），与主 Flask 服务解耦。
- 启动时将 PID 写入 `honeypots.pid` 数据库字段；停止时发送 `SIGTERM`/`taskkill`。
- 服务重启后调用 `psutil.pid_exists()` 检查进程存活状态，自动修正数据库状态。
- 蜜罐捕获到攻击后，通过 HTTP 调用 `/api/logs/internal/upload` 上报主服务。

### 5. Agent 与智能响应模块 (`backend/agent/`)

```
agent/
├── core.py          # AI代理调度核心，支持多模型工作池、Queue+Threading异步队列
├── llm_client.py    # LLM客户端，封装 OpenAI 兼容 API 调用
├── mcp/
│   └── skill.py     # MCP技能协议基类
└── skills/
    ├── block_ip_skill.py    # 自动封禁技能：先记录 malicious_ip 再调用防火墙封禁
    ├── decoder_skill.py     # Base64/URL解码技能，辅助攻击载荷分析
    └── log_query_skill.py   # 日志查询技能，供 AI Agent 检索历史攻击日志
```

**关键设计**：AI 分析通过 `Queue + Threading` 异步执行，不阻塞 HTTP 请求线程。

### 6. 工具模块 (`backend/utils/`)

| 文件 | 说明 |
| :--- | :--- |
| `api_response.py` | 统一 API 响应格式工具（`ApiResponse.success/error/bad_request` 等） |
| `ip_utils.py` | **离线** IP 地理位置解析（MaxMind GeoLite2 MMDB），含 LRU 缓存 10000 条、私有 IP 判断 |
| `time_utils.py` | 时间格式化工具函数 |
| `download_geoip.py` | 自动下载/更新 GeoLite2 数据库脚本 |
| `data/GeoLite2-City.mmdb` | 离线城市/国家地理数据库 |
| `data/GeoLite2-ASN.mmdb` | 离线 ASN 自治系统数据库 |

> **注意**：IP 溯源已从在线 `ip-api.com` 全面迁移至离线 MaxMind GeoLite2，无需外网访问。

### 7. 前端视图清单 (`vueweb/vue-project/src/views/`)

| 文件路径 | 功能说明 |
| :--- | :--- |
| `Dashboard.vue` | 仪表盘入口（路由容器） |
| `dashboard/DashboardLayout.vue` | 数据大屏布局（导航 + 内容区） |
| `dashboard/Overview.vue` | 攻击总览（总数、封禁数、实时告警） |
| `dashboard/Trend.vue` | 攻击趋势折线图（按天/小时粒度） |
| `dashboard/Types.vue` | 攻击类型饼图/柱状图分布 |
| `dashboard/Map.vue` | 世界地图攻击来源热力图（ECharts） |
| `HoneypotManagement.vue` | 蜜罐管理（CRUD、启停控制、健康状态监控） |
| `LogQuery.vue` | 日志查询（多维度过滤、详情展示、CSV导出） |
| `MaliciousIPManagement.vue` | 恶意IP管理（封禁/解封、威胁等级筛选） |
| `MatchRuleManagement.vue` | 匹配规则管理（正则规则CRUD、启停切换） |
| `AIConfigManagement.vue` | AI配置管理（多模型配置、激活/禁用、连通测试） |
| `UserManagement.vue` | 用户管理（管理员）：列表、增删改、模块权限分配 |
| `UserProfile.vue` | 个人中心：查看/修改自己的手机、邮箱、密码 |

**前端特性**：
- 支持**暗黑/明亮**主题切换（持久化到 localStorage）。
- 路由守卫：token 存在但 `user` 为空时，先 `await fetchCurrentUser()` 再放行，防止权限检查时序问题。
- 所有 HTTP 请求通过 Axios 统一拦截器附加 `Authorization: Bearer <token>`。

### 8. 后端初始化脚本

| 文件 | 用途 |
| :--- | :--- |
| `init_database.py` | 创建所有数据库表（`db.create_all()`） |
| `init_data.py` | 初始化基础数据（角色、权限） |
| `init_modules.py` | 初始化系统功能模块数据 |
| `init_permissions.py` | 初始化权限条目 |
| `init_honeypot.py` | 初始化默认蜜罐配置 |
| `config.py` | Flask 配置类（数据库URI、JWT密钥、CORS等） |
| `extensions.py` | Flask 扩展实例集中管理（SocketIO 全局单例），避免 reloader 实例不一致 |
| `app.py` | Flask 应用入口，注册所有蓝图，初始化 SocketIO 并注册 /ws namespace |

### 9. 数据库迁移

使用 Flask-Migrate（Alembic），迁移文件位于 `backend/migrations/versions/`。

**已有迁移**：
- `f1a2b3c4d5e6_add_pid_to_honeypots.py` — 为 `honeypots` 表新增 `pid` 字段，支持进程持久化重启检测。

---

## 八、WebSocket 实时推送架构

### 1. 技术选型
| 层 | 技术 | 版本 |
| :--- | :--- | :--- |
| 后端 | Flask-SocketIO | 5.3.6 |
| 后端传输 | python-socketio + python-engineio | 5.10.0 / 4.8.2 |
| 前端 | socket.io-client | 4.7.5 |

### 2. 架构流程

```
蜜罐捕获攻击
    ↓ HTTP POST /api/logs/internal/upload
log_service.py · create_log()
    ├─ 规则匹配 (MatchRule)
    ├─ 写入 MySQL (Log)
    ├─ AI 分析任务入队
    ├─ 记录恶意 IP
    └─ [仅恶意流量] socketio.emit('new_attack', payload, namespace='/ws')
                            ↓ WebSocket
                    前端 useSocket composable
                            ↓
              ┌─────────────┼─────────────┐
    DashboardLayout.vue  Overview.vue   Map.vue
    (ElNotification弹窗  (数字跳动+     (地图红色
     + 高危横幅)          实时告警列表)   脉冲散点)
```

### 3. 关键文件

| 文件 | 职责 |
| :--- | :--- |
| `backend/extensions.py` | **全局唯一** `socketio = SocketIO()` 实例，所有模块必须从此处导入 socketio，避免 werkzeug reloader 导致实例不一致 |
| `backend/app.py` | `from extensions import socketio`，调用 `socketio.init_app(app, ...)`，注册 `/ws` namespace 的 connect/disconnect handler，使用 `socketio.run()` 替代 `app.run()` |
| `backend/service/log_service.py` | `create_log()` 末尾 `from extensions import socketio`，emit `new_attack` 事件到 `/ws` namespace |
| `frontend/src/composables/useSocket.ts` | 全局 Socket 单例管理，`connectSocket()`/`disconnectSocket()` 由 DashboardLayout 统一管理生命周期，提供 `onAttack/offAttack` 订阅方法，pending 队列 + 重连恢复（先 `off('new_attack')` 再统一重绑，避免 handler 重复注册） |
| `frontend/src/views/dashboard/DashboardLayout.vue` | 订阅 `new_attack`，显示 `ElNotification` 弹窗 + 高危横幅（含滑入动画），菜单栏显示连接状态指示灯（绿/红），使用 `<keep-alive>` 缓存子路由 |
| `frontend/src/views/dashboard/Overview.vue` | 订阅 `new_attack`，数字递增 + bounce 跳动动画 + 实时告警列表（最多 10 条，transition-group 滑入动画） |
| `frontend/src/views/dashboard/Map.vue` | 订阅 `new_attack`，追加 `effectScatter` 脉冲散点到地图（使用 `Map` 结构消除竞态），5 秒后自动消失，过滤 `(0,0)` null-island 坐标 |

> **重要**：`socketio` 实例必须从 `extensions.py` 导入，**禁止**从 `app.py` 导入。原因：werkzeug 的 `use_reloader=True` 会在子进程中重新执行 `app.py`，导致 `app.py` 中定义的 `socketio` 和其他模块缓存导入的 `socketio` 不是同一个对象。`extensions.py` 作为独立模块不受 reloader 影响。

### 4. 推送事件规范

**事件名**：`new_attack`  
**Namespace**：`/ws`  
**触发条件**：`is_malicious == True`（低危/正常流量不推送，减少噪声）

**载荷字段**：
```json
{
  "log_id": 123,
  "source_ip": "1.2.3.4",
  "attack_type": "SQL注入",
  "threat_level": "high",
  "protocol": "HTTP",
  "target_port": 80,
  "attack_time": "2026-03-27T10:30:00",
  "attack_description": "触发规则: SQL注入检测",
  "longitude": 116.4074,
  "latitude": 39.9042
}
```

### 5. 后端重启说明

WebSocket 需要使用 `socketio.run()` 替代 `app.run()`，已在 `app.py` 中完成更新。
重启后端后 WebSocket 功能即生效，无需额外操作。

### 6. WebSocket 测试脚本

| 文件 | 用途 |
| :--- | :--- |
| `backend/test/test_realtime_report.py` | 主测试脚本：30 次/60 秒全球 IP 的 SQL 注入攻击，用于验证大屏 4 个核心动态效果 |
| `backend/test/verify_websocket.py` | WebSocket 推送端到端验证：Python socketio 客户端连接 `/ws`，发 3 条攻击，验证 4 项指标（事件到达、坐标、攻击类型、威胁等级） |

---

## 九、代码重载
后端代码修改之后必须重新启动后端进程

---

## 十、多级恶意流量识别引擎

### 1. 架构概述

蜜罐捕获的原始流量经过**三级识别漏斗**，逐级过滤和分类：

```
蜜罐原始数据 → 第一级：正则规则匹配 → 第二级：暴力破解频次分析 → 第三级：AI深度分析
```

### 2. 蜜罐端设计原则（纯数据采集探针）

蜜罐脚本**只负责捕获原始数据**，不做任何攻击分类。上报字段：
- `attacker_ip` / `attacker_port` — 攻击来源
- `honeypot_port` — 蜜罐端口
- `protocol` — 协议类型 (SSH/FTP/HTTP/TCP 等)
- `raw_log` — 原始请求/命令完整记录
- `payload` — 载荷内容（认证类蜜罐统一格式：`"Username: xxx, Password: xxx"`）
- `request_path` / `user_agent` — HTTP 蜜罐专用字段

**禁止**在蜜罐脚本中包含 `attack_type`、`threat_level`、`attack_description` 等分类逻辑。

### 3. 三级识别流水线（`log_service.py` · `create_log()`）

#### 第一级：正则规则引擎匹配
- 从 `match_rules` 表读取所有 `is_enabled=True` 的规则，按 `priority ASC` 排序（数字越小优先级越高）
- 匹配字段由规则的 `match_field` 决定（目前全部为 `raw_log`）
- 命中规则后立即设置 `attack_type`、`threat_level`、`attack_description`、`is_malicious`
- **首条命中即停止**，不会继续匹配后续规则

#### 第二级：暴力破解频次分析
- **触发条件**：第一级未命中任何规则（`attack_type` 仍为 `'正常流量'`）
- **检测方法**：`_check_brute_force(source_ip, protocol, current_payload)`
  - 查询同一 IP + 同一协议在最近 **1 分钟** 内的日志数量
  - HTTP 协议特殊处理：只有包含认证凭证（`Username:...Password:...`）的请求才计入暴力破解计数
  - 阈值：**20 次/分钟** (`BRUTE_FORCE_THRESHOLD = 20`)
- **凭证检测**：`_is_credential_payload(payload)` 使用正则 `r'Username:\s*.+,\s*Password:\s*.+'` 判断
- 命中后设置 `attack_type='暴力破解'`、`threat_level='high'`、`is_malicious=True`

#### 第三级：AI 深度分析
- **触发条件**：所有日志均入 AI 分析队列（`Queue + Threading` 异步执行）
- **AI 辅助判断机制**（i_analysis_service.py · _process_single_log()）：
  - AI 仅独立提取和存入自己的分析结果字段（如 i_attack_type、i_confidence、i_analysis_result）。
  - **不修改、不覆写** 前置规则匹配引擎和暴力破解识别引擎的主判断结论（如 ttack_type、is_malicious、	hreat_level 和 ttack_description）。
  - AI 判定后，将 AI 判断结论与主记录判断进行比较，记录在 i_rule_match_consistency 字段（一致 / 不一致），用作辅助审计依据。

### 4. 匹配规则优先级说明

规则按 `priority ASC` 排序匹配，关键优先级分布：

| 优先级范围 | 规则类型 | 说明 |
| :--- | :--- | :--- |
| 1-3 | XSS、SQL注入(基础)、目录遍历 | 高频攻击，精确正则 |
| 5 | Redis未授权访问 | 协议专用规则 |
| 6-9 | WebShell、RCE、扫描探测 | 中等精度规则 |
| 11-15 | SQL注入(盲注)、XXE、信息泄露 | 长正则、较复杂模式 |
| 18 | 命令注入(宽泛匹配) | 匹配 `;` `|` `(` 等字符，优先级故意调低，避免误判 |
| 20-50 | XSS/目录遍历/信息泄露/扫描探测(补充) | 低优先级兜底规则 |

> **重要**：命令注入规则 (ID=8) 的正则包含 `(;|\||&|\$|\(|\)|...)` 极其宽泛，priority 已从 5 调整为 18，防止将 `sleep()`、`eval()`、Nmap UA 等载荷误判为命令注入。

### 5. 自动化测试

测试脚本：`backend/test_traffic_identification.py`

- **51 个断言**，覆盖 22 个测试场景
- 4 个正常流量测试（SSH/FTP/HTTP/ES）
- 11 个正则规则匹配测试（SQL注入×2、XSS×2、命令注入、目录遍历、信息泄露、Redis×2、WebShell、扫描探测）
- 5 个暴力破解测试（SSH低频/高频、HTTP纯GET不触发、HTTP凭证爆破、FTP爆破、MySQL爆破）
- 2 个混合场景测试

运行方式：
```bash
# 确保 Flask 后端运行在 5000 端口
cd backend
python run_server.py &    # 或 python app.py
python test_traffic_identification.py
```

测试脚本在 SETUP 阶段会自动：
- 创建/复用测试账户 `testadmin01`
- 动态发现蜜罐端口
- 确保 Redis 匹配规则存在
- 将命令注入规则优先级调至 18