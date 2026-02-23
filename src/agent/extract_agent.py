"""
信息抽取Agent（仅做事实提取）
核心职责：仅按预设固定字段清单，从原文提取事实内容+行号锚点
无任何归类、判断、解读权限，仅允许从原文复制内容
"""

from typing import Dict, Any, List

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger, settings
from src.utils import (
    load_prompt_template,
    load_topic_rules,
    call_llm,
    validate_json_format,
    validate_extraction_result,
    validate_similarity,
    validate_similarity_by_line,
    ValidationException,
    clean_and_parse_json,
)


class ExtractAgent(BaseAgent):
    """信息抽取Agent（AI仅做事实提取+行号锚点，无任何判断权限）"""

    def __init__(self):
        super().__init__(
            agent_name="extract_agent",
            agent_role="固定字段事实提取工具（仅从原文复制内容+行号锚点）",
        )
        # 加载固定Prompt和固定字段清单（仅1条Prompt，无需调试）
        self.extract_prompt = load_prompt_template("extract_prompt")
        self.topic_rules = load_topic_rules()
        # 从规则中获取固定字段清单（待行业研究结果，存入规则）
        self.fixed_fields = self.topic_rules.get("fixed_extraction_fields", [
            "company_name", "report_year", "scope1_emission", "scope2_emission", "green_energy_usage"
        ])

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行信息抽取任务
        :param task_input: 必须包含 corpus_result 字段（语料处理Agent的输出）
        :return: 信息抽取结果（带行号锚点、相似度校验）
        """
        # 1. 解析任务输入
        corpus_result = task_input.get("corpus_result")
        if not corpus_result:
            raise ValidationException("任务输入缺少必填字段: corpus_result")
        fixed_text = corpus_result.get("fixed_text")
        if not fixed_text:
            raise ValidationException("语料处理结果缺少fixed_text字段")

        # 2. 构建固定Prompt（仅1条，无需调试）
        self.logger.debug("开始构建信息抽取Prompt")
        prompt = self.extract_prompt.render(
            fixed_fields=self.fixed_fields,
            text=fixed_text[:8000],  # 仅取前8000字符（避免token超限）（15000字符提取时间过长）
        )
        messages = [{"role": "user", "content": prompt}]

        # 3. 调用大模型（仅做事实提取，强制JSON格式）
        self.logger.debug("开始调用大模型进行信息抽取")
        llm_output = call_llm(messages)

        # 4. 清洗并校验JSON格式（防御性解析：处理Markdown包裹、前后废话等）
        self.logger.debug(f"LLM返回内容长度: {len(llm_output) if llm_output else 0}, 前200字符: {repr(llm_output[:200]) if llm_output else 'None'}")
        extraction_data = clean_and_parse_json(llm_output, logger=self.logger)
        if "extraction_results" not in extraction_data:
            self.logger.error(f"LLM输出缺少extraction_results字段，原始输出: {llm_output[:500]}")
            raise ValidationException("LLM输出缺少extraction_results字段")

        # 5. 逐个校验抽取结果（格式、行号锚点、相似度）
        self.logger.debug("开始逐个校验抽取结果")
        validated_results = []
        for result in extraction_data["extraction_results"]:
            # 5.1 校验格式完整性；返回 False = 该字段原文中未找到（合法），跳过相似度校验
            has_content = validate_extraction_result(result)
            if not has_content:
                result["validation_status"] = "not_found"
                result["similarity"] = None
                self.logger.debug(f"字段在原文中未找到，跳过相似度校验: {result.get('field_name')}")
                validated_results.append(result)
                continue

            # 5.2 校验与原文的相似度（拦截幻觉）
            extracted_content = result["extracted_content"]
            
            # 优先使用行号进行校验（更准确）
            if "line_number" in result and result["line_number"] is not None:
                line_number = result["line_number"]
                is_passed, similarity, matched_text = validate_similarity_by_line(
                    fixed_text, extracted_content, line_number
                )
                result["matched_text"] = matched_text  # 记录匹配到的原文行
            # 兼容旧格式：使用字符位置
            elif "char_start" in result and "char_end" in result:
                char_start = result["char_start"]
                char_end = result["char_end"]
                is_passed, similarity = validate_similarity(fixed_text, extracted_content, char_start, char_end)
            else:
                # 没有位置信息，无法校验
                self.logger.warning(f"抽取结果缺少位置信息: {result['field_name']}")
                result["validation_status"] = "failed"
                result["similarity"] = 0.0
                validated_results.append(result)
                continue
            
            if not is_passed:
                self.logger.warning(
                    f"抽取结果相似度校验失败: {result['field_name']}, "
                    f"相似度: {similarity:.2f}, 阈值: {settings.SIMILARITY_THRESHOLD}"
                )
                result["validation_status"] = "failed"
                result["similarity"] = similarity
            else:
                result["validation_status"] = "passed"
                result["similarity"] = similarity
            validated_results.append(result)

        # 6. 返回结果
        passed_count = len([r for r in validated_results if r['validation_status'] == 'passed'])
        failed_count = len([r for r in validated_results if r['validation_status'] == 'failed'])
        not_found_count = len([r for r in validated_results if r['validation_status'] == 'not_found'])
        self.logger.debug(f"信息抽取完成，通过: {passed_count}, 失败: {failed_count}, 未找到: {not_found_count}")
        
        return {
            "corpus_metadata": corpus_result.get("metadata"),
            "fixed_fields": self.fixed_fields,
            "extraction_results": validated_results,
            "raw_llm_output": llm_output,
        }
