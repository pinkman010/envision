"""
Chroma 向量数据库工具：语料存储、检索、管理
使用本地 Ollama 嵌入模型（配置项：EMBEDDING_MODEL）
优化：批量向量化 + 并发处理
"""

import json
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from src.core_config.paths import CHROMA_DB_DIR, RAW_CORPUS_DIR
from src.core_config import get_logger
from src.core_config.settings import (
    OLLAMA_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_WORKERS,
    EMBEDDING_TIMEOUT,
)
from src.utils.exception_utils import FileProcessingException

logger = get_logger(__name__)

# ESG指标定义
ESG_INDICATORS = {
    "scope1_emission": {"name": "范围1温室气体排放量", "unit": "tCO2e"},
    "scope2_emission": {"name": "范围2温室气体排放量", "unit": "tCO2e"},
    "scope3_emission": {"name": "范围3温室气体排放量", "unit": "tCO2e"},
    "energy_intensity": {"name": "能耗强度", "unit": "GJ/MW"},
    "trir": {"name": "工伤率(TRIR)", "unit": ""},
    "ltir": {"name": "工伤率(LTIR)", "unit": ""},
    "total_employees": {"name": "员工总数", "unit": "人"},
    "renewable_energy_ratio": {"name": "可再生能源使用占比", "unit": "%"},
    "renewable_energy_mwh": {"name": "可再生能源发电量", "unit": "MWh"},
    "waste_total": {"name": "废弃物总量", "unit": "吨"},
    "waste_recycle_rate": {"name": "废弃物回收率", "unit": "%"},
    "water_consumption": {"name": "水消耗量", "unit": "m³"},
    "female_ratio": {"name": "女性员工比例", "unit": "%"},
    "rd_investment": {"name": "研发投入", "unit": "元"},
}

# 单位转换表
UNIT_CONVERSION = {
    "万吨": (10000, "吨"),
    "万吨CO2e": (10000, "tCO2e"),
    "千人次": (1000, "人"),
    "万人": (10000, "人"),
    "亿元": (100000000, "元"),
    "百万元": (1000000, "元"),
    "千万元": (10000000, "元"),
    "GWh": (1000, "MWh"),
    "万MWh": (10000, "MWh"),
}


class ChromaManager:
    """Chroma 向量数据库管理器（单例模式）"""
    
    _instance = None
    _client = None
    _corpus_collection = None
    _metrics_collection = None
    _embedding_function = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is not None:
            return
        
        try:
            import chromadb
            from chromadb.utils.embedding_functions.ollama_embedding_function import (
                OllamaEmbeddingFunction
            )
            
            # 初始化 Ollama 嵌入函数（使用配置项）
            self._embedding_function = OllamaEmbeddingFunction(
                url=OLLAMA_BASE_URL,
                model_name=EMBEDDING_MODEL,
            )
            
            # 确保目录存在
            CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
            
            # 初始化 Chroma 客户端
            self._client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
            
            # 获取或创建语料集合
            self._corpus_collection = self._client.get_or_create_collection(
                name="corpus_collection",
                embedding_function=self._embedding_function,
                metadata={"description": "ESG语料分块存储", "version": "1.0"},
            )
            
            # 获取或创建ESG指标集合
            self._metrics_collection = self._client.get_or_create_collection(
                name="esg_metrics_collection",
                embedding_function=self._embedding_function,
                metadata={"description": "ESG结构化指标存储", "version": "1.0"},
            )
            
            logger.info("ChromaManager 初始化完成")
            
        except Exception as e:
            logger.error(f"ChromaManager 初始化失败: {str(e)}")
            raise FileProcessingException(f"向量数据库初始化失败: {str(e)}") from e
    
    def _save_raw_text_to_file(
        self, 
        corpus_id: str, 
        raw_text: str, 
        fixed_text: str
    ) -> Tuple[str, str]:
        """
        保存原始文本和修复后文本到文件
        :return: (raw_text_path, fixed_text_path)
        """
        # 按日期组织目录
        now = datetime.now()
        date_dir = RAW_CORPUS_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存原始文本
        raw_path = date_dir / f"{corpus_id}_raw.txt"
        raw_path.write_text(raw_text, encoding="utf-8")
        
        # 保存修复后文本
        fixed_path = date_dir / f"{corpus_id}_fixed.txt"
        fixed_path.write_text(fixed_text, encoding="utf-8")
        
        return str(raw_path.relative_to(Path(__file__).parent.parent.parent)), \
               str(fixed_path.relative_to(Path(__file__).parent.parent.parent))
    
    def _batch_embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本向量（优化核心：批量调用 Ollama）
        :param texts: 文本列表
        :return: 向量列表
        """
        try:
            import requests
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": EMBEDDING_MODEL,
                    "input": texts,
                },
                timeout=EMBEDDING_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
            
            return result["embeddings"]
            
        except Exception as e:
            logger.error(f"批量向量化失败: {str(e)}, 批次大小: {len(texts)}")
            raise

    def _embed_with_fallback(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成向量，失败时回退到单条处理
        """
        try:
            return self._batch_embed_texts(texts)
        except Exception as e:
            logger.warning(f"批量向量化失败，回退到单条处理: {str(e)}")
            # 单条处理回退
            embeddings = []
            for text in texts:
                try:
                    emb = self._batch_embed_texts([text])
                    embeddings.append(emb[0])
                except Exception as e2:
                    logger.error(f"单条向量化失败: {str(e2)}")
                    # 返回零向量作为占位（避免整个批次失败）
                    embeddings.append([0.0] * EMBEDDING_DIMENSION)
            return embeddings

    def _generate_embeddings_parallel(
        self, 
        chunks: List[Tuple[int, int, str]]
    ) -> List[List[float]]:
        """
        并行批量生成所有分块的向量
        :return: 按 chunks 顺序的向量列表
        """
        chunk_count = len(chunks)
        if chunk_count == 0:
            return []
        
        # 提取所有文本
        texts = [chunk[2] for chunk in chunks]
        
        # 分批处理
        batches = []
        for i in range(0, chunk_count, EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + EMBEDDING_BATCH_SIZE]
            batches.append((i, batch))
        
        logger.info(f"开始批量生成向量: 总分块={chunk_count}, 批次数={len(batches)}, 批次大小={EMBEDDING_BATCH_SIZE}")
        start_time = time.time()
        
        # 并发处理批次
        batch_results = {}
        with ThreadPoolExecutor(max_workers=EMBEDDING_MAX_WORKERS) as executor:
            # 提交所有批次任务
            future_to_idx = {
                executor.submit(self._embed_with_fallback, batch): idx 
                for idx, batch in batches
            }
            
            # 收集结果
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    embeddings = future.result()
                    batch_results[idx] = embeddings
                    logger.debug(f"批次 {idx // EMBEDDING_BATCH_SIZE + 1}/{len(batches)} 完成")
                except Exception as e:
                    logger.error(f"批次 {idx} 处理失败: {str(e)}")
                    # 填充零向量
                    batch_size = len(batches[idx // EMBEDDING_BATCH_SIZE][1])
                    batch_results[idx] = [[0.0] * EMBEDDING_DIMENSION] * batch_size
        
        # 按原始顺序组装结果
        all_embeddings = []
        for i in range(0, chunk_count, EMBEDDING_BATCH_SIZE):
            all_embeddings.extend(batch_results[i])
        
        elapsed = time.time() - start_time
        logger.info(f"向量生成完成: {chunk_count} 个分块, 耗时 {elapsed:.2f} 秒, 平均 {elapsed/chunk_count:.3f} 秒/块")
        
        return all_embeddings

    def save_corpus(
        self,
        file_name: str,
        file_suffix: str,
        file_size: int,
        raw_text: str,
        fixed_text: str,
        chunks: List[Tuple[int, int, str]],
        esg_metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        保存语料到 Chroma 数据库（优化版：批量向量化）
        :return: corpus_id（文档唯一标识）
        """
        try:
            start_time = time.time()
            
            # 生成唯一文档ID
            corpus_id = f"{Path(file_name).stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 保存原始文本到文件（选项B）
            raw_text_path, fixed_text_path = self._save_raw_text_to_file(
                corpus_id, raw_text, fixed_text
            )
            
            chunk_count = len(chunks)
            
            # 准备分块数据
            documents = []
            metadatas = []
            ids = []
            
            for idx, (start, end, chunk_text) in enumerate(chunks):
                chunk_id = f"{corpus_id}_chunk_{idx}"
                ids.append(chunk_id)
                documents.append(chunk_text)
                
                metadata = {
                    # 基础信息
                    "corpus_id": corpus_id,
                    "file_name": file_name,
                    "file_suffix": file_suffix,
                    "file_size": file_size,
                    "text_length": len(fixed_text),
                    
                    # 分块信息
                    "chunk_index": idx,
                    "total_chunks": chunk_count,
                    "chunk_start": start,
                    "chunk_end": end,
                    
                    # 时间戳
                    "processed_at": datetime.now().isoformat(),
                    
                    # 文件路径（选项B）
                    "raw_text_path": raw_text_path,
                    "fixed_text_path": fixed_text_path,
                    
                    # ESG 指标标识
                    "has_esg_extraction": esg_metrics is not None,
                }
                metadatas.append(metadata)
            
            # 批量生成向量（优化核心）
            logger.info(f"开始为 {chunk_count} 个分块生成向量...")
            embeddings = self._generate_embeddings_parallel(chunks)
            
            # 批量添加到 Chroma（直接传入 embeddings，跳过自动向量化）
            logger.info(f"开始保存到 Chroma 数据库...")
            self._corpus_collection.add(
                documents=documents,
                embeddings=embeddings,  # 直接传入预生成的向量
                metadatas=metadatas,
                ids=ids,
            )
            
            # 如果有 ESG 指标，保存到指标集合
            if esg_metrics:
                self._save_esg_metrics(corpus_id, esg_metrics)
            
            total_elapsed = time.time() - start_time
            logger.info(f"语料保存成功: {corpus_id}, 分块数: {chunk_count}, 总耗时: {total_elapsed:.2f} 秒")
            return corpus_id
            
        except Exception as e:
            logger.error(f"语料保存失败: {str(e)}")
            raise FileProcessingException(f"语料保存失败: {str(e)}") from e
    
    def _save_esg_metrics(self, corpus_id: str, metrics: Dict[str, Any]) -> None:
        """保存 ESG 结构化指标"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for metric_key, metric_data in metrics.items():
                if metric_key not in ESG_INDICATORS:
                    continue
                
                metric_id = f"{corpus_id}_metric_{metric_key}"
                indicator_info = ESG_INDICATORS[metric_key]
                
                # 构建可搜索的文本描述
                value = metric_data.get("value")
                unit = metric_data.get("unit", indicator_info["unit"])
                original_text = metric_data.get("original_text", "")
                
                searchable_text = (
                    f"{indicator_info['name']}: {value} {unit}. "
                    f"原文: {original_text}"
                )
                
                documents.append(searchable_text)
                ids.append(metric_id)
                
                # 归一化数值
                normalized_value, normalized_unit = self._normalize_unit(value, unit)
                
                metadatas.append({
                    "corpus_id": corpus_id,
                    "metric_key": metric_key,
                    "metric_name": indicator_info["name"],
                    "original_value": value,
                    "original_unit": unit,
                    "normalized_value": normalized_value,
                    "normalized_unit": normalized_unit,
                    "original_text": original_text,
                    "extracted_at": datetime.now().isoformat(),
                    "confidence": metric_data.get("confidence", 1.0),
                })
            
            if documents:
                self._metrics_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
                logger.info(f"ESG指标保存成功: {corpus_id}, 指标数: {len(documents)}")
                
        except Exception as e:
            logger.error(f"ESG指标保存失败: {str(e)}")
            # ESG 指标保存失败不影响语料保存，仅记录错误
    
    def _normalize_unit(self, value: float, unit: str) -> Tuple[float, str]:
        """
        单位归一化
        :return: (normalized_value, normalized_unit)
        """
        if unit in UNIT_CONVERSION:
            factor, normalized_unit = UNIT_CONVERSION[unit]
            return value * factor, normalized_unit
        return value, unit
    
    def query_corpus_list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        查询历史语料列表（去重，返回文档级别）
        """
        try:
            # 获取所有语料（只取第一个分块的metadata）
            results = self._corpus_collection.get(
                limit=limit * 5,  # 多取一些用于去重
                offset=offset,
            )
            
            if not results["ids"]:
                return []
            
            # 按 corpus_id 去重
            seen_corpus = set()
            corpus_list = []
            
            for idx, metadata in enumerate(results["metadatas"]):
                corpus_id = metadata.get("corpus_id")
                if not corpus_id or corpus_id in seen_corpus:
                    continue
                
                seen_corpus.add(corpus_id)
                corpus_list.append({
                    "corpus_id": corpus_id,
                    "file_name": metadata.get("file_name"),
                    "file_suffix": metadata.get("file_suffix"),
                    "file_size": metadata.get("file_size"),
                    "text_length": metadata.get("text_length"),
                    "chunk_count": metadata.get("total_chunks"),
                    "processed_at": metadata.get("processed_at"),
                    "has_esg_extraction": metadata.get("has_esg_extraction", False),
                    "raw_text_path": metadata.get("raw_text_path"),
                })
                
                if len(corpus_list) >= limit:
                    break
            
            return corpus_list
            
        except Exception as e:
            logger.error(f"语料列表查询失败: {str(e)}")
            raise FileProcessingException(f"语料列表查询失败: {str(e)}") from e
    
    def get_corpus_by_id(self, corpus_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取语料详情
        """
        try:
            # 查询该文档的所有分块
            results = self._corpus_collection.get(
                where={"corpus_id": corpus_id}
            )
            
            if not results["ids"]:
                return None
            
            # 获取第一个分块的元数据
            first_metadata = results["metadatas"][0] if results["metadatas"] else {}
            
            # 读取原始文本
            raw_text = ""
            fixed_text = ""
            raw_path = first_metadata.get("raw_text_path", "")
            fixed_path = first_metadata.get("fixed_text_path", "")
            
            project_root = Path(__file__).parent.parent.parent
            if raw_path:
                raw_file = project_root / raw_path
                if raw_file.exists():
                    raw_text = raw_file.read_text(encoding="utf-8")
            
            if fixed_path:
                fixed_file = project_root / fixed_path
                if fixed_file.exists():
                    fixed_text = fixed_file.read_text(encoding="utf-8")
            
            # 组装所有分块
            chunks = []
            for idx, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
                chunks.append({
                    "chunk_index": metadata.get("chunk_index", idx),
                    "start": metadata.get("chunk_start", 0),
                    "end": metadata.get("chunk_end", 0),
                    "text": doc,
                })
            
            # 按 chunk_index 排序
            chunks.sort(key=lambda x: x["chunk_index"])
            
            return {
                "corpus_id": corpus_id,
                "file_name": first_metadata.get("file_name"),
                "file_suffix": first_metadata.get("file_suffix"),
                "file_size": first_metadata.get("file_size"),
                "text_length": first_metadata.get("text_length"),
                "chunk_count": first_metadata.get("total_chunks"),
                "processed_at": first_metadata.get("processed_at"),
                "has_esg_extraction": first_metadata.get("has_esg_extraction", False),
                "raw_text": raw_text,
                "fixed_text": fixed_text,
                "chunks": chunks,
            }
            
        except Exception as e:
            logger.error(f"语料详情查询失败: {str(e)}")
            raise FileProcessingException(f"语料详情查询失败: {str(e)}") from e
    
    def search_corpus(
        self,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索语料
        """
        try:
            results = self._corpus_collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            
            search_results = []
            for idx, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                search_results.append({
                    "corpus_id": metadata.get("corpus_id"),
                    "file_name": metadata.get("file_name"),
                    "chunk_index": metadata.get("chunk_index"),
                    "text": doc,
                    "score": 1 - distance,  # 转换为相似度分数
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"语料搜索失败: {str(e)}")
            raise FileProcessingException(f"语料搜索失败: {str(e)}") from e
    
    def get_esg_metrics_by_corpus(self, corpus_id: str) -> List[Dict[str, Any]]:
        """
        获取指定语料的 ESG 指标
        """
        try:
            results = self._metrics_collection.get(
                where={"corpus_id": corpus_id}
            )
            
            metrics = []
            for metadata in results["metadatas"]:
                metrics.append({
                    "metric_key": metadata.get("metric_key"),
                    "metric_name": metadata.get("metric_name"),
                    "original_value": metadata.get("original_value"),
                    "original_unit": metadata.get("original_unit"),
                    "normalized_value": metadata.get("normalized_value"),
                    "normalized_unit": metadata.get("normalized_unit"),
                    "confidence": metadata.get("confidence"),
                    "original_text": metadata.get("original_text"),
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"ESG指标查询失败: {str(e)}")
            return []


# 全局单例
_chroma_manager = None


def get_chroma_manager() -> ChromaManager:
    """获取 ChromaManager 单例实例"""
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager


# 便捷函数
def save_corpus_to_db(
    file_name: str,
    file_suffix: str,
    file_size: int,
    raw_text: str,
    fixed_text: str,
    chunks: List[Tuple[int, int, str]],
    esg_metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """便捷函数：保存语料到数据库"""
    manager = get_chroma_manager()
    return manager.save_corpus(
        file_name=file_name,
        file_suffix=file_suffix,
        file_size=file_size,
        raw_text=raw_text,
        fixed_text=fixed_text,
        chunks=chunks,
        esg_metrics=esg_metrics,
    )


def get_corpus_list(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """便捷函数：获取语料列表"""
    manager = get_chroma_manager()
    return manager.query_corpus_list(limit=limit, offset=offset)


def get_corpus_detail(corpus_id: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取语料详情"""
    manager = get_chroma_manager()
    return manager.get_corpus_by_id(corpus_id)


def search_corpus(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """便捷函数：搜索语料"""
    manager = get_chroma_manager()
    return manager.search_corpus(query=query, n_results=n_results)


def get_esg_metrics(corpus_id: str) -> List[Dict[str, Any]]:
    """便捷函数：获取ESG指标"""
    manager = get_chroma_manager()
    return manager.get_esg_metrics_by_corpus(corpus_id)
