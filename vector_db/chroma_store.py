"""ChromaDB向量数据库管理

提供文档向量化和检索功能。
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 尝试导入chromadb
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    chromadb = None
    Settings = None

from utils.ollama_utils import OllamaEmbeddings
from config import PROJECT_ROOT


class ChromaDBStore:
    """ChromaDB向量数据库管理器"""
    
    def __init__(self, collection_name: str = "esg_docs", persist_dir: Optional[str] = None):
        """初始化向量数据库
        
        Args:
            collection_name: 集合名称
            persist_dir: 数据持久化目录，默认在项目根目录的chroma_db文件夹
        """
        self.collection_name = collection_name
        self.persist_dir = persist_dir or os.path.join(PROJECT_ROOT, "chroma_db")
        self.client = None
        self.collection = None
        self.embedding_client = None
        self._initialized = False
        self._error_msg = None
        
        if not HAS_CHROMADB:
            self._error_msg = "ChromaDB未安装，请运行: pip install chromadb"
            print(f"警告: {self._error_msg}")
            return
        
        try:
            # 确保目录存在
            os.makedirs(self.persist_dir, exist_ok=True)
            
            # 初始化ChromaDB客户端（新版配置）
            try:
                # 尝试新版配置方式 (Chroma 0.4.x+)
                self.client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            except Exception:
                # 回退到旧版配置方式
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_dir,
                    anonymized_telemetry=False
                ))
            
            # 获取或创建集合
            try:
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception:
                # 如果集合存在但有问题，尝试删除重建
                try:
                    self.client.delete_collection(collection_name)
                except:
                    pass
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            
            # 初始化embedding客户端
            self.embedding_client = OllamaEmbeddings()
            self._initialized = True
            
            print(f"ChromaDB初始化完成，集合: {collection_name}，文档数: {self.collection.count()}")
            
        except Exception as e:
            self._error_msg = f"ChromaDB初始化失败: {e}"
            print(f"错误: {self._error_msg}")
    
    def _check_initialized(self):
        """检查是否已初始化"""
        if not self._initialized:
            raise RuntimeError(self._error_msg or "ChromaDB未正确初始化")
    
    def add_documents(self, documents: List[Dict[str, str]]) -> List[str]:
        """添加文档到向量数据库
        
        Args:
            documents: 文档列表，每个文档包含text, source, position等字段
            
        Returns:
            文档ID列表
        """
        self._check_initialized()
        
        if not documents:
            return []
        
        ids = []
        embeddings = []
        metadatas = []
        texts = []
        
        for doc in documents:
            # 生成唯一ID
            doc_id = hashlib.md5(
                f"{doc.get('source', '')}_{doc.get('position', '')}_{doc.get('text', '')[:50]}".encode()
            ).hexdigest()
            
            # 检查是否已存在
            try:
                existing = self.collection.get(ids=[doc_id])
                if existing and existing['ids']:
                    continue
            except:
                pass
            
            # 生成向量
            text = doc.get('text', '')
            if not text:
                continue
                
            try:
                embedding = self.embedding_client.embed_query(text)
            except Exception as e:
                print(f"生成向量失败: {e}")
                continue
            
            ids.append(doc_id)
            embeddings.append(embedding)
            texts.append(text)
            metadatas.append({
                'source': doc.get('source', 'unknown'),
                'position': doc.get('position', ''),
                'title': doc.get('title', '')[:200]
            })
        
        if ids:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            print(f"成功添加 {len(ids)} 个文档片段到向量数据库")
        
        return ids
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            相关文档列表，包含文本、来源、相似度等信息
        """
        self._check_initialized()
        
        if self.collection.count() == 0:
            return []
        
        # 生成查询向量
        query_embedding = self.embedding_client.embed_query(query)
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        # 整理结果
        documents = []
        for i in range(len(results['ids'][0])):
            doc = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'score': 1 - results['distances'][0][i]  # 转换为相似度分数
            }
            documents.append(doc)
        
        return documents
    
    def clear(self):
        """清空集合"""
        self._check_initialized()
        try:
            # 尝试删除后重建
            self.client.delete_collection(self.collection_name)
        except:
            pass
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"集合 {self.collection_name} 已清空")
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        if not self._initialized:
            return {
                'total_documents': 0,
                'collection_name': self.collection_name,
                'persist_dir': self.persist_dir,
                'status': '未初始化',
                'error': self._error_msg
            }
        
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection_name,
            'persist_dir': self.persist_dir,
            'status': '正常'
        }


def load_and_index_documents(data_dir: str, db_store: ChromaDBStore) -> int:
    """加载并索引文档
    
    Args:
        data_dir: 数据目录
        db_store: ChromaDB存储实例
        
    Returns:
        索引的文档数量
    """
    documents = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"数据目录不存在: {data_dir}")
        return 0
    
    # 加载JSON文件
    json_files = list(data_path.glob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 处理不同格式的JSON
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        text = item.get('text', item.get('content', str(item)))
                    else:
                        text = str(item)
                    
                    documents.append({
                        'text': text[:1000],  # 限制长度
                        'source': json_file.name,
                        'position': f"第{i+1}条记录",
                        'title': item.get('title', '') if isinstance(item, dict) else ''
                    })
            elif isinstance(data, dict):
                for key, value in data.items():
                    text = str(value)
                    documents.append({
                        'text': text[:1000],
                        'source': json_file.name,
                        'position': f"键: {key}",
                        'title': key
                    })
        except Exception as e:
            print(f"加载 {json_file.name} 失败: {e}")
    
    # 批量添加到数据库
    if documents:
        try:
            db_store.add_documents(documents)
        except Exception as e:
            print(f"添加文档到数据库失败: {e}")
            return 0
    
    return len(documents)


# 全局实例
_db_store = None

def get_db_store() -> Optional[ChromaDBStore]:
    """获取全局ChromaDB实例（单例模式）"""
    global _db_store
    if _db_store is None:
        _db_store = ChromaDBStore()
    return _db_store
