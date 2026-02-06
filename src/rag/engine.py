"""RAG问答引擎

实现基于检索增强生成的智能问答功能。
"""

import re
import json
import requests
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass

from src.config import MODELS, OLLAMA_URL, OLLAMA_TIMEOUT
from src.vector_store import ChromaDBStore


@dataclass
class RAGResponse:
    """RAG响应结果"""
    answer: str
    reasoning: str  # 思考过程
    sources: List[Dict]  # 参考来源
    confidence: float  # 置信度


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
    
    def query(self, question: str, top_k: int = 5) -> RAGResponse:
        """执行RAG查询"""
        relevant_docs = self.store.search(question, top_k=top_k)
        
        if not relevant_docs:
            return RAGResponse(
                answer="抱歉，在知识库中未找到相关信息。",
                reasoning="知识库为空。",
                sources=[],
                confidence=0.0
            )
        
        prompt = self._build_prompt(question, relevant_docs)
        answer, reasoning = self._generate(prompt)
        confidence = self._calculate_confidence(relevant_docs)
        
        return RAGResponse(
            answer=answer,
            reasoning=reasoning,
            sources=relevant_docs,
            confidence=confidence
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
        
        return f"""基于以下参考文档回答问题：

{context}

问题：{question}

请在<think>标签内展示思考过程，然后给出答案。"""
    
    def _generate(self, prompt: str) -> Tuple[str, str]:
        """生成回答"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_ctx": 4096}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            text = response.json().get("response", "")
            
            match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                answer = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
            else:
                reasoning = "未显示思考过程"
                answer = text
            
            return answer, reasoning
            
        except Exception as e:
            return f"生成失败: {str(e)}", ""
    
    def _calculate_confidence(self, documents: List[Dict]) -> float:
        """计算置信度"""
        if not documents:
            return 0.0
        scores = [doc.get("score", 0) for doc in documents]
        avg_score = sum(scores) / len(scores)
        return round(max(0, min(1, (avg_score - 0.5) * 2)), 2)
