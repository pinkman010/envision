"""向量数据库服务"""

import os
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

from src.config import DB_DIR, MODELS
from src.utils.ollama import OllamaClient


class VectorStore:
    """向量存储服务"""
    
    def __init__(self, collection: str = "esg_docs"):
        self.collection_name = collection
        self.client = None
        self.collection = None
        self.embedding = OllamaClient(model=MODELS["embedding"])
        
        if HAS_CHROMADB:
            self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            
            # 尝试新版API
            try:
                self.client = chromadb.PersistentClient(
                    path=str(DB_DIR),
                    settings=Settings(anonymized_telemetry=False)
                )
            except:
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(DB_DIR)
                ))
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"向量数据库初始化失败: {e}")
    
    def add(self, documents: List[Dict]) -> int:
        """添加文档"""
        if not self.collection:
            return 0
        
        ids, embeddings, texts, metas = [], [], [], []
        
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
            
            doc_id = hashlib.md5(f"{doc.get('source', '')}_{text[:50]}".encode()).hexdigest()
            
            try:
                emb = self.embedding.embed(text)
                ids.append(doc_id)
                embeddings.append(emb)
                texts.append(text)
                metas.append({
                    "source": doc.get("source", "unknown"),
                    "position": doc.get("position", "")
                })
            except Exception as e:
                print(f"嵌入失败: {e}")
        
        if ids:
            self.collection.add(
                ids=ids, embeddings=embeddings,
                documents=texts, metadatas=metas
            )
        
        return len(ids)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索文档"""
        if not self.collection or self.collection.count() == 0:
            return []
        
        query_emb = self.embedding.embed(query)
        
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]
    
    def count(self) -> int:
        """获取文档数量"""
        return self.collection.count() if self.collection else 0
