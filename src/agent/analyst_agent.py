"""
差距分析Agent（对照标准找差距）
核心职责：对照ISSB/HKEX标准，与同行对比，识别披露差距

变化点（v2.0）：
- 不再校验validation_status
- 输入从extract_result改为retrieval_result
- 输出从compliance_notes改为gap_analysis + peer_comparison
- 使用clean_and_parse_json替代validate_json_format
"""

from typing import Dict, Any

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger
from src.utils import (
    load_prompt_template,
    load_esg_standards,
    call_llm,
    clean_and_parse_json,
    ValidationException,
)


class AnalystAgent(BaseAgent):
    """差距分析Agent（对照标准+同行对比找差距）"""

    def __init__(self):
        super().__init__(
            agent_name="analyst_agent",
            agent_role="ESG差距分析专家（对照标准找差距，与同行对比找差异）",
        )
        # 加载Prompt模板和ESG标准
        self.analyst_prompt = load_prompt_template("analyst_prompt")
        self.esg_standards = load_esg_standards()

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行差距分析任务
        :param task_input: 必须包含 retrieval_result 字段
        :return: 差距分析结果 + 同行对比结果
        """
        # 1. 解析任务输入
        retrieval_result = task_input.get("retrieval_result")
        if not retrieval_result:
            raise ValidationException("任务输入缺少必填字段: retrieval_result")

        identified_topics = retrieval_result.get("identified_topics", [])
        retrieved_standards = retrieval_result.get("retrieved_standards", [])
        retrieved_peers = retrieval_result.get("retrieved_peers", [])
        input_text = retrieval_result.get("input_text", "")

        if not identified_topics:
            self.logger.warning("未识别到任何议题，跳过差距分析")
            return {
                "identified_topics": [],
                "gap_analysis": [],
                "peer_comparison": [],
                "overall_assessment": "未识别到ESG议题，无法进行分析",
                "status": "skipped",
            }

        # 2. 构建Prompt
        self.logger.debug("开始构建差距分析Prompt")
        prompt = self.analyst_prompt.render(
            identified_topics=identified_topics,
            retrieved_standards=retrieved_standards,
            retrieved_peers=retrieved_peers,
            input_text=input_text,
        )
        messages = [{"role": "user", "content": prompt}]

        # 3. 调用大模型
        self.logger.debug("开始调用大模型进行差距分析")
        llm_output = call_llm(messages)

        # 4. 宽松解析JSON（替代原来的validate_json_format）
        self.logger.debug("开始解析差距分析结果")
        analyst_data = clean_and_parse_json(llm_output, logger=self.logger)

        # 5. 确保必要字段存在
        if "gap_analysis" not in analyst_data:
            self.logger.warning("LLM输出缺少gap_analysis字段，返回空列表")
            analyst_data["gap_analysis"] = []

        if "peer_comparison" not in analyst_data:
            self.logger.warning("LLM输出缺少peer_comparison字段，返回空列表")
            analyst_data["peer_comparison"] = []

        if "overall_assessment" not in analyst_data:
            analyst_data["overall_assessment"] = "未生成整体评估"

        gap_analysis = analyst_data["gap_analysis"]
        peer_comparison = analyst_data["peer_comparison"]

        # 6. 统计差距分布
        major_count = len([g for g in gap_analysis if g.get("gap_level") == "major"])
        minor_count = len([g for g in gap_analysis if g.get("gap_level") == "minor"])
        none_count = len([g for g in gap_analysis if g.get("gap_level") == "none"])

        # 7. 返回结果
        self.logger.info(
            f"差距分析完成: 重大差距={major_count}, 轻微差距={minor_count}, 无差距={none_count}"
        )

        return {
            "identified_topics": identified_topics,
            "gap_analysis": gap_analysis,
            "peer_comparison": peer_comparison,
            "overall_assessment": analyst_data["overall_assessment"],
            "raw_llm_output": llm_output,
            "analysis_summary": {
                "major_gaps": major_count,
                "minor_gaps": minor_count,
                "no_gaps": none_count,
                "total_topics": len(identified_topics),
            },
            "status": "completed",
        }
