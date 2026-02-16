"""ChromaDB 向量存储实现

提供基于 ChromaDB 的向量存储功能，支持 Ollama embedding 服务。
兼容新版和旧版 ChromaDB API。
"""

# 修复SQLite版本问题：在导入chromadb之前替换sqlite3
try:
    import sys

    import pysqlite3

    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from src.esg.config import DB_DIR, MODELS, OLLAMA_TIMEOUT, OLLAMA_URL
from src.esg.utils.ollama_client import OllamaClient

# ChromaDB 可用性检查（延迟导入，避免导入时检查sqlite3版本）
HAS_CHROMADB = False
_chromadb_module = None
_Settings_class = None
_CHROMADB_ERROR = None


def _check_chromadb():
    """运行时检查ChromaDB是否可用"""
    global HAS_CHROMADB, _chromadb_module, _Settings_class, _CHROMADB_ERROR

    # 如果已经成功过，直接返回
    if HAS_CHROMADB:
        return True

    try:
        import chromadb
        from chromadb.config import Settings

        _chromadb_module = chromadb
        _Settings_class = Settings

        # 不再测试初始化，直接标记为可用
        # 真正的初始化在 _init_db() 中进行
        HAS_CHROMADB = True
        _CHROMADB_ERROR = None
        return True
    except ImportError as e:
        _CHROMADB_ERROR = f"未安装: {str(e)}"
        HAS_CHROMADB = False
        return False
    except Exception as e:
        _CHROMADB_ERROR = str(e)[:100]
        HAS_CHROMADB = False
        return False


def get_chromadb_error():
    """获取ChromaDB的错误信息"""
    return _CHROMADB_ERROR


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

        # 初始化 Ollama 嵌入客户端（修复：传递超时配置）
        model = embedding_model or MODELS.get("embedding", "nomic-embed-text")
        self.embedding = OllamaClient(model=model, url=OLLAMA_URL, timeout=OLLAMA_TIMEOUT)
        self.embedding_timeout = OLLAMA_TIMEOUT

        # 运行时检查 ChromaDB 是否可用（修复：先检查再初始化）
        if _check_chromadb():
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
            # 清理旧版本的整个数据库目录（兼容性问题）
            import shutil
            import time

            if self.db_dir.exists():
                try:
                    # Windows文件锁定解决：先关闭可能的数据库连接
                    self.client = None
                    self.collection = None
                    time.sleep(0.5)  # 等待文件句柄释放

                    # 尝试删除，失败则重试一次
                    try:
                        shutil.rmtree(self.db_dir)
                        logger.info(f"已删除旧数据库目录: {self.db_dir}")
                    except Exception as e_first:
                        time.sleep(1)  # 等待更长时间
                        try:
                            shutil.rmtree(self.db_dir)
                            logger.info(f"已删除旧数据库目录（重试成功）: {self.db_dir}")
                        except Exception as e_retry:
                            logger.warning(f"无法删除旧数据库目录，将尝试使用现有数据库: {e_retry}")
                except Exception as e:
                    logger.warning(f"无法删除旧数据库目录，将尝试使用现有数据库: {e}")

            # 如果目录不存在，创建新目录
            if not self.db_dir.exists():
                os.makedirs(self.db_dir, exist_ok=True)

            # 尝试新版 API (ChromaDB >= 0.4.0)
            try:
                self.client = _chromadb_module.PersistentClient(
                    path=str(self.db_dir), settings=_Settings_class(anonymized_telemetry=False)
                )
            except (AttributeError, TypeError):
                # 回退到旧版 API
                self.client = _chromadb_module.Client(
                    _Settings_class(
                        chroma_db_impl="duckdb+parquet", persist_directory=str(self.db_dir)
                    )
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

        基于文档来源、前100个字符内容和位置信息生成 MD5 哈希。
        修复：增加哈希基准长度，添加位置信息，降低冲突风险。

        Args:
            doc: 文档字典，包含 text、source 和 position 字段

        Returns:
            str: MD5 哈希值作为文档 ID
        """
        text = doc.get("text", "")
        source = doc.get("source", "unknown")
        position = doc.get("position", "")
        # 修复1：增加哈希基准到100字符，添加位置信息
        id_string = f"{source}_{position}_{text[:100]}"
        return hashlib.md5(id_string.encode("utf-8")).hexdigest()

    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> int:
        """添加文档到向量存储

        将文档转换为向量并存储到 ChromaDB 中。
        修复：添加批量大小限制，避免内存溢出。

        Args:
            documents: 文档列表，每个文档应包含:
                - text: 文档文本内容（必需）
                - source: 文档来源（可选）
                - position: 文档位置信息（可选）
                - 其他自定义元数据字段
            batch_size: 每批处理的文档数量，默认100

        Returns:
            int: 成功添加的文档数量

        Raises:
            RuntimeError: 当向量存储未初始化时
        """
        # 尝试重新初始化（如果之前失败）
        if not self.collection:
            logger.warning("向量存储未初始化，尝试重新初始化...")
            self._init_db()

        if not self.collection:
            raise RuntimeError("向量存储未初始化，无法添加文档")

        total_added = 0

        # 修复2：分批处理，避免大内存占用
        for batch_start in range(0, len(documents), batch_size):
            batch = documents[batch_start : batch_start + batch_size]
            added = self._add_batch(batch)
            total_added += added
            logger.debug(f"已处理批次 {batch_start//batch_size + 1}, 添加 {added} 个文档")

        return total_added

    def _add_batch(self, documents: List[Dict[str, Any]]) -> int:
        """添加一批文档（内部方法）

        优化：使用列表推导式和生成器表达式替代嵌套循环，提高性能。
        """

        # 使用生成器表达式过滤空文档
        def process_document(doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """处理单个文档，返回处理结果或None"""
            text = doc.get("text", "")
            if not text or not text.strip():
                return None

            doc_id = self._generate_id(doc)

            try:
                # 生成嵌入向量
                emb = self.embedding.embed(text)

                # 构建元数据
                metadata = {
                    "source": doc.get("source", "unknown"),
                    "position": doc.get("position", ""),
                }
                # 添加其他自定义元数据字段（使用字典推导式）
                metadata.update(
                    {
                        key: value
                        for key, value in doc.items()
                        if key not in ("text", "source", "position")
                        and isinstance(value, (str, int, float, bool))
                    }
                )

                return {"id": doc_id, "embedding": emb, "text": text, "metadata": metadata}

            except (OSError, RuntimeError, ValueError) as e:
                logger.warning(f"文档嵌入失败 [source={doc.get('source', 'unknown')}]: {e}")
                return None
            except Exception as e:
                logger.warning(f"文档嵌入失败 [source={doc.get('source', 'unknown')}]: {e}")
                return None

        # 使用列表推导式处理文档
        processed_docs = [
            result for result in (process_document(doc) for doc in documents) if result is not None
        ]

        if not processed_docs:
            return 0

        # 批量添加到 ChromaDB
        try:
            self.collection.add(
                ids=[d["id"] for d in processed_docs],
                embeddings=[d["embedding"] for d in processed_docs],
                documents=[d["text"] for d in processed_docs],
                metadatas=[d["metadata"] for d in processed_docs],
            )
        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            return 0

        return len(processed_docs)

    def add_document(self, text: str, source: str = "unknown", **metadata) -> Optional[str]:
        """添加单个文档（便捷方法）

        Args:
            text: 文档文本
            source: 文档来源
            **metadata: 其他元数据

        Returns:
            str: 文档ID，失败返回None
        """
        doc = {"text": text, "source": source, **metadata}
        count = self.add_documents([doc])
        return self._generate_id(doc) if count > 0 else None

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
        """
        # 尝试重新初始化（如果之前失败）
        if not self.collection:
            logger.warning("向量存储未初始化，尝试重新初始化...")
            self._init_db()

        if not self.collection:
            logger.error("向量存储初始化失败")
            return []

        if self.collection.count() == 0:
            return []

        try:
            # 生成查询向量
            query_emb = self.embedding.embed(query)

            # 执行搜索
            total_docs = self.collection.count()
            n_results = min(top_k, total_docs)

            # 修复3：如果请求数量大于实际数量，记录警告
            if top_k > total_docs:
                logger.warning(f"请求 top_k={top_k} 但知识库只有 {total_docs} 个文档，将返回全部")
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
            # 修复4：记录详细错误信息，方便排查
            logger.error(f"搜索失败: {e}", exc_info=True)
            # 根据错误类型返回不同信息
            if "embedding" in str(e).lower():
                logger.error("嵌入生成失败，请检查Ollama服务状态")
            elif "connection" in str(e).lower():
                logger.error("连接失败，请检查网络或ChromaDB服务")
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

    def auto_load_from_directory(self, directory: str, force_reload: bool = False) -> int:
        """自动从目录加载所有PDF文件并向量化

        Args:
            directory: 要扫描的目录路径
            force_reload: 是否强制重新加载（忽略已有文档）

        Returns:
            int: 成功加载的文档数量
        """
        from pathlib import Path

        from src.esg.vector_store.document_loader import DocumentLoader

        # 如果不强制重载且已有文档，返回0
        if not force_reload and self.collection.count() > 0:
            logger.info(f"知识库已有 {self.collection.count()} 个文档，跳过加载")
            return 0

        dir_path = Path(directory)

        # 如果是相对路径，转换为绝对路径
        if not dir_path.is_absolute():
            from src.esg.config import PROJECT_ROOT

            dir_path = PROJECT_ROOT / directory

        if not dir_path.exists():
            logger.warning(f"目录不存在: {dir_path}")
            return 0

        # 获取所有PDF文件
        pdf_files = list(dir_path.glob("*.pdf"))
        if not pdf_files:
            logger.info(f"目录中没有PDF文件: {dir_path}")
            return 0

        logger.info(f"找到 {len(pdf_files)} 个PDF文件，开始向量化...")

        # 创建不指定data_dir的加载器，这样load_pdf不会重复添加data路径
        loader = DocumentLoader(data_dir=None)
        total_added = 0

        for pdf_file in pdf_files:
            try:
                logger.info(f"正在处理: {pdf_file.name}")
                # 直接使用绝对路径
                chunks = loader.load_pdf(str(pdf_file.absolute()))
                if chunks:
                    count = self.add_documents(chunks)
                    total_added += count
                    logger.info(f"已添加 {count} 个文档片段: {pdf_file.name}")
            except Exception as e:
                logger.error(f"处理文件失败 {pdf_file.name}: {e}")
                continue

        logger.info(f"自动加载完成，共添加 {total_added} 个文档")
        return total_added


# 别名，用于向后兼容
VectorStore = ChromaDBStore


# 导出
__all__ = ["ChromaDBStore", "VectorStore", "HAS_CHROMADB", "get_chromadb_error"]
