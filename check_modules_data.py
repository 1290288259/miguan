from app import create_app
from model.module_model import Module
from database import db

app = create_app()

with app.app_context():
    modules = Module.query.all()
    print(f"当前数据库中的模块数量: {len(modules)}")
    for m in modules:
        print(f"ID: {m.id}, Title: {m.title}, Path: {m.path}")

    if len(modules) == 0:
        print("警告: 数据库中没有模块数据！")
