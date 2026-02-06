# -*- coding: utf-8 -*-
"""
【核心逻辑】RAG 推理引擎（优化版）
修改内容：
1. [优化] 拆分 ask_stream 为多个小方法 - 提升可读性
2. [新增] 引用配置中心 - 消除硬编码
3. [新增] 日志记录 - 便于调试
4. [新增] 类型注解
5. [安全] 添加输入验证和 Prompt 注入防护
6. [修复] 资源管理和上下文管理器支持
"""
import os
import sys
import re
import requests
import json
import logging
from typing import Generator, Tuple, Any, List, Optional
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# === 路径补丁 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from scripts.ollama_utils import OllamaEmbeddings
from scripts.config import (
    OLLAMA_URL, MODELS, VECTOR_DB_PATH, 
    RETRIEVER_TOP_K, OLLAMA_TIMEOUT
)

logger = logging.getLogger(__name__)

# ==================== Prompt 模板 ====================
RAG_PROMPT_TEMPLATE = """
【Context / 参考资料】
{context}

【Question / 用户问题】
{query}

请根据上述参考资料回答问题。如果资料中没有相关信息，请说明。使用中文回答。
"""


def sanitize_input(text: Optional[str], max_length: int = 5000, field_name: str = "输入") -> str:
    """
    清理用户输入，防止 Prompt 注入攻击
    
    Args:
        text: 输入文本
        max_length: 最大长度限制
        field_name: 字段名称（用于错误提示）
    
    Returns:
        清理后的安全文本
    
    Raises:
        ValueError: 输入不合法时抛出
    """
    if text is None:
        raise ValueError(f"{field_name} 不能为空")
    
    text = text.strip()
    
    if not text:
        raise ValueError(f"{field_name} 不能为空")
    
    if len(text) > max_length:
        raise ValueError(f"{field_name} 长度超过限制（最大 {max_length} 字符）")
    
    # 移除控制字符（保留换行和制表符）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 转义特殊标签，防止 Prompt 注入
    dangerous_patterns = [
        (r'<think>', '[思考开始]'),
        (r'</think>', '[思考结束]'),
        (r'<\s*/?\s*[Ss][Yy][Ss][Tt][Ee][Mm]\s*>', '[系统标签]'),
        (r'<\s*/?\s*[Uu][Ss][Ee][Rr]\s*>', '[用户标签]'),
        (r'<\s*/?\s*[Aa][Ss][Ss][Ii][Ss][Tt][Aa][Nn][Tt]\s*>', '[助手标签]'),
        (r'【\s*[Ss][Yy][Ss][Tt][Ee][Mm]\s*】', '[系统标记]'),
    ]
    
    for pattern, replacement in dangerous_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


class RAGSystem:
    """RAG 问答系统"""
    
    def __init__(self, db_path: str = VECTOR_DB_PATH, top_k: int = RETRIEVER_TOP_K):
        """
        初始化
        修改点：top_k 参数化，便于调优
        """
        self.top_k = self._validate_top_k(top_k)
        self.embeddings = OllamaEmbeddings()
        
        if not os.path.exists(db_path) or not os.listdir(db_path):
            raise FileNotFoundError(
                f"向量数据库不存在: {db_path}\n"
                "请先运行: python scripts/create_vector_db.py"
            )
        
        self.vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings
        )
        self.retriever = self.vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k}
        )
        self._closed = False
        logger.info(f"RAG 系统初始化完成，知识库大小: {self.get_doc_count()}")

    @staticmethod
    def _validate_top_k(value: int) -> int:
        """验证 top_k 参数"""
        if not isinstance(value, int):
            raise TypeError(f"top_k 必须是整数，当前类型: {type(value)}")
        if value < 1 or value > 20:
            raise ValueError(f"top_k 必须在 1-20 之间，当前值: {value}")
        return value

    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，确保资源释放"""
        self.close()
    
    def close(self):
        """显式释放资源"""
        if self._closed:
            return
        
        try:
            if hasattr(self, 'vector_db') and self.vector_db:
                logger.info("正在持久化向量数据库...")
                self.vector_db.persist()
        except Exception as e:
            logger.error(f"持久化数据库失败: {e}")
        finally:
            self.vector_db = None
            self._closed = True
            logger.info("RAG 系统资源已释放")

    def get_doc_count(self) -> int:
        """获取文档数量"""
        try:
            return self.vector_db._collection.count()
        except Exception:
            return 0

    def _retrieve_context(self, query: str) -> Tuple[List[Document], str]:
        """
        检索相关文档（修改点：拆分为独立方法）
        """
        # 验证输入
        if not query or not query.strip():
            raise ValueError("查询不能为空")
        
        docs = self.retriever.invoke(query)
        context = "\n\n".join([d.page_content for d in docs])
        return docs, context

    def _build_prompt(self, query: str, context: str) -> str:
        """构建提示词"""
        # 清理输入，防止 Prompt 注入
        safe_query = sanitize_input(query, max_length=2000, field_name="查询")
        safe_context = sanitize_input(context, max_length=10000, field_name="上下文")
        return RAG_PROMPT_TEMPLATE.format(context=safe_context, query=safe_query)

    def _parse_stream_response(
        self, 
        response_stream, 
        docs: List[Document]
    ) -> Generator[Tuple[str, Any], None, None]:
        """
        解析流式响应（修改点：拆分思维链解析逻辑）
        """
        in_think_block = False
        
        for line in response_stream.iter_lines():
            if not line:
                continue
            
            try:
                body = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            content = body.get("response", "")
            
            # 优先处理结束信号
            if body.get("done", False):
                yield "done", {"source_documents": docs, "answer": ""}
                return
            
            if not content:
                continue

            # 思维链解析
            if "<think>" in content:
                in_think_block = True
                content = content.replace("<think>", "")
                if content.strip():
                    yield "think", content
                continue

            if "</think>" in content:
                in_think_block = False
                parts = content.split("</think>")
                if parts[0].strip():
                    yield "think", parts[0]
                yield "think_end", ""
                if len(parts) > 1 and parts[1].strip():
                    yield "answer", parts[1]
                continue

            # 常规输出
            yield ("think" if in_think_block else "answer"), content

    def ask_stream(self, query: str) -> Generator[Tuple[str, Any], None, None]:
        """
        流式问答生成器
        Yields: (msg_type, content)
            - "status": 状态信息
            - "think": 思维链内容
            - "think_end": 思维链结束
            - "answer": 回答内容
            - "done": 完成信号，包含 source_documents
        
        Raises:
            RuntimeError: 系统已关闭时调用
        """
        if self._closed:
            raise RuntimeError("RAG 系统已关闭，无法处理请求")
        
        # Step 1: 检索
        yield "status", "🔍 正在检索相关文档..."
        
        try:
            docs, context = self._retrieve_context(query)
            
            if not docs:
                yield "status", "⚠️ 未找到相关文档，将使用通用知识回答"
            else:
                yield "status", f"📚 已检索到 {len(docs)} 个相关片段"
        except ValueError as e:
            yield "status", f"❌ 输入错误: {e}"
            yield "done", {"source_documents": []}
            return
        except Exception as e:
            logger.error(f"检索失败: {e}")
            yield "answer", f"检索错误: {str(e)}"
            yield "done", {"source_documents": []}
            return

        # Step 2: 构建 Prompt
        prompt = self._build_prompt(query, context)

        # Step 3: 调用 LLM
        try:
            with requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODELS["llm"],
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=OLLAMA_TIMEOUT * 2  # 生成可能较慢
            ) as response:
                response.raise_for_status()
                yield from self._parse_stream_response(response, docs)
                
        except requests.RequestException as e:
            logger.error(f"LLM 调用失败: {e}")
            yield "answer", f"生成错误: {str(e)}"
            yield "done", {"source_documents": docs}


def init_system(warmup: bool = True) -> Tuple['RAGSystem', int]:
    """
    工厂函数
    参数:
        warmup: 是否预热模型（首次调用较慢）
    """
    rag = RAGSystem()
    
    if warmup:
        # 发送一个简单请求预热模型
        try:
            list(rag.ask_stream("测试"))  # 消费生成器
            logger.info("模型预热完成")
        except Exception as e:
            logger.warning(f"预热失败（可忽略）: {e}")
    
    return rag, rag.get_doc_count()