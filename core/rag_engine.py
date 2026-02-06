"""RAG引擎

提供基于检索增强生成的问答功能，支持COT思维链显示。
"""

import re
import json
import requests
from typing import List, Dict, Optional, Generator, Tuple
from dataclasses import dataclass

from config import OLLAMA_URL, OLLAMA_TIMEOUT, MODELS
from vector_db.chroma_store import ChromaDBStore, get_db_store


@dataclass
class RAGResponse:
    """RAG响应数据结构"""
    answer: str
    reasoning: str  # COT思维过程
    sources: List[Dict]  # 参考来源
    confidence: float  # 置信度


class RAGEngine:
    """RAG问答引擎"""
    
    def __init__(self, model_name: Optional[str] = None):
        """初始化RAG引擎
        
        Args:
            model_name: 使用的模型名称，默认使用config中的配置
        """
        self.model_name = model_name or MODELS.get("llm", "deepseek-r1:7b")
        self.ollama_url = OLLAMA_URL
        self.timeout = OLLAMA_TIMEOUT
        
        # 获取数据库实例
        try:
            self.db_store = get_db_store()
            if self.db_store is None or not getattr(self.db_store, '_initialized', False):
                raise RuntimeError("向量数据库未正确初始化")
        except Exception as e:
            raise RuntimeError(f"RAG引擎初始化失败: {e}")
    
    def query(self, question: str, top_k: int = 5) -> RAGResponse:
        """执行RAG查询
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            
        Returns:
            RAG响应，包含答案、思维过程、来源
        """
        # 1. 检索相关文档
        relevant_docs = self.db_store.search(question, top_k=top_k)
        
        if not relevant_docs:
            return RAGResponse(
                answer="抱歉，在知识库中未找到相关信息。",
                reasoning="知识库为空或未找到相关文档。",
                sources=[],
                confidence=0.0
            )
        
        # 2. 构建提示词
        prompt = self._build_prompt(question, relevant_docs)
        
        # 3. 调用模型生成回答
        answer, reasoning = self._generate_with_cot(prompt)
        
        # 4. 计算置信度
        confidence = self._calculate_confidence(relevant_docs)
        
        return RAGResponse(
            answer=answer,
            reasoning=reasoning,
            sources=relevant_docs,
            confidence=confidence
        )
    
    def query_stream(self, question: str, top_k: int = 4) -> Generator[str, None, None]:
        """流式RAG查询（用于实时显示）
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            
        Yields:
            生成的文本片段
        """
        # 检索相关文档
        relevant_docs = self.db_store.search(question, top_k=top_k)
        
        if not relevant_docs:
            yield json.dumps({
                'type': 'error',
                'content': '知识库为空或未找到相关文档。'
            })
            return
        
        # 发送来源信息
        yield json.dumps({
            'type': 'sources',
            'content': relevant_docs
        })
        
        # 构建提示词
        prompt = self._build_prompt(question, relevant_docs)
        
        # 流式生成
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 4096
                    }
                },
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            reasoning_buffer = []
            answer_buffer = []
            in_reasoning = True
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get('response', '')
                        
                        # 检测思维链标记（deepseek-r1使用<think>标签）
                        if '<think>' in token:
                            in_reasoning = True
                            token = token.replace('<think>', '')
                        elif '</think>' in token:
                            in_reasoning = False
                            token = token.replace('</think>', '')
                        
                        # 根据状态分类输出
                        if in_reasoning:
                            reasoning_buffer.append(token)
                            yield json.dumps({
                                'type': 'reasoning',
                                'content': token
                            })
                        else:
                            answer_buffer.append(token)
                            yield json.dumps({
                                'type': 'answer',
                                'content': token
                            })
                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            yield json.dumps({
                'type': 'error',
                'content': f'生成回答时出错: {str(e)}'
            })
    
    def _build_prompt(self, question: str, documents: List[Dict]) -> str:
        """构建RAG提示词
        
        Args:
            question: 用户问题
            documents: 相关文档列表
            
        Returns:
            完整的提示词
        """
        # 构建上下文
        context_parts = []
        for i, doc in enumerate(documents, 1):
            meta = doc.get('metadata', {})
            context_parts.append(
                f"[文档{i}] 来源: {meta.get('source', '未知')}, "
                f"位置: {meta.get('position', '未知')}\n"
                f"内容: {doc.get('text', '')}\n"
            )
        
        context = "\n".join(context_parts)
        
        prompt = f"""你是一个专业的ESG（环境、社会、治理）分析助手。请基于以下参考文档回答用户问题。

参考文档：
{context}

用户问题：{question}

请按照以下格式回答：
1. 首先展示你的思考过程（在<think>标签内）
2. 然后给出简洁、准确的答案
3. 答案应基于参考文档，如果文档中信息不足，请明确说明

回答格式示例：
<think>
1. 用户询问的是...
2. 在参考文档[1]中，提到了...
3. 综合分析，答案是...
</think>

[最终答案]
"""
        return prompt
    
    def _generate_with_cot(self, prompt: str) -> Tuple[str, str]:
        """生成带思维链的回答
        
        Args:
            prompt: 提示词
            
        Returns:
            (答案, 思维过程)
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 4096
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            full_text = result.get('response', '')
            
            # 提取思维过程和答案
            reasoning_match = re.search(r'<think>(.*?)</think>', full_text, re.DOTALL)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
                answer = re.sub(r'<think>.*?</think>', '', full_text, flags=re.DOTALL).strip()
                # 移除"[最终答案]"标记
                answer = answer.replace('[最终答案]', '').strip()
            else:
                # 如果没有思维链标记，全部作为答案
                reasoning = "模型未返回明确的思考过程。"
                answer = full_text
            
            return answer, reasoning
            
        except Exception as e:
            return f"生成回答时出错: {str(e)}", ""
    
    def _calculate_confidence(self, documents: List[Dict]) -> float:
        """计算回答置信度
        
        Args:
            documents: 相关文档列表
            
        Returns:
            置信度分数(0-1)
        """
        if not documents:
            return 0.0
        
        # 基于文档相似度计算置信度
        scores = [doc.get('score', 0) for doc in documents]
        avg_score = sum(scores) / len(scores)
        
        # 归一化到0-1范围（假设相似度在0.5-1.0之间是合理的）
        confidence = max(0, min(1, (avg_score - 0.5) * 2))
        
        return round(confidence, 2)
    
    def index_documents(self, data_dir: str) -> int:
        """索引文档到向量数据库
        
        Args:
            data_dir: 数据目录路径
            
        Returns:
            索引的文档数量
        """
        from vector_db.chroma_store import load_and_index_documents
        return load_and_index_documents(data_dir, self.db_store)


# 全局实例
_rag_engine = None

def get_rag_engine() -> RAGEngine:
    """获取全局RAG引擎实例（单例模式）"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
