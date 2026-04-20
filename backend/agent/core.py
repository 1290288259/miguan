# -*- coding: utf-8 -*-
import json
import logging
from typing import Dict, Any, List

from agent.llm_client import LLMClient
from agent.mcp.skill import SkillRegistry
# 确保注册技能
import agent.skills.decoder_skill
import agent.skills.block_ip_skill

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
        # 手动注册新技能 (或者依赖模块导入时的自动注册，如果有实现的话)
        # 这里显式实例化并注册，确保可用
        SkillRegistry.register(agent.skills.decoder_skill.DecoderSkill())
        SkillRegistry.register(agent.skills.block_ip_skill.BlockIPSkill())
        
        self.skills = SkillRegistry.get_all_skills()
        self.is_auto_block = llm_config.get('is_auto_block', False)
        logger.info(f"TrafficAnalysisAgent initialized with skills: {list(self.skills.keys())}, auto_block: {self.is_auto_block}")

    def analyze(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析流量日志
        :param log_data: 日志数据字典
        :return: 分析结果
        """
        try:
            # 1. 观察与预处理 (Observation)
            context = self._gather_context(log_data)
            source_ip = log_data.get('source_ip')
            
            # 2. 技能执行 (Tool Execution) - 预处理阶段
            
            # A. 自动检测 payload 并尝试解码
            payload = log_data.get('payload') or log_data.get('raw_log', '')
            decoded_info = self._try_skills(payload)
            if decoded_info:
                context['decoded_info'] = decoded_info
            
            # B. 查询该 IP 的历史行为 (已移除 LogQuerySkill，仅依赖单条日志)
            # 这里的代码块已删除，不再获取历史信息

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
                
            # 6. 自动响应 (Action) - 封禁恶意 IP
            # 如果 AI 判定为高置信度恶意攻击，且建议封禁，则自动封禁
            attack_type = result.get("attack_type", "Unknown")
            confidence = float(result.get("confidence", 0.0))
            is_malicious = attack_type not in ["Normal", "Unknown", "正常流量", "Page Visit", "正常"]
            
            if self.is_auto_block and is_malicious and confidence > 0.8:
                # 调用封禁技能
                block_skill = self.skills.get('block_ip')
                if block_skill and source_ip:
                    # 默认封禁 24 小时
                    block_result = block_skill.execute({
                        "ip_address": source_ip,
                        "reason": f"AI自动封禁: {attack_type} (置信度 {confidence})",
                        "duration": 24 * 3600
                    })
                    
                    if block_result and block_result.get('success'):
                        analysis_text += f"\n[Agent Action]: 已自动封禁恶意IP {source_ip} (24小时)"
                    else:
                        analysis_text += f"\n[Agent Action]: 尝试封禁IP失败: {block_result.get('message')}"

            return {
                "ai_attack_type": attack_type,
                "ai_confidence": confidence,
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
        ip_history_info = context.get('ip_history', None)
        
        # 基础 Prompt
        prompt = f"""
你是一个网络安全专家 Agent。请分析以下蜜罐捕获的流量日志，判断其是否为恶意攻击。

重要判断规则：
1. 【正常访问】：如果是标准的 HTTP GET 请求，访问主页(/)、登录页(/login)、注册页(/register)、静态资源(/static/..., /assets/...)，且没有包含任何 SQL 注入、XSS 代码、命令执行载荷或明显的扫描特征（如 .git, .env, wp-admin 等），请务必将其判定为 "正常流量"。
2. 【扫描判定】：只有当请求包含明确的漏洞探测路径（如 .env, actuator, shell, admin.php, .git 等）或明显的攻击载荷时，才判定为 "扫描探测" 或其他攻击类型。
3. 【误报防止】：不要仅仅因为请求来自外部 IP 就判定为攻击。如果没有恶意特征，就是正常流量。普通用户的浏览行为不应标记为扫描。
4. 【登录尝试】：对于 SSH、FTP、MySQL、Redis 等协议的单次登录尝试日志（例如仅包含一对用户名和密码的验证），请判定为 "{protocol}尝试登录" (如 "SSH尝试登录") 或者是 "正常流量"，**绝对不要**将其判定为 "暴力破解"。"暴力破解" 的判定由系统另外的频次检测引擎负责，单条日志不应判定为暴力破解。

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
        
        # 如果有IP历史信息，添加到 Prompt 中
        if ip_history_info:
            prompt += f"""
[IP 历史行为]
该 IP 在近 24 小时内的行为记录：
- 总请求次数: {ip_history_info.get('total_logs', 0)}
- 恶意请求次数: {ip_history_info.get('malicious_logs', 0)}
- 攻击类型分布: {ip_history_info.get('attack_type_distribution', {})}
- 历史样本: {ip_history_info.get('recent_samples', [])}
请结合历史行为判断当前请求是否属于持续攻击的一部分。
"""

        prompt += """
请按照以下JSON格式返回结果，不要包含思考过程或其他废话，只要JSON：
{
    "attack_type": "攻击类型(如果是正常请求务必返回 '正常流量', 否则返回具体且规范的中文攻击类型，如 'SQL注入', 'XSS', '扫描探测', '暴力破解', '命令注入' 等)",
    "confidence": 0.0-1.0之间的置信度数值,
    "analysis": "简短的分析理由(中文)"
}
"""
        return prompt
