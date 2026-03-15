# -*- coding: utf-8 -*-
"""
IP工具类
提供IP地址相关的工具函数
"""

import requests
import ipaddress
import logging
import os
import geoip2.database
import shutil
import tempfile
from functools import lru_cache
from utils.download_geoip import download_db, DB_PATH_CITY, DB_PATH_ASN

logger = logging.getLogger(__name__)

# 初始化地理位置和ISP数据库读取器
_city_reader = None
_asn_reader = None

def _get_safe_path(original_path):
    """
    Ensure the path is safe for maxminddb (ASCII only on Windows).
    If not, copy to a temp file.
    """
    try:
        original_path.encode('ascii')
        return original_path
    except UnicodeEncodeError:
        # Path contains non-ASCII characters
        filename = os.path.basename(original_path)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        # Check if temp path is ASCII
        try:
            temp_path.encode('ascii')
        except UnicodeEncodeError:
            # Fallback to a simpler name if temp dir also has non-ASCII (unlikely but possible)
            import hashlib
            hash_name = hashlib.md5(filename.encode('utf-8')).hexdigest() + ".mmdb"
            temp_path = os.path.join(temp_dir, hash_name)

        # Copy if not exists or size differs
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) != os.path.getsize(original_path):
            logger.info(f"Copying GeoIP DB to temp path {temp_path} to avoid encoding issues...")
            shutil.copy2(original_path, temp_path)
            
        return temp_path

def _init_readers():
    global _city_reader, _asn_reader
    if _city_reader is None or _asn_reader is None:
        if not os.path.exists(DB_PATH_CITY) or not os.path.exists(DB_PATH_ASN):
            logger.info("GeoIP databases missing. Starting download...")
            download_db()
        
        try:
            if os.path.exists(DB_PATH_CITY):
                safe_city_path = _get_safe_path(DB_PATH_CITY)
                _city_reader = geoip2.database.Reader(safe_city_path)
            if os.path.exists(DB_PATH_ASN):
                safe_asn_path = _get_safe_path(DB_PATH_ASN)
                _asn_reader = geoip2.database.Reader(safe_asn_path)
        except Exception as e:
            logger.error(f"Failed to load GeoIP database: {e}")

@lru_cache(maxsize=10000)
def get_ip_location(ip_address: str) -> tuple[str, str]:
    """
    获取IP地址的地理位置和ISP信息
    
    参数:
        ip_address: IP地址字符串
        
    返回:
        tuple[str, str]: (地理位置, ISP)，无法识别则返回 ("未知", "")
    """
    if not ip_address:
        return "未知", ""
        
    # 检查是否为私有IP或回环地址
    try:
        ip = ipaddress.ip_address(ip_address)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return "局域网", "Local Network"
    except ValueError:
        # IP格式无效
        return "未知", ""

    # 初始化读取器（仅在第一次调用时执行或文件缺失时重试）
    _init_readers()

    location = "未知"
    isp = ""

    # 1. 尝试从本地 GeoLite2 数据库获取
    if _city_reader:
        try:
            response = _city_reader.city(ip_address)
            # 优先获取中文名称，如果没有则使用英文
            country = response.country.names.get('zh-CN', response.country.name) or ''
            subdivision = response.subdivisions.most_specific.names.get('zh-CN', response.subdivisions.most_specific.name) or ''
            city = response.city.names.get('zh-CN', response.city.name) or ''
            
            location_parts = []
            if country: location_parts.append(country)
            if subdivision and subdivision != country: location_parts.append(subdivision)
            if city and city != subdivision: location_parts.append(city)
            
            if location_parts:
                location = " ".join(location_parts)
        except geoip2.errors.AddressNotFoundError:
            pass
        except Exception as e:
            logger.error(f"GeoIP City DB error for {ip_address}: {e}")

    if _asn_reader:
        try:
            response = _asn_reader.asn(ip_address)
            isp = response.autonomous_system_organization or ''
        except geoip2.errors.AddressNotFoundError:
            pass
        except Exception as e:
            logger.error(f"GeoIP ASN DB error for {ip_address}: {e}")

    # 2. 如果本地库完全没有找到，可选择 Fallback 到 API (可选)
    if location == "未知" and isp == "":
        try:
            url = f"http://ip-api.com/json/{ip_address}?lang=zh-CN"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country', '')
                    region = data.get('regionName', '')
                    city = data.get('city', '')
                    isp = data.get('isp', '')
                    
                    location_parts = []
                    if country: location_parts.append(country)
                    if region and region != country: location_parts.append(region)
                    if city and city != region: location_parts.append(city)
                        
                    if location_parts:
                        location = " ".join(location_parts)
        except Exception as e:
            logger.error(f"Fallback API error for {ip_address}: {e}")

    return location, isp
