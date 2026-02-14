"""向量存储模块

提供基于 ChromaDB 的向量存储功能和文档加载功能。
支持 Ollama embedding 和多种文档格式。
"""

from src.esg.vector_store.chroma_store import (
    HAS_CHROMADB,
    ChromaDBStore,
    VectorStore,
    get_chromadb_error,
)
from src.esg.vector_store.document_loader import DocumentLoader

__all__ = ["ChromaDBStore", "VectorStore", "DocumentLoader", "HAS_CHROMADB", "get_chromadb_error"]
