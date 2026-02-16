"""RAG问答引擎

实现基于检索增强生成的智能问答功能。
支持流式输出，提升用户体验。
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import requests

from src.esg.config import MODELS, OLLAMA_TIMEOUT, OLLAMA_URL
from src.esg.vector_store import ChromaDBStore


@dataclass
class RAGResponse:
    """RAG响应结果"""

    answer: str
    reasoning: str  # 思考过程
    sources: List[Dict]  # 参考来源
    confidence: float  # 置信度
    is_streaming: bool = False  # 是否为流式响应
    stream_generator: Optional[Generator[str, None, None]] = None  # 流式生成器


class RAGEngine:
    """RAG问答引擎"""

    def __init__(self, model: Optional[str] = None, store: Optional[ChromaDBStore] = None):
        """初始化RAG引擎

        Args:
            model: 使用的LLM模型名称
            store: 向量存储实例
        """
        self.model = model or MODELS.get("llm", "deepseek-r1:7b")
        self.store = store or ChromaDBStore()
        self.ollama_url = OLLAMA_URL
        self.timeout = OLLAMA_TIMEOUT

    def query(
        self, question: str, top_k: int = 5, stream: bool = False
    ) -> Union[RAGResponse, Generator[str, None, None]]:
        """执行RAG查询

        Args:
            question: 用户问题
            top_k: 检索文档数量
            stream: 是否使用流式输出

        Returns:
            RAGResponse 或 流式生成器
        """
        relevant_docs = self.store.search(question, top_k=top_k)

        if not relevant_docs:
            if stream:
                # 流式模式下返回错误信息生成器
                def empty_stream():
                    """当没有找到相关文档时，返回默认的空流响应"""
                    yield "抱歉，在知识库中未找到相关信息。"

                return empty_stream()
            return RAGResponse(
                answer="抱歉，在知识库中未找到相关信息。",
                reasoning="知识库为空。",
                sources=[],
                confidence=0.0,
            )

        prompt = self._build_prompt(question, relevant_docs)
        confidence = self._calculate_confidence(relevant_docs)

        if stream:
            # 返回流式生成器
            return self._generate_stream(prompt, relevant_docs, confidence)

        # 非流式模式
        answer, reasoning = self._generate(prompt)
        return RAGResponse(
            answer=answer, reasoning=reasoning, sources=relevant_docs, confidence=confidence
        )

    def _build_prompt(self, question: str, documents: List[Dict]) -> str:
        """构建RAG提示词"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            meta = doc.get("metadata", {})
            context_parts.append(
                f"[文档{i}] 来源: {meta.get('source', '未知')}\n{doc.get('text', '')[:500]}"
            )

        context = "\n\n".join(context_parts)

        return f"""你是一个ESG领域的专家助手。请基于以下参考文档回答问题。

参考文档：
{context}

用户问题：{question}

重要提示：在回答之前，请先展示你的思考过程。请用以下格式输出：

<thinking>
1. 分析用户问题的关键要点
2. 从参考文档中寻找相关信息
3. 推理和整理思路
4. 形成结论
</thinking>

<answer>
基于以上思考，给出清晰、准确的答案。
</answer>

请严格按照以上格式输出。"""

    def _generate(self, prompt: str) -> Tuple[str, str]:
        """生成回答（非流式）"""
        try:
            options = self._build_options()

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "options": options},
                timeout=self.timeout,
            )
            response.raise_for_status()

            text = response.json().get("response", "")
            reasoning, answer = self._extract_thinking_and_answer(text)

            return answer, reasoning

        except Exception as e:
            return f"生成失败: {str(e)}", ""

    def _generate_stream(
        self, prompt: str, sources: List[Dict], confidence: float
    ) -> Generator[str, None, None]:
        """流式生成回答

        Args:
            prompt: 构建好的提示词
            sources: 参考文档来源
            confidence: 置信度

        Yields:
            生成的文本片段
        """
        try:
            options = self._build_options()

            # 使用流式API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True, "options": options},
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()

            # 解析流式响应
            full_text = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("response", "")
                        full_text += chunk
                        yield chunk
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            yield f"\n[生成失败: {str(e)}]"

    def _build_options(self) -> Dict[str, Any]:
        """构建LLM选项

        Returns:
            选项字典
        """
        options = {
            "temperature": 0.7,
            "num_ctx": 4096,
        }

        # 针对 deepseek-r1 模型启用特殊推理模式
        if "deepseek-r1" in self.model.lower():
            options["num_predict"] = 2048

        return options

    def _extract_thinking_and_answer(self, text: str) -> Tuple[str, str]:
        """提取思考过程和答案

        尝试多种格式提取思考过程，支持流式文本的增量解析。
        """
        text = text.strip()

        # 尝试 <thinking>...</thinking> 格式
        think_match = re.search(r"<thinking>(.*?)</thinking>", text, re.DOTALL | re.IGNORECASE)
        if think_match:
            reasoning = think_match.group(1).strip()
            answer = re.sub(
                r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE
            ).strip()
            answer = re.sub(r"</?answer>", "", answer, flags=re.IGNORECASE).strip()
            return reasoning, answer

        # 尝试 <think>...</think> 格式
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL | re.IGNORECASE)
        if think_match:
            reasoning = think_match.group(1).strip()
            answer = re.sub(
                r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE
            ).strip()
            return reasoning, answer

        # 尝试识别 "思考：" 或 "分析：" 等中文标记
        think_match = re.search(
            r"(?:思考|分析|推理|思路)[：:](.*?)(?:答案|回答|结论)[：:]",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if think_match:
            reasoning = think_match.group(1).strip()
            answer_match = re.search(
                r"(?:答案|回答|结论)[：:](.*)", text, re.DOTALL | re.IGNORECASE
            )
            if answer_match:
                answer = answer_match.group(1).strip()
                return reasoning, answer

        # 尝试通过段落结构识别
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) >= 2 and len(text) > 500:
            mid = len(paragraphs) // 2
            reasoning = "\n\n".join(paragraphs[:mid])
            answer = "\n\n".join(paragraphs[mid:])
            return reasoning, answer

        # 默认返回
        return "模型未按照预期格式输出思考过程。以下是完整回答：", text

    def query_with_stream(
        self, question: str, top_k: int = 5
    ) -> Tuple[List[Dict], Generator[str, None, None], float]:
        """流式查询（兼容Streamlit的write_stream）

        Args:
            question: 用户问题
            top_k: 检索文档数量

        Returns:
            (sources, stream_generator, confidence)
        """
        relevant_docs = self.store.search(question, top_k=top_k)
        confidence = self._calculate_confidence(relevant_docs)

        if not relevant_docs:

            def empty_stream():
                """当没有找到相关文档时，返回默认的空流响应"""
                yield "抱歉，在知识库中未找到相关信息。"

            return [], empty_stream(), 0.0

        prompt = self._build_prompt(question, relevant_docs)
        return relevant_docs, self._generate_stream(prompt, relevant_docs, confidence), confidence

    def _calculate_confidence(self, documents: List[Dict]) -> float:
        """计算置信度"""
        if not documents:
            return 0.0
        scores = [doc.get("score", 0) for doc in documents]
        avg_score = sum(scores) / len(scores)
        return round(max(0, min(1, (avg_score - 0.5) * 2)), 2)
