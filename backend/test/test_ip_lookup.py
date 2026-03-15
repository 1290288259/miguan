import time
import random
import sys
import os

# 将 src 目录加入 path 以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ip_utils import get_ip_location

def test_ip_lookup():
    test_ips = [
        "8.8.8.8",          # Google DNS
        "1.1.1.1",          # Cloudflare DNS
        "114.114.114.114",  # 114 DNS
        "223.5.5.5",        # AliDNS
        "127.0.0.1",        # Localhost
        "192.168.1.1",      # Private IP
        "invalid_ip",       # Invalid
    ]
    
    print("--- 准确性测试 ---")
    for ip in test_ips:
        start_time = time.time()
        loc, isp = get_ip_location(ip)
        elapsed = (time.time() - start_time) * 1000
        print(f"IP: {ip:<15} | Location: {loc:<25} | ISP: {isp:<30} | 耗时: {elapsed:.2f} ms")

    print("\n--- 性能测试 (1000次随机公网IP查询) ---")
    # 生成随机公网IP进行测试
    random_ips = []
    for _ in range(1000):
        ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        random_ips.append(ip)

    start_time = time.time()
    for ip in random_ips:
        get_ip_location(ip)
    
    total_time = time.time() - start_time
    avg_time = (total_time / 1000) * 1000
    
    print(f"1000 次查询总耗时: {total_time:.4f} 秒")
    print(f"平均每次查询耗时: {avg_time:.4f} 毫秒")
    print(f"预计每秒并发量(QPS): {1000/total_time:.2f} 次/秒")

if __name__ == "__main__":
    test_ip_lookup()