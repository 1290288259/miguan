import socket
import paramiko
import ftplib
import pymysql
import time

def test_ssh(port=2222):
    print(f"[*] 测试 SSH 蜜罐 (端口 {port})...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('127.0.0.1', port=port, username='root', password='password123', timeout=5)
    except Exception as e:
        print(f"[+] SSH 尝试登录结果: {e}")
    finally:
        client.close()

def test_ftp(port=2121):
    print(f"[*] 测试 FTP 蜜罐 (端口 {port})...")
    try:
        ftp = ftplib.FTP()
        ftp.connect('127.0.0.1', port, timeout=5)
        ftp.login(user='admin', passwd='adminpassword')
        ftp.quit()
    except Exception as e:
        print(f"[+] FTP 尝试登录结果: {e}")

def test_mysql(port=3307):
    print(f"[*] 测试 MySQL 蜜罐 (端口 {port})...")
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            port=port,
            user='root',
            password='rootpassword',
            connect_timeout=5
        )
        connection.close()
    except Exception as e:
        print(f"[+] MySQL 尝试登录结果: {e}")

def test_redis(port=6379):
    print(f"[*] 测试 Redis 蜜罐 (端口 {port})...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', port))
        s.sendall(b"AUTH redispassword\r\n")
        response = s.recv(1024)
        print(f"[+] Redis 尝试登录结果: {response.decode('utf-8', errors='ignore').strip()}")
        s.close()
    except Exception as e:
        print(f"[+] Redis 尝试登录结果: {e}")

if __name__ == '__main__':
    print("开始测试各蜜罐的登录尝试...")
    test_ssh()
    test_ftp() 
    test_mysql()
    test_redis()
        
    print("测试完毕。请在后端日志查看结果。")
