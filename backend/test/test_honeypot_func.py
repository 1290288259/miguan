import requests
import socket
import time
import json

BASE_URL = "http://127.0.0.1:5000/api"
LOGIN_URL = f"{BASE_URL}/user/login"
HONEYPOT_URL = f"{BASE_URL}/honeypots"

def test_honeypot():
    # 1. Login to get token
    print("1. Logging in...")
    try:
        resp = requests.post(LOGIN_URL, json={"username": "administrator", "password": "123456"}) # Assuming default admin
        if resp.status_code != 200:
            # Try registering if login fails (first run)
            print("Login failed, trying to register admin...")
            requests.post(f"{BASE_URL}/user/create_admin", json={"username": "administrator", "password": "123456", "email": "admin@example.com"})
            resp = requests.post(LOGIN_URL, json={"username": "administrator", "password": "123456"})
        
        token = resp.json()['data']['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")
    except Exception as e:
        print(f"Login/Register failed: {e}")
        return

    # 2. Get SSH Honeypot ID
    print("2. Getting SSH Honeypot...")
    resp = requests.get(HONEYPOT_URL, headers=headers)
    honeypots = resp.json()['data']['honeypots']
    ssh_hp = next((hp for hp in honeypots if hp['type'] == 'SSH'), None)
    
    if not ssh_hp:
        print("SSH Honeypot not found!")
        return
    
    hp_id = ssh_hp['id']
    print(f"Found SSH Honeypot ID: {hp_id}")

    # 3. Start Honeypot
    print("3. Starting Honeypot...")
    # Force stop first to ensure clean state (or if it's "running" but dead)
    print("Stopping honeypot first...")
    requests.post(f"{HONEYPOT_URL}/{hp_id}/stop", headers=headers)
    time.sleep(1)
    
    print("Starting honeypot...")
    resp = requests.post(f"{HONEYPOT_URL}/{hp_id}/start", headers=headers)
    print(f"Start response: {resp.json()}")
    time.sleep(2) # Wait for startup

    # 4. Connect to Honeypot
    print("4. Connecting to Honeypot (Port 2222)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 2222))
        banner = s.recv(1024)
        print(f"Received banner: {banner}")
        s.send(b"SSH-2.0-TestClient\r\n")
        s.close()
        print("Connection successful.")
    except Exception as e:
        print(f"Connection failed: {e}")

    # 5. Check Logs
    print("5. Checking Logs...")
    time.sleep(1) # Wait for log upload
    resp = requests.get(f"{BASE_URL}/logs", headers=headers, params={"protocol": "SSH"})
    logs = resp.json()['data']['logs']
    if logs:
        print(f"Found {len(logs)} SSH logs. Latest: {logs[0]['raw_log']}")
    else:
        print("No logs found!")

if __name__ == "__main__":
    test_honeypot()
