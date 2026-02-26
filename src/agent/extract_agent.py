"""
信息抽取Agent（仅做事实提取）
核心职责：仅按预设固定字段清单，从原文提取事实内容+行号锚点
无任何归类、判断、解读权限，仅允许从原文复制内容

支持RAG增强：利用语料库知识库提高信息提取精准度
"""

from typing import Dict, Any, List

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger, settings
from src.utils import (
    load_prompt_template,
    load_topic_rules,
    call_llm,
    validate_extraction_result,
    validate_similarity,
    validate_similarity_by_line,
    ValidationException,
    clean_and_parse_json,
    get_chroma_manager,
)


class ExtractAgent(BaseAgent):
    """信息抽取Agent（AI仅做事实提取+行号锚点，无任何判断权限）"""

    def __init__(self):
        super().__init__(
            agent_name="extract_agent",
            agent_role="固定字段事实提取工具（仅从原文复制内容+行号锚点）",
        )
        # 加载固定Prompt和固定字段清单
        self.extract_prompt = load_prompt_template("extract_prompt")
        self.topic_rules = load_topic_rules()
        # 从规则中获取固定字段清单（配置必须存在，无硬编码回退）
        self.fixed_fields = self.topic_rules.get("fixed_extraction_fields", [])
        if not self.fixed_fields:
            raise ValueError("配置文件中缺少 'fixed_extraction_fields' 字段，请检查 topic_rules.json")
        # 相似度阈值
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        # RAG增强配置
        self.use_rag_enhancement = settings.USE_RAG_ENHANCEMENT
        self.logger.info(f"信息抽取Agent初始化完成，相似度阈值: {self.similarity_threshold}, RAG增强: {self.use_rag_enhancement}")

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行信息抽取任务
        :param task_input: 必须包含 corpus_result 字段
        :return: 信息抽取结果
        """
        # 1. 解析任务输入
        corpus_result = task_input.get("corpus_result")
        if not corpus_result:
            raise ValidationException("任务输入缺少必填字段: corpus_result")
        fixed_text = corpus_result.get("fixed_text")
        if not fixed_text:
            raise ValidationException("语料处理结果缺少fixed_text字段")
        
        # 获取企业和年份信息
        metadata = corpus_result.get("metadata", {})
        company_name = metadata.get("company_name", "")
        report_year = metadata.get("report_year", 0)

        # 2. 构建Prompt
        self.logger.debug("开始构建信息抽取Prompt")
        prompt = self.extract_prompt.render(
            fixed_fields=self.fixed_fields,
            text=fixed_text[:8000],
        )
        messages = [{"role": "user", "content": prompt}]

        # 3. 调用大模型
        self.logger.debug("开始调用大模型进行信息抽取")
        llm_output = call_llm(messages)

        # 4. 清洗并解析JSON
        self.logger.debug(f"LLM返回内容长度: {len(llm_output) if llm_output else 0}")
        extraction_data = clean_and_parse_json(llm_output, logger=self.logger)
        if "extraction_results" not in extraction_data:
            self.logger.error(f"LLM输出缺少extraction_results字段")
            raise ValidationException("LLM输出缺少extraction_results字段")

        # 5. 逐个校验抽取结果
        self.logger.debug("开始逐个校验抽取结果")
        validated_results = []
        blocked_count = 0
        
        for result in extraction_data["extraction_results"]:
            # 5.1 校验格式完整性
            has_content = validate_extraction_result(result)
            if not has_content:
                result["validation_status"] = "not_found"
                result["similarity"] = None
                result["blocked"] = False
                validated_results.append(result)
                continue

            # 5.2 校验与原文的相似度
            extracted_content = result["extracted_content"]
            
            if "line_number" in result and result["line_number"] is not None:
                line_number = result["line_number"]
                is_passed, similarity, matched_text, exact_char_start, exact_char_end = validate_similarity_by_line(
                    fixed_text, extracted_content, line_number
                )
                result["matched_text"] = matched_text
                
                if exact_char_start >= 0 and exact_char_end > exact_char_start:
                    result["char_start"] = exact_char_start
                    result["char_end"] = exact_char_end
                else:
                    lines = fixed_text.split('\n')
                    if 1 <= line_number <= len(lines):
                        char_start = sum(len(lines[i]) + 1 for i in range(line_number - 1))
                        char_end = char_start + len(matched_text) if matched_text else char_start + len(lines[line_number - 1])
                        result["char_start"] = char_start
                        result["char_end"] = char_end
            elif "char_start" in result and "char_end" in result:
                char_start = result["char_start"]
                char_end = result["char_end"]
                is_passed, similarity = validate_similarity(fixed_text, extracted_content, char_start, char_end)
            else:
                self.logger.warning(f"抽取结果缺少位置信息: {result['field_name']}")
                result["validation_status"] = "failed"
                result["similarity"] = 0.0
                result["blocked"] = True
                validated_results.append(result)
                blocked_count += 1
                continue
            
            # 5.3 拦截逻辑
            if not is_passed:
                self.logger.warning(
                    f"抽取结果相似度校验失败，已拦截: {result['field_name']}, "
                    f"相似度: {similarity:.4f}, 阈值: {self.similarity_threshold}"
                )
                result["validation_status"] = "failed"
                result["similarity"] = similarity
                result["blocked"] = True
                blocked_count += 1
            else:
                result["validation_status"] = "passed"
                result["similarity"] = similarity
                result["blocked"] = False
                
            validated_results.append(result)

        # 6. RAG增强（可选）
        rag_enhanced_results = validated_results
        rag_stats = {"enhanced_count": 0}
        
        if self.use_rag_enhancement:
            self.logger.debug("开始RAG增强提取")
            try:
                chroma_manager = get_chroma_manager()
                
                for result in rag_enhanced_results:
                    if result.get("validation_status") != "passed":
                        continue
                    
                    field_name = result.get("field_name", "")
                    extracted_content = result.get("extracted_content", "")
                    
                    if not extracted_content:
                        continue
                    
                    # 执行RAG增强
                    enhancement = chroma_manager.enhance_extraction(
                        field_name=field_name,
                        extracted_content=extracted_content,
                        source_text=fixed_text,
                        company_name=company_name,
                        report_year=report_year,
                    )
                    
                    # 更新结果
                    if enhancement.enhanced_extraction != extracted_content:
                        result["enhanced_extraction"] = enhancement.enhanced_extraction
                        result["rag_enhanced"] = True
                        rag_stats["enhanced_count"] += 1
                    
                    result["rag_confidence_boost"] = enhancement.confidence_boost
                    result["rag_supporting_evidence"] = enhancement.supporting_evidence
                    result["rag_inconsistencies"] = enhancement.inconsistencies
                    result["rag_suggestions"] = enhancement.suggestions
                
                self.logger.info(f"RAG增强完成: 增强{rag_stats['enhanced_count']}个字段")
                
            except Exception as e:
                self.logger.error(f"RAG增强失败: {str(e)}")

        # 7. 返回结果
        passed_count = len([r for r in rag_enhanced_results if r['validation_status'] == 'passed'])
        failed_count = len([r for r in rag_enhanced_results if r['validation_status'] == 'failed'])
        not_found_count = len([r for r in rag_enhanced_results if r['validation_status'] == 'not_found'])
        
        self.logger.info(
            f"信息抽取完成 - 通过: {passed_count}, 失败: {failed_count}, "
            f"未找到: {not_found_count}, 拦截: {blocked_count}"
        )
        
        return {
            "corpus_metadata": corpus_result.get("metadata"),
            "fixed_fields": self.fixed_fields,
            "extraction_results": rag_enhanced_results,
            "raw_llm_output": llm_output,
            "validation_summary": {
                "passed": passed_count,
                "failed": failed_count,
                "not_found": not_found_count,
                "blocked": blocked_count,
                "total": len(rag_enhanced_results),
            },
            "similarity_threshold": self.similarity_threshold,
            "rag_enhancement": {
                "enabled": self.use_rag_enhancement,
                **rag_stats,
            } if self.use_rag_enhancement else {"enabled": False},
        }
