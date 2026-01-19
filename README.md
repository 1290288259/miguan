# Flask标准框架

这是一个基于Python Flask框架的Web应用程序标准模板，提供了完整的项目结构和基础功能，适合快速启动新的Web项目。

## 项目特性

- 🏗️ **标准目录结构** - 遵循Flask最佳实践的目录组织
- ⚙️ **灵活配置** - 支持多环境配置（开发、测试、生产）
- 🛡️ **安全考虑** - 包含基本的安全配置和最佳实践
- 📱 **响应式设计** - 基于Bootstrap 5的现代化UI
- 🔧 **详细注释** - 完整的中文代码注释，便于学习
- 📊 **错误处理** - 自定义的404和500错误页面
- 🚀 **API示例** - 包含RESTful API示例

## 技术栈

- **后端**: Python 3.7+, Flask 2.3+
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5
- **模板引擎**: Jinja2
- **开发工具**: pytest, flake8, black

## 快速开始

### 1. 环境准备

确保已安装Python 3.7或更高版本：

```bash
python --version
```

### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv flask_env

# 激活虚拟环境
# Windows
flask_env\Scripts\activate
# Linux/Mac
source flask_env/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 上运行。

## 项目结构

```
├── app.py              # 应用程序主文件
├── config.py           # 配置文件
├── requirements.txt    # 项目依赖
├── static/             # 静态文件目录
│   ├── css/           # CSS样式文件
│   │   └── style.css  # 自定义样式
│   ├── js/            # JavaScript文件
│   │   └── main.js    # 自定义脚本
│   └── images/        # 图片文件
├── templates/          # 模板文件目录
│   ├── base.html      # 基础模板
│   ├── index.html     # 主页模板
│   ├── about.html     # 关于页面模板
│   ├── 404.html       # 404错误页面
│   └── 500.html       # 500错误页面
└── uploads/            # 文件上传目录
```

## 配置说明

配置文件 `config.py` 包含了不同环境的配置：

- `DevelopmentConfig` - 开发环境配置
- `TestingConfig` - 测试环境配置
- `ProductionConfig` - 生产环境配置

可以通过环境变量 `FLASK_ENV` 来指定使用哪个配置：

```bash
# Windows
set FLASK_ENV=development

# Linux/Mac
export FLASK_ENV=development
```

## 开发指南

### 添加新路由

在 `app.py` 中添加新的路由：

```python
@app.route('/new-page')
def new_page():
    return render_template('new_page.html', title='新页面')
```

### 添加新模板

在 `templates` 目录下创建新的HTML文件，并继承 `base.html`：

```html
{% extends "base.html" %}

{% block content %}
<div class="container">
    <h1>新页面</h1>
    <p>这是新页面的内容</p>
</div>
{% endblock %}
```

### 添加静态文件

将CSS文件放在 `static/css/` 目录下，JavaScript文件放在 `static/js/` 目录下，图片文件放在 `static/images/` 目录下。

在模板中引用静态文件：

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
```

## 部署指南

### 使用Gunicorn部署

1. 安装Gunicorn：

```bash
pip install gunicorn
```

2. 运行应用：

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 使用Docker部署

1. 创建Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

2. 构建并运行容器：

```bash
docker build -t flask-app .
docker run -p 5000:5000 flask-app
```

## 常见问题

### 1. 如何添加数据库支持？

取消 `config.py` 中数据库配置的注释，并安装相应的数据库驱动：

```bash
pip install Flask-SQLAlchemy
```

### 2. 如何添加用户认证？

可以使用Flask-Login扩展：

```bash
pip install Flask-Login
```

### 3. 如何处理表单？

可以使用Flask-WTF扩展：

```bash
pip install Flask-WTF WTForms
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个框架！

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系：developer@example.com