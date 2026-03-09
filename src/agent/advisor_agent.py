"""
优化建议Agent（生成可操作的改进建议）
核心职责：根据差距分析结果，结合同行优秀案例，生成具体可操作的改进建议

变化点（v2.0）：
- 输入从confirmed_data + template_type改为analyst_result
- 输出从generated_content改为recommendations + priority_actions + generated_content
- 删除多模板选择，固定一套输出格式
"""

from typing import Dict, Any, List

from src.agent.base_agent import BaseAgent
from src.config import get_logger
from src.utils import (
    load_prompt_template,
    call_llm,
    clean_and_parse_json,
    ValidationException,
)


class AdvisorAgent(BaseAgent):
    """优化建议Agent（生成可操作的ESG改进建议）"""

    def __init__(self):
        super().__init__(
            agent_name="advisor_agent",
            agent_role="ESG披露优化顾问（生成具体可操作的改进建议）",
        )
        # 加载Prompt模板
        try:
            self.advisor_prompt = load_prompt_template("advisor_prompt")
        except FileNotFoundError:
            self.logger.warning("优化建议模板加载失败，AdvisorAgent可能无法正常工作")
            self.advisor_prompt = None

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行优化建议生成任务
        :param task_input: 必须包含 analyst_result 字段
        :return: 改进建议结果（含优先行动项和完整建议文本）
        """
        # 1. 检查模板是否加载成功
        if self.advisor_prompt is None:
            raise ValidationException("优化建议模板未加载，无法执行建议生成任务")
        
        # 2. 解析任务输入
        analyst_result = task_input.get("analyst_result")
        if not analyst_result:
            raise ValidationException("任务输入缺少必填字段: analyst_result")
        
        gap_analysis = analyst_result.get("gap_analysis", [])
        peer_comparison = analyst_result.get("peer_comparison", [])
        overall_assessment = analyst_result.get("overall_assessment", "")

        if not gap_analysis:
            self.logger.warning("无差距分析结果，跳过建议生成")
            return {
                "recommendations": [],
                "priority_actions": [],
                "reference_cases": [],
                "generated_content": "未发现明显差距，暂无改进建议",
                "status": "skipped",
            }

        # 3. 构建Prompt
        self.logger.debug("开始构建优化建议Prompt")
        prompt = self.advisor_prompt.render(
            gap_analysis=gap_analysis,
            peer_comparison=peer_comparison,
            overall_assessment=overall_assessment,
        )
        messages = [{"role": "user", "content": prompt}]

        # 4. 调用大模型
        self.logger.debug("开始调用大模型生成优化建议")
        llm_output = call_llm(messages)

        # 5. 解析JSON结果
        self.logger.debug("开始解析优化建议结果")
        advisor_data = clean_and_parse_json(llm_output, logger=self.logger)
        
        # 6. 确保必要字段存在
        if "recommendations" not in advisor_data:
            self.logger.warning("LLM输出缺少recommendations字段，返回空列表")
            advisor_data["recommendations"] = []
        
        if "priority_actions" not in advisor_data:
            self.logger.warning("LLM输出缺少priority_actions字段，返回空列表")
            advisor_data["priority_actions"] = []
        
        if "generated_content" not in advisor_data:
            # 如果没有generated_content，从recommendations生成一个简版
            generated_content = self._generate_simple_content(advisor_data["recommendations"])
            advisor_data["generated_content"] = generated_content

        recommendations = advisor_data["recommendations"]
        priority_actions = advisor_data["priority_actions"]
        generated_content = advisor_data["generated_content"]

        # 7. 提取参考案例
        reference_cases = [
            r.get("reference_case", "") 
            for r in recommendations 
            if r.get("reference_case")
        ]

        # 8. 统计建议分布
        high_count = len([r for r in recommendations if r.get("priority") == "high"])
        medium_count = len([r for r in recommendations if r.get("priority") == "medium"])
        low_count = len([r for r in recommendations if r.get("priority") == "low"])

        # 9. 返回结果
        self.logger.info(
            f"优化建议生成完成: 总建议={len(recommendations)}, "
            f"高优先级={high_count}, 优先行动={len(priority_actions)}"
        )
        
        return {
            "recommendations": recommendations,
            "priority_actions": priority_actions,
            "reference_cases": reference_cases,
            "generated_content": generated_content,
            "raw_llm_output": llm_output,
            "advisor_summary": {
                "total_recommendations": len(recommendations),
                "high_priority": high_count,
                "medium_priority": medium_count,
                "low_priority": low_count,
                "priority_actions_count": len(priority_actions),
            },
            "status": "completed",
        }

    def _generate_simple_content(self, recommendations: List[Dict[str, Any]]) -> str:
        """从recommendations生成简化的建议文本（兜底）"""
        if not recommendations:
            return "暂无改进建议"
        
        lines = ["# ESG披露优化建议", ""]
        for i, rec in enumerate(recommendations, 1):
            topic = rec.get("topic_name", "未知议题")
            action = rec.get("action", "")
            priority = rec.get("priority", "")
            standard = rec.get("standard_basis", "")
            
            lines.append(f"{i}. 【{topic}】{action}")
            lines.append(f"   优先级：{priority}")
            if standard:
                lines.append(f"   依据标准：{standard}")
            lines.append("")
        
        return "\n".join(lines)
