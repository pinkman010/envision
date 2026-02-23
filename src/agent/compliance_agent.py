"""
合规提示Agent（仅做风险标注，无任何拦截/决策权限）
核心职责：仅按预设合规条款，给抽取内容做风险高亮标注
最终决策权100%在人工手里
"""

from typing import Dict, Any, List

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger
from src.utils import (
    load_prompt_template,
    load_esg_standards,
    call_llm,
    validate_json_format,
    ValidationException,
)


class ComplianceAgent(BaseAgent):
    """合规提示Agent（仅做风险标注，无任何拦截/决策权限）"""

    def __init__(self):
        super().__init__(
            agent_name="compliance_agent",
            agent_role="ESG合规风险高亮标注工具（仅做提示，无决策权限）",
        )
        # 加载固定Prompt和合规条款（仅1条Prompt，无需调试）
        self.compliance_prompt = load_prompt_template("compliance_prompt")
        self.esg_standards = load_esg_standards()

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行合规提示任务
        :param task_input: 必须包含 extract_result 字段（信息抽取Agent的输出）
        :return: 合规提示结果（仅风险标注，无决策）
        """
        # 1. 解析任务输入
        extract_result = task_input.get("extract_result")
        if not extract_result:
            raise ValidationException("任务输入缺少必填字段: extract_result")
        extraction_results = extract_result.get("extraction_results")
        if not extraction_results:
            self.logger.warning("无抽取结果，跳过合规提示")
            return {"compliance_notes": [], "status": "skipped"}

        # 2. 仅对校验通过的抽取结果做合规提示
        passed_results = [r for r in extraction_results if r.get("validation_status") == "passed"]
        if not passed_results:
            self.logger.warning("无校验通过的抽取结果，跳过合规提示")
            return {"compliance_notes": [], "status": "skipped"}

        # 3. 构建固定Prompt（仅1条，无需调试）
        self.logger.debug("开始构建合规提示Prompt")
        prompt = self.compliance_prompt.render(
            esg_standards=self.esg_standards.get("core_standards", []),
            extraction_results=passed_results,
        )
        messages = [{"role": "user", "content": prompt}]

        # 4. 调用大模型（仅做风险标注，强制JSON格式）
        self.logger.debug("开始调用大模型进行合规提示")
        llm_output = call_llm(messages)

        # 5. 校验JSON格式
        self.logger.debug("开始校验合规提示JSON格式")
        compliance_data = validate_json_format(llm_output)
        if "compliance_notes" not in compliance_data:
            raise ValidationException("LLM输出缺少compliance_notes字段")

        # 6. 给每个合规提示加上明确的「仅为提示，无决策权限」标识
        for note in compliance_data["compliance_notes"]:
            note["note_type"] = "compliance_hint_only"
            note["decision_right"] = "人工最终决策"

        # 7. 返回结果
        self.logger.debug(f"合规提示完成，风险提示数: {len(compliance_data['compliance_notes'])}")
        return {
            "extraction_metadata": extract_result.get("corpus_metadata"),
            "compliance_notes": compliance_data["compliance_notes"],
            "raw_llm_output": llm_output,
            "status": "completed",
            "important_note": "本结果仅为合规风险提示，不构成任何合规决策，最终决策权100%在人工手里",
        }
