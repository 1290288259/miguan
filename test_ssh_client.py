import paramiko
import time

def test_ssh_login():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Connecting to honeypot...")
    try:
        client.connect('127.0.0.1', port=2222, username='admin', password='password123', timeout=5)
    except paramiko.AuthenticationException:
        print("Authentication failed as expected.")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    test_ssh_login()
