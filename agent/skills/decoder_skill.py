# -*- coding: utf-8 -*-
import base64
import binascii
import urllib.parse
import re
from typing import Dict, Any, Optional
from agent.mcp.skill import BaseSkill, SkillRegistry

class DecoderSkill(BaseSkill):
    """
    解码技能
    用于识别和解码常见的编码格式 (Base64, Hex, URL Encoding)
    """
    
    @property
    def name(self) -> str:
        return "payload_decoder"
        
    @property
    def description(self) -> str:
        return "识别并解码 Base64, Hex, URL 等常见编码格式的恶意载荷"
    
    def execute(self, input_data: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        尝试解码输入字符串
        :param input_data: 待检测的字符串 (通常是 payload)
        :return: 解码结果字典
        """
        if not input_data or not isinstance(input_data, str):
            return None
            
        results = []
        
        # 1. URL 解码
        try:
            if '%' in input_data:
                decoded = urllib.parse.unquote(input_data)
                if decoded != input_data:
                    results.append({
                        "type": "URL Encoding",
                        "decoded": decoded,
                        "confidence": 1.0
                    })
                    # 对URL解码后的内容继续尝试其他解码
                    input_data = decoded
        except:
            pass
            
        # 2. Base64 解码
        # 简单的启发式检查: 长度是4的倍数, 包含字母数字+/=
        if len(input_data) > 8 and len(input_data) % 4 == 0:
            if re.match(r'^[A-Za-z0-9+/=]+$', input_data):
                try:
                    decoded_bytes = base64.b64decode(input_data)
                    # 尝试解码为UTF-8字符串，如果是二进制则忽略或标记
                    try:
                        decoded_str = decoded_bytes.decode('utf-8')
                        # 排除乱码结果 (简单判断: 是否包含大量不可打印字符)
                        if self._is_readable(decoded_str):
                            results.append({
                                "type": "Base64",
                                "decoded": decoded_str,
                                "confidence": 0.9
                            })
                    except UnicodeDecodeError:
                        # 可能是二进制 payload，记录 hex
                        results.append({
                            "type": "Base64 (Binary)",
                            "decoded": f"Hex: {binascii.hexlify(decoded_bytes).decode('utf-8')}",
                            "confidence": 0.9
                        })
                except:
                    pass

        # 3. Hex 解码 (如 0x414141 或 \x41\x41)
        # 移除常见的 hex 前缀/分隔符
        hex_clean = input_data.replace('0x', '').replace('\\x', '').replace(' ', '')
        if len(hex_clean) > 4 and len(hex_clean) % 2 == 0 and re.match(r'^[0-9a-fA-F]+$', hex_clean):
            try:
                decoded_bytes = binascii.unhexlify(hex_clean)
                try:
                    decoded_str = decoded_bytes.decode('utf-8')
                    if self._is_readable(decoded_str):
                        results.append({
                            "type": "Hex",
                            "decoded": decoded_str,
                            "confidence": 0.8
                        })
                except UnicodeDecodeError:
                    pass
            except:
                pass
                
        if results:
            return {
                "detected_encodings": results,
                "summary": f"检测到 {len(results)} 种编码格式: {', '.join([r['type'] for r in results])}"
            }
            
        return None

    def _is_readable(self, text: str) -> bool:
        """判断字符串是否主要由可打印字符组成"""
        if not text:
            return False
        printable_count = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
        return (printable_count / len(text)) > 0.8

# 自动注册
SkillRegistry.register(DecoderSkill())
