"""ChromaDB 向量存储实现

提供基于 ChromaDB 的向量存储功能，支持 Ollama embedding 服务。
兼容新版和旧版 ChromaDB API。
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.esg.config import DB_DIR, MODELS, OLLAMA_TIMEOUT, OLLAMA_URL
from src.esg.utils.ollama_client import OllamaClient

# ChromaDB 可用性检查（延迟导入，避免导入时检查sqlite3版本）
HAS_CHROMADB = False
_chromadb_module = None
_Settings_class = None


def _check_chromadb():
    """运行时检查ChromaDB是否可用"""
    global HAS_CHROMADB, _chromadb_module, _Settings_class
    if HAS_CHROMADB:
        return True
    try:
        import chromadb
        from chromadb.config import Settings

        _chromadb_module = chromadb
        _Settings_class = Settings
        HAS_CHROMADB = True
        return True
    except ImportError:
        return False
    except Exception:
        # 处理其他导入错误（如sqlite3版本问题）
        return False

# 配置日志
logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB 向量存储类

    提供文档的向量化存储和相似度搜索功能。
    支持自动初始化 ChromaDB 客户端（兼容新旧 API）。

    Attributes:
        collection_name: 集合名称
        client: ChromaDB 客户端实例
        collection: ChromaDB 集合实例
        embedding: Ollama 嵌入客户端

    Example:
        >>> store = ChromaDBStore(collection="esg_docs")
        >>> store.add_documents([{"text": "ESG报告内容", "source": "report.pdf"}])
        >>> results = store.search("环境指标", top_k=3)
    """

    def __init__(
        self,
        collection: str = "esg_docs",
        embedding_model: Optional[str] = None,
        db_dir: Optional[Union[str, Path]] = None,
    ):
        """初始化 ChromaDB 存储

        Args:
            collection: 集合名称，默认为 "esg_docs"
            embedding_model: 嵌入模型名称，默认使用配置中的模型
            db_dir: 数据库目录路径，默认使用配置中的 DB_DIR
        """
        self.collection_name = collection
        self.db_dir = Path(db_dir) if db_dir else DB_DIR
        self.client: Optional[Any] = None
        self.collection: Optional[Any] = None

        # 初始化 Ollama 嵌入客户端
        model = embedding_model or MODELS.get("embedding", "nomic-embed-text")
        self.embedding = OllamaClient(model=model, url=OLLAMA_URL)
        self.embedding_timeout = OLLAMA_TIMEOUT

        # 初始化数据库（如果 ChromaDB 可用）
        if HAS_CHROMADB:
            self._init_db()
        else:
            logger.warning("ChromaDB 未安装，向量存储功能不可用")

    def _init_db(self) -> None:
        """初始化 ChromaDB 客户端和集合

        尝试使用新版 API，失败时回退到旧版 API。
        创建或获取指定的集合。
        """
        global _chromadb_module, _Settings_class
        
        # 运行时检查ChromaDB是否可用
        if not _check_chromadb():
            logger.warning("ChromaDB 不可用（可能未安装或sqlite3版本不兼容）")
            return
        
        try:
            # 确保数据库目录存在
            os.makedirs(self.db_dir, exist_ok=True)

            # 尝试新版 API (ChromaDB >= 0.4.0)
            try:
                self.client = _chromadb_module.PersistentClient(
                    path=str(self.db_dir), settings=_Settings_class(anonymized_telemetry=False)
                )
            except (AttributeError, TypeError):
                # 回退到旧版 API
                self.client = _chromadb_module.Client(
                    _Settings_class(chroma_db_impl="duckdb+parquet", persist_directory=str(self.db_dir))
                )

            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )

        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            self.client = None
            self.collection = None

    def _generate_id(self, doc: Dict[str, Any]) -> str:
        """为文档生成唯一 ID

        基于文档来源和前50个字符内容生成 MD5 哈希。

        Args:
            doc: 文档字典，包含 text 和 source 字段

        Returns:
            str: MD5 哈希值作为文档 ID
        """
        text = doc.get("text", "")
        source = doc.get("source", "unknown")
        id_string = f"{source}_{text[:50]}"
        return hashlib.md5(id_string.encode("utf-8")).hexdigest()

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """添加文档到向量存储

        将文档转换为向量并存储到 ChromaDB 中。

        Args:
            documents: 文档列表，每个文档应包含:
                - text: 文档文本内容（必需）
                - source: 文档来源（可选）
                - position: 文档位置信息（可选）
                - 其他自定义元数据字段

        Returns:
            int: 成功添加的文档数量

        Raises:
            RuntimeError: 当向量存储未初始化时
        """
        if not self.collection:
            raise RuntimeError("向量存储未初始化，无法添加文档")

        ids: List[str] = []
        embeddings: List[List[float]] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for doc in documents:
            text = doc.get("text", "")
            if not text or not text.strip():
                continue

            doc_id = self._generate_id(doc)

            try:
                # 生成嵌入向量
                emb = self.embedding.embed(text)

                ids.append(doc_id)
                embeddings.append(emb)
                texts.append(text)

                # 构建元数据
                metadata = {
                    "source": doc.get("source", "unknown"),
                    "position": doc.get("position", ""),
                }
                # 添加其他自定义元数据字段
                for key, value in doc.items():
                    if key not in ("text", "source", "position") and isinstance(
                        value, (str, int, float, bool)
                    ):
                        metadata[key] = value

                metadatas.append(metadata)

            except Exception as e:
                logger.warning(f"文档嵌入失败 [source={doc.get('source', 'unknown')}]: {e}")
                continue

        # 批量添加到 ChromaDB
        if ids:
            try:
                self.collection.add(
                    ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
                )
            except Exception as e:
                logger.error(f"批量添加文档失败: {e}")
                return 0

        return len(ids)

    def search(
        self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似文档

        将查询转换为向量，在 ChromaDB 中搜索最相似的文档。

        Args:
            query: 查询文本
            top_k: 返回结果数量，默认为 5
            filter_dict: 元数据过滤条件（可选）

        Returns:
            List[Dict]: 搜索结果列表，每个结果包含:
                - id: 文档 ID
                - text: 文档文本
                - metadata: 文档元数据
                - score: 相似度分数 (0-1，越高越相似)

        Raises:
            RuntimeError: 当向量存储未初始化时
        """
        if not self.collection:
            raise RuntimeError("向量存储未初始化，无法搜索")

        if self.collection.count() == 0:
            return []

        try:
            # 生成查询向量
            query_emb = self.embedding.embed(query)

            # 执行搜索
            n_results = min(top_k, self.collection.count())
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=n_results,
                where=filter_dict,
                include=["documents", "metadatas", "distances"],
            )

            # 格式化结果
            formatted_results: List[Dict[str, Any]] = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append(
                        {
                            "id": results["ids"][0][i],
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "score": 1 - results["distances"][0][i],  # 转换为相似度分数
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        """删除指定文档

        Args:
            doc_id: 文档 ID

        Returns:
            bool: 是否删除成功
        """
        if not self.collection:
            return False

        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def clear(self) -> bool:
        """清空集合中的所有文档

        Returns:
            bool: 是否清空成功
        """
        if not self.collection:
            return False

        try:
            self.collection.delete(where={})
            return True
        except Exception as e:
            logger.error(f"清空集合失败: {e}")
            return False

    def count(self) -> int:
        """获取集合中的文档数量

        Returns:
            int: 文档数量，如果未初始化则返回 0
        """
        if not self.collection:
            return 0
        return self.collection.count()

    def is_available(self) -> bool:
        """检查向量存储是否可用

        Returns:
            bool: ChromaDB 是否已安装且已初始化
        """
        return HAS_CHROMADB and self.collection is not None


# 别名，用于向后兼容
VectorStore = ChromaDBStore


# 导出 HAS_CHROMADB
__all__ = ["ChromaDBStore", "VectorStore", "HAS_CHROMADB"]
