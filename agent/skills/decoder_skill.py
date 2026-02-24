# -*- coding: utf-8 -*-
import base64
import binascii
import urllib.parse
import re
import html
import codecs
from typing import Dict, Any, Optional
from agent.mcp.skill import BaseSkill, SkillRegistry

class DecoderSkill(BaseSkill):
    """
    解码技能
    用于识别和解码常见的编码格式 (Base64, Hex, URL Encoding, Unicode, HTML Entity, Rot13)
    """
    
    @property
    def name(self) -> str:
        return "payload_decoder"
        
    @property
    def description(self) -> str:
        return "识别并解码 Base64, Hex, URL, Unicode, HTML Entity 等常见编码格式的恶意载荷"
    
    def execute(self, input_data: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        尝试解码输入字符串
        :param input_data: 待检测的字符串 (通常是 payload)
        :return: 解码结果字典
        """
        if not input_data or not isinstance(input_data, str):
            return None
            
        results = []
        original_input = input_data
        
        # 1. URL 解码 (多次尝试，处理双重编码)
        try:
            decoded = input_data
            for _ in range(3): # 最多尝试3层解码
                if '%' in decoded:
                    new_decoded = urllib.parse.unquote(decoded)
                    if new_decoded != decoded:
                        decoded = new_decoded
                        if self._is_readable(decoded) and decoded != original_input:
                             # 避免重复添加
                            if not any(r['type'] == "URL Encoding" and r['decoded'] == decoded for r in results):
                                results.append({
                                    "type": "URL Encoding",
                                    "decoded": decoded,
                                    "confidence": 1.0
                                })
                    else:
                        break
                else:
                    break
            #以此为基础继续解码
            if results:
                input_data = results[-1]['decoded']
        except:
            pass
            
        # 2. Unicode 解码 (\u0041, %u0041)
        try:
            # 标准 unicode escape
            if '\\u' in input_data or '%u' in input_data:
                # 处理 %u 格式 (IIS unicode)
                temp_data = input_data.replace('%u', '\\u')
                try:
                    decoded = temp_data.encode('utf-8').decode('unicode_escape')
                    if decoded != input_data and self._is_readable(decoded):
                        results.append({
                            "type": "Unicode Escape",
                            "decoded": decoded,
                            "confidence": 0.95
                        })
                except:
                    pass
        except:
            pass

        # 3. HTML Entity 解码 (&lt;, &#60;)
        try:
            if '&' in input_data and ';' in input_data:
                decoded = html.unescape(input_data)
                if decoded != input_data:
                    results.append({
                        "type": "HTML Entity",
                        "decoded": decoded,
                        "confidence": 0.95
                    })
        except:
            pass

        # 4. Base64 解码
        # 简单的启发式检查: 长度是4的倍数(或接近), 包含字母数字+/=
        # 尝试清理非base64字符（容错模式）
        b64_pattern = re.compile(r'[A-Za-z0-9+/=]{8,}')
        potential_b64s = b64_pattern.findall(input_data)
        
        for b64_str in potential_b64s:
            # 补全 padding
            missing_padding = len(b64_str) % 4
            if missing_padding:
                b64_str += '=' * (4 - missing_padding)
                
            try:
                decoded_bytes = base64.b64decode(b64_str)
                try:
                    decoded_str = decoded_bytes.decode('utf-8')
                    # 排除乱码结果 (简单判断: 是否包含大量不可打印字符)
                    # 且解码后长度不能太短，防止误判
                    if len(decoded_str) > 3 and self._is_readable(decoded_str):
                        # 避免重复
                        if not any(r['decoded'] == decoded_str for r in results):
                            results.append({
                                "type": "Base64",
                                "decoded": decoded_str,
                                "confidence": 0.9
                            })
                except UnicodeDecodeError:
                    pass
            except:
                pass

        # 5. Hex 解码 (如 0x414141, \x41\x41, 41 42 43)
        # 移除常见的 hex 前缀/分隔符
        hex_clean = input_data.replace('0x', '').replace('\\x', '').replace(' ', '').replace('%', '')
        if len(hex_clean) > 4 and len(hex_clean) % 2 == 0:
             if re.match(r'^[0-9a-fA-F]+$', hex_clean):
                try:
                    decoded_bytes = binascii.unhexlify(hex_clean)
                    try:
                        decoded_str = decoded_bytes.decode('utf-8')
                        if len(decoded_str) > 2 and self._is_readable(decoded_str):
                             if not any(r['decoded'] == decoded_str for r in results):
                                results.append({
                                    "type": "Hex",
                                    "decoded": decoded_str,
                                    "confidence": 0.85
                                })
                    except UnicodeDecodeError:
                        pass
                except:
                    pass

        # 6. Rot13 (仅尝试，如果解码后包含常见关键字则保留)
        try:
            # 只有当输入看起来像字母时才尝试
            if any(c.isalpha() for c in input_data):
                decoded = codecs.decode(input_data, 'rot_13')
                # 简单的关键字检查，防止误报
                keywords = ['select', 'union', 'exec', 'script', 'alert', 'document', 'eval', 'system', 'cmd', 'bash', 'sh']
                if any(kw in decoded.lower() for kw in keywords) and decoded != input_data:
                    results.append({
                        "type": "Rot13",
                        "decoded": decoded,
                        "confidence": 0.7
                    })
        except:
            pass
            
        if results:
            # 去重
            unique_results = []
            seen = set()
            for r in results:
                if r['decoded'] not in seen:
                    unique_results.append(r)
                    seen.add(r['decoded'])
            
            return {
                "detected_encodings": unique_results,
                "summary": f"检测到 {len(unique_results)} 种编码格式: {', '.join([r['type'] for r in unique_results])}"
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
