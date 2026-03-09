"""
议题检索Agent（RAG驱动的问题识别）
核心职责：从知识库检索相关标准条文，用LLM识别输入文本涉及的ESG议题

变化点（v2.0）：
- 不再做字符级锚点和相似度校验
- 不再使用fixed_fields固定字段清单
- 新增RAG检索standards/和peer_reports/集合
- 输出改为identified_topics + retrieved_standards + retrieved_peers
"""

from typing import Dict, Any, List

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger
from src.utils import (
    load_prompt_template,
    load_topic_rules,
    call_llm,
    clean_and_parse_json,
    ValidationException,
    get_chroma_manager,
)


class RetrievalAgent(BaseAgent):
    """议题检索Agent（RAG+LLM识别ESG议题）"""

    def __init__(self):
        super().__init__(
            agent_name="retrieval_agent",
            agent_role="ESG议题识别与知识库检索工具（RAG驱动）",
        )
        # 加载Prompt模板和议题规则
        self.retrieval_prompt = load_prompt_template("retrieval_prompt")
        self.topic_rules = load_topic_rules()
        self.topics = self.topic_rules.get("topics", [])
        self.logger.info(f"议题检索Agent初始化完成，支持 {len(self.topics)} 个ESG议题")

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行议题检索任务
        :param task_input: 必须包含 corpus_result 字段
        :return: 议题识别结果 + 检索到的标准条文 + 检索到的同行案例
        """
        # 1. 解析任务输入
        corpus_result = task_input.get("corpus_result")
        if not corpus_result:
            raise ValidationException("任务输入缺少必填字段: corpus_result")
        fixed_text = corpus_result.get("fixed_text")
        if not fixed_text:
            raise ValidationException("语料处理结果缺少fixed_text字段")

        metadata = corpus_result.get("metadata", {})

        # 2. RAG检索知识库
        self.logger.debug("开始RAG检索知识库")
        try:
            chroma_manager = get_chroma_manager()

            # 2.1 检索标准条文（standards集合）
            # 使用文本摘要作为查询，获取相关标准
            query_text = fixed_text[:500]  # 取前500字符作为查询
            retrieved_standards = chroma_manager.search_standards(
                query=query_text,
                n_results=5,
                score_threshold=0.5,
            )

            # 2.2 检索同行案例（peer_reports集合）
            retrieved_peers = chroma_manager.search_peer_reports(
                query=query_text,
                n_results=3,
                score_threshold=0.5,
            )

            self.logger.info(
                f"RAG检索完成: standards={len(retrieved_standards)}, peers={len(retrieved_peers)}"
            )

        except Exception as e:
            self.logger.warning(f"RAG检索失败（可能集合为空）: {str(e)}")
            retrieved_standards = []
            retrieved_peers = []

        # 3. 构建Prompt并调用LLM识别议题
        self.logger.debug("开始构建议题识别Prompt")
        prompt = self.retrieval_prompt.render(
            topics=self.topics,
            retrieved_standards=retrieved_standards,
            retrieved_peers=retrieved_peers,
            input_text=fixed_text,
        )
        messages = [{"role": "user", "content": prompt}]

        # 4. 调用大模型
        self.logger.debug("开始调用大模型进行议题识别")
        llm_output = call_llm(messages)

        # 5. 清洗并解析JSON
        self.logger.debug(f"LLM返回内容长度: {len(llm_output) if llm_output else 0}")
        retrieval_data = clean_and_parse_json(llm_output, logger=self.logger)

        if "identified_topics" not in retrieval_data:
            self.logger.warning("LLM输出缺少identified_topics字段，返回空列表")
            retrieval_data["identified_topics"] = []

        if "coverage_summary" not in retrieval_data:
            retrieval_data["coverage_summary"] = "未能生成覆盖情况总结"

        identified_topics = retrieval_data["identified_topics"]

        # 6. 返回结果
        self.logger.info(f"议题识别完成: 识别到 {len(identified_topics)} 个议题")

        return {
            "corpus_metadata": metadata,
            "input_text": fixed_text[:6000],  # 保留输入文本供后续使用
            "identified_topics": identified_topics,
            "retrieved_standards": retrieved_standards,
            "retrieved_peers": retrieved_peers,
            "coverage_summary": retrieval_data["coverage_summary"],
            "raw_llm_output": llm_output,
            "retrieval_summary": {
                "topic_count": len(identified_topics),
                "standards_count": len(retrieved_standards),
                "peers_count": len(retrieved_peers),
            },
        }
