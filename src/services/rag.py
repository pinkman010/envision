"""RAG问答服务"""

import re
import json
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from src.config import OLLAMA_URL, OLLAMA_TIMEOUT, MODELS
from src.services.vector_store import VectorStore


@dataclass
class RAGResponse:
    """RAG响应"""
    answer: str
    reasoning: str
    sources: List[Dict]
    confidence: float


class RAGEngine:
    """RAG问答引擎"""
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or MODELS["llm"]
        self.store = VectorStore()
        self.url = OLLAMA_URL
        self.timeout = OLLAMA_TIMEOUT
    
    def query(self, question: str, top_k: int = 5) -> RAGResponse:
        """执行RAG查询"""
        docs = self.store.search(question, top_k)
        
        if not docs:
            return RAGResponse(
                answer="知识库为空或未找到相关信息。",
                reasoning="无相关文档。",
                sources=[],
                confidence=0.0
            )
        
        prompt = self._build_prompt(question, docs)
        answer, reasoning = self._generate(prompt)
        confidence = self._calc_confidence(docs)
        
        return RAGResponse(
            answer=answer,
            reasoning=reasoning,
            sources=docs,
            confidence=confidence
        )
    
    def _build_prompt(self, question: str, docs: List[Dict]) -> str:
        """构建提示词"""
        context = "\n\n".join(
            f"[来源{i+1}] {d['metadata'].get('source', '未知')}:\n{d['text'][:500]}"
            for i, d in enumerate(docs)
        )
        
        return f"""基于以下参考文档回答问题：

{context}

问题：{question}

请在<think>标签内展示思考过程，然后给出答案。"""
    
    def _generate(self, prompt: str) -> Tuple[str, str]:
        """生成回答"""
        try:
            resp = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_ctx": 4096}
                },
                timeout=self.timeout
            )
            resp.raise_for_status()
            
            text = resp.json().get("response", "")
            
            # 提取思维链
            match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                answer = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
            else:
                reasoning = "未显示思考过程"
                answer = text
            
            return answer, reasoning
            
        except Exception as e:
            return f"生成失败: {e}", ""
    
    def _calc_confidence(self, docs: List[Dict]) -> float:
        """计算置信度"""
        if not docs:
            return 0.0
        scores = [d.get("score", 0) for d in docs]
        return round(sum(scores) / len(scores), 2)
