# -*- coding: utf-8 -*-
"""启动Flask服务器的简单启动器（供测试用）"""
from app import app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
