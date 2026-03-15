
import os
import time
import hashlib
from flask import Flask
from database import db
from model.user_model import User
from config import config
from playwright.sync_api import sync_playwright

# 1. Initialize Flask App to access DB
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

app = create_app()

def ensure_admin_user():
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("Creating admin user...")
            sha256_hash = hashlib.sha256()
            sha256_hash.update('123456'.encode('utf-8'))
            hashed_password = sha256_hash.hexdigest()
            
            new_user = User(username='admin', password=hashed_password, role=1)
            db.session.add(new_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")

def capture_screenshots():
    ensure_admin_user()
    
    # Ensure directory exists
    os.makedirs('论文/screenshots', exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Run headless
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            # 1. Login Page
            print('Taking login screenshot...')
            page.goto('http://localhost:8080/#/login')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path='论文/screenshots/login.png')

            # 2. Login Action
            print('Logging in...')
            # Update selectors based on typical Element Plus or Vue usage
            # If placeholders are used:
            page.fill('input[placeholder="请输入账号"]', 'admin') 
            page.fill('input[placeholder="请输入密码"]', '123456')
            
            # Click login button
            page.click('button:has-text("登录")') 
            
            # Wait for navigation
            page.wait_for_load_state('networkidle')
            time.sleep(3)
            
            # Check if login successful (url changed or element present)
            if '/login' not in page.url:
                print('Login successful!')
                
                # 3. Dashboard
                print('Taking dashboard screenshot...')
                page.screenshot(path='论文/screenshots/dashboard.png')
                
                # 4. Logs
                print('Taking log list screenshot...')
                page.goto('http://localhost:8080/#/logs')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path='论文/screenshots/log_list.png')
                
                # 5. Malicious IP
                print('Taking malicious ip screenshot...')
                page.goto('http://localhost:8080/#/malicious-ip')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path='论文/screenshots/malicious_ip.png')
                
                # 6. AI Analysis (if available)
                # page.goto('http://localhost:8080/#/analysis')
                # ...
            else:
                print('Login failed or stayed on login page.')
                # Try to take a screenshot of the error
                page.screenshot(path='论文/screenshots/login_failed.png')

        except Exception as e:
            print(f"Error during screenshots: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == '__main__':
    capture_screenshots()
