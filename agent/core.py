# -*- coding: utf-8 -*-
import json
import logging
from typing import Dict, Any, List

from agent.llm_client import LLMClient
from agent.mcp.skill import SkillRegistry
# 确保注册技能
import agent.skills.decoder_skill

logger = logging.getLogger(__name__)

class TrafficAnalysisAgent:
    """
    恶意流量分析 Agent
    基于 MCP (Model Context Protocol) 架构，集成多种 Skill 进行智能分析
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化 Agent
        :param llm_config: LLM 配置信息
        """
        self.llm_client = LLMClient(llm_config)
        self.skills = SkillRegistry.get_all_skills()
        logger.info(f"TrafficAnalysisAgent initialized with skills: {list(self.skills.keys())}")

    def analyze(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析流量日志
        :param log_data: 日志数据字典
        :return: 分析结果
        """
        try:
            # 1. 观察与预处理 (Observation)
            context = self._gather_context(log_data)
            
            # 2. 技能执行 (Tool Execution)
            # 自动检测 payload 并尝试解码
            payload = log_data.get('payload') or log_data.get('raw_log', '')
            decoded_info = self._try_skills(payload)
            
            if decoded_info:
                context['decoded_info'] = decoded_info
                
            # 3. 构建 Prompt (Prompt Engineering)
            prompt = self._build_prompt(log_data, context)
            
            # 4. LLM 推理 (Reasoning)
            response_text = self.llm_client.call_api(prompt)
            
            if not response_text:
                return {
                    "ai_attack_type": "Unknown",
                    "ai_confidence": 0.0,
                    "ai_analysis_result": "AI Agent 调用失败: 无响应"
                }
            
            # 5. 结果解析 (Response Parsing)
            result = self.llm_client.parse_response(response_text)
            
            # 整合解码信息到分析结果中
            analysis_text = result.get("analysis", "无详细分析")
            if decoded_info:
                analysis_text += f"\n[Agent Skill]: 检测到并解码了隐藏载荷: {decoded_info}"
                
            return {
                "ai_attack_type": result.get("attack_type", "Unknown"),
                "ai_confidence": float(result.get("confidence", 0.0)),
                "ai_analysis_result": analysis_text
            }
            
        except Exception as e:
            logger.error(f"Agent 分析过程出错: {str(e)}")
            return {
                "ai_attack_type": "Error",
                "ai_confidence": 0.0,
                "ai_analysis_result": f"Agent 内部错误: {str(e)}"
            }

    def _gather_context(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """收集上下文信息"""
        return {
            "timestamp": log_data.get('timestamp', ''),
            "source_ip": log_data.get('source_ip', ''),
            "target_port": log_data.get('target_port', '')
        }

    def _try_skills(self, payload: str) -> str:
        """尝试使用所有可用技能处理 payload"""
        if not payload:
            return ""
            
        skill_results = []
        
        # 尝试调用解码技能
        decoder = SkillRegistry.get_skill("payload_decoder")
        if decoder:
            result = decoder.execute(payload)
            if result:
                # 格式化输出
                summary = result.get('summary', '')
                details = []
                for item in result.get('detected_encodings', []):
                    details.append(f"- {item['type']}: {item['decoded']}")
                
                skill_results.append(f"{summary}\n" + "\n".join(details))
        
        return "\n".join(skill_results)

    def _build_prompt(self, log_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """构建分析 Prompt"""
        raw_log = log_data.get('raw_log', '')
        protocol = log_data.get('protocol', 'Unknown')
        request_path = log_data.get('request_path', '')
        payload = log_data.get('payload', '')
        decoded_info = context.get('decoded_info', '')
        
        # 基础 Prompt
        prompt = f"""
你是一个网络安全专家 Agent。请分析以下蜜罐捕获的流量日志，判断其是否为恶意攻击。

[日志信息]
- 协议: {protocol}
- 请求路径: {request_path}
- 载荷/内容: {payload if payload else raw_log}
- 原始日志: {raw_log}
"""

        # 如果有解码信息，添加到 Prompt 中
        if decoded_info:
            prompt += f"""
[Agent 技能发现]
Agent 使用解码技能发现了以下隐藏内容:
{decoded_info}
请在分析时重点考虑这些解码后的内容。
"""

        prompt += """
请按照以下JSON格式返回结果，不要包含思考过程或其他废话，只要JSON：
{
    "attack_type": "攻击类型(如: SQL注入, XSS, 暴力破解, 扫描, 正常流量, 未知)",
    "confidence": 0.0-1.0之间的置信度数值,
    "analysis": "简短的分析理由(中文)"
}
"""
        return prompt
