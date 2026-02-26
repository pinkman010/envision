"""
内容生成Agent（仅做固定模板填充，无自主创作权限）
核心职责：仅按固定模板，把人工确认后的结构化数据生成标准化文本
无自主创作、无开放式内容生成权限
"""

from typing import Dict, Any

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger
from src.utils import (
    load_prompt_template,
    call_llm,
    ValidationException,
)


class ContentAgent(BaseAgent):
    """内容生成Agent（仅做固定模板填充，无自主创作权限）"""

    def __init__(self):
        super().__init__(
            agent_name="content_agent",
            agent_role="固定模板文本填充工具（仅润色，无自主创作）",
        )
        # 加载固定Prompt（仅1条，无需调试）
        try:
            self.content_prompt = load_prompt_template("content_prompt")
        except FileNotFoundError:
            self.logger.warning("内容生成模板加载失败，ContentAgent可能无法正常工作")
            self.content_prompt = None

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行内容生成任务
        :param task_input: 必须包含 confirmed_data 和 template_type 字段
        :return: 内容生成结果（仅模板填充+润色）
        """
        # 1. 检查模板是否加载成功
        if self.content_prompt is None:
            raise ValidationException("内容生成模板未加载，无法执行内容生成任务")
        
        # 2. 解析任务输入
        confirmed_data = task_input.get("confirmed_data")
        template_type = task_input.get("template_type", "analysis_report")
        if not confirmed_data:
            raise ValidationException("任务输入缺少必填字段: confirmed_data")
        if not isinstance(confirmed_data, dict):
            raise ValidationException("confirmed_data必须为字典格式（人工确认后的结构化数据）")

        # 3. 构建固定Prompt（仅1条，无需调试）
        self.logger.debug(f"开始构建内容生成Prompt，模板类型: {template_type}")
        prompt = self.content_prompt.render(
            template_type=template_type,
            confirmed_data=confirmed_data,
        )
        messages = [{"role": "user", "content": prompt}]

        # 3. 调用大模型（仅做模板填充+润色，无自主创作）
        self.logger.debug("开始调用大模型进行内容生成")
        generated_content = call_llm(messages)

        # 4. 返回结果
        self.logger.debug("内容生成完成")
        return {
            "template_type": template_type,
            "confirmed_data": confirmed_data,
            "generated_content": generated_content,
            "important_note": "本内容仅为基于人工确认数据的模板填充与润色，无自主创作，所有核心数据、结论均来自人工确认",
        }
