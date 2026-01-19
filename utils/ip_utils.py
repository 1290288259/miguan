# -*- coding: utf-8 -*-
"""
IP工具类
提供IP地址相关的工具函数
"""

import requests
import ipaddress
import logging

logger = logging.getLogger(__name__)

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
            return "未知", "Local Network"
    except ValueError:
        # IP格式无效
        return "未知", ""

    # 调用公共API获取地理位置
    # 使用 ip-api.com (免费，限制 45 requests/minute)
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
                
                # 组合地理位置信息
                location_parts = []
                if country:
                    location_parts.append(country)
                if region and region != country: # 避免重复
                    location_parts.append(region)
                if city and city != region:
                    location_parts.append(city)
                    
                location = " ".join(location_parts)
                return (location if location else "未知"), isp
            else:
                logger.warning(f"IP location API returned failure for {ip_address}: {data.get('message')}")
        else:
            logger.warning(f"IP location API failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting IP location for {ip_address}: {str(e)}")
        
    return "未知", ""
