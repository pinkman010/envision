"""
Chroma 向量数据库工具：语料存储、检索、管理
使用本地 Ollama 嵌入模型（配置项：EMBEDDING_MODEL）
优化：批量向量化 + 并发处理

包含RAG增强提取功能：利用语料库知识库提高信息提取精准度
"""

import json
import uuid
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from src.core_config.paths import CHROMA_DB_DIR, RAW_CORPUS_DIR, ROOT_DIR
from src.core_config import get_logger
from src.core_config.settings import (
    OLLAMA_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_WORKERS,
    EMBEDDING_TIMEOUT,
    USE_RAG_ENHANCEMENT,
    RAG_EXTRACTION_TOP_K,
    RAG_EXTRACTION_THRESHOLD,
)
from src.utils.exception_utils import FileProcessingException, ValidationException
from src.utils.llm_utils import call_llm
from src.utils.config_utils import (
    load_prompt_template,
    load_esg_indicators,
    load_unit_conversions,
)

logger = get_logger(__name__)

# 加载ESG指标定义配置
_ESG_INDICATORS_CONFIG = load_esg_indicators()
ESG_INDICATORS = _ESG_INDICATORS_CONFIG.get("indicators", {})

# 加载单位转换表配置
_UNIT_CONVERSION_CONFIG = load_unit_conversions()
_UNIT_CONVERSION_RAW = _UNIT_CONVERSION_CONFIG.get("conversions", {})
UNIT_CONVERSION = {
    unit: (data["factor"], data["target_unit"])
    for unit, data in _UNIT_CONVERSION_RAW.items()
}


@dataclass
class RetrievedChunk:
    """检索到的文本块"""

    text: str
    score: float
    corpus_id: str
    file_name: str
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class ExtractionEnhancement:
    """提取增强结果"""

    original_extraction: str
    enhanced_extraction: str
    confidence_boost: float
    supporting_evidence: List[Dict[str, Any]]
    inconsistencies: List[str]
    suggestions: List[str]


class ChromaManager:
    """Chroma 向量数据库管理器（单例模式）"""

    _instance = None
    _client = None
    _corpus_collection = None
    _metrics_collection = None
    _standards_collection = None  # ESG标准条文集合（预留）
    _peer_reports_collection = None  # 同行报告案例集合（预留）
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
                OllamaEmbeddingFunction,
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

            # 获取或创建ESG标准条文集合（预留，用于RetrievalAgent检索标准要求）
            self._standards_collection = self._client.get_or_create_collection(
                name="standards",
                embedding_function=self._embedding_function,
                metadata={
                    "description": "ESG披露标准条文（ISSB/HKEX/SASB等）",
                    "version": "1.0",
                },
            )

            # 获取或创建同行报告案例集合（预留，用于RetrievalAgent检索优秀案例）
            self._peer_reports_collection = self._client.get_or_create_collection(
                name="peer_reports",
                embedding_function=self._embedding_function,
                metadata={"description": "同行业ESG报告披露案例", "version": "1.0"},
            )

            logger.info("ChromaManager 初始化完成（含standards和peer_reports预留集合）")

        except Exception as e:
            logger.error(f"ChromaManager 初始化失败: {str(e)}")
            raise FileProcessingException(f"向量数据库初始化失败: {str(e)}") from e

    def _save_raw_text_to_file(
        self, corpus_id: str, raw_text: str, fixed_text: str
    ) -> Tuple[str, str]:
        """
        保存原始文本和修复后文本到文件
        :return: (raw_text_path, fixed_text_path)
        """
        # 按日期组织目录
        now = datetime.now()
        date_dir = (
            RAW_CORPUS_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
        )
        date_dir.mkdir(parents=True, exist_ok=True)

        # 保存原始文本
        raw_path = date_dir / f"{corpus_id}_raw.txt"
        raw_path.write_text(raw_text, encoding="utf-8")

        # 保存修复后文本
        fixed_path = date_dir / f"{corpus_id}_fixed.txt"
        fixed_path.write_text(fixed_text, encoding="utf-8")

        return str(raw_path.relative_to(ROOT_DIR)), str(
            fixed_path.relative_to(ROOT_DIR)
        )

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
        self, chunks: List[Tuple[int, int, str]]
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
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            batches.append((i, batch))

        logger.info(
            f"开始批量生成向量: 总分块={chunk_count}, 批次数={len(batches)}, 批次大小={EMBEDDING_BATCH_SIZE}"
        )
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
                    logger.debug(
                        f"批次 {idx // EMBEDDING_BATCH_SIZE + 1}/{len(batches)} 完成"
                    )
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
        logger.info(
            f"向量生成完成: {chunk_count} 个分块, 耗时 {elapsed:.2f} 秒, 平均 {elapsed / chunk_count:.3f} 秒/块"
        )

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
            logger.info(
                f"语料保存成功: {corpus_id}, 分块数: {chunk_count}, 总耗时: {total_elapsed:.2f} 秒"
            )
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
                    f"{indicator_info['name']}: {value} {unit}. 原文: {original_text}"
                )

                documents.append(searchable_text)
                ids.append(metric_id)

                # 归一化数值
                normalized_value, normalized_unit = self._normalize_unit(value, unit)

                metadatas.append(
                    {
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
                    }
                )

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
                corpus_list.append(
                    {
                        "corpus_id": corpus_id,
                        "file_name": metadata.get("file_name"),
                        "file_suffix": metadata.get("file_suffix"),
                        "file_size": metadata.get("file_size"),
                        "text_length": metadata.get("text_length"),
                        "chunk_count": metadata.get("total_chunks"),
                        "processed_at": metadata.get("processed_at"),
                        "has_esg_extraction": metadata.get("has_esg_extraction", False),
                        "raw_text_path": metadata.get("raw_text_path"),
                    }
                )

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
            results = self._corpus_collection.get(where={"corpus_id": corpus_id})

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
            for idx, (doc, metadata) in enumerate(
                zip(results["documents"], results["metadatas"])
            ):
                chunks.append(
                    {
                        "chunk_index": metadata.get("chunk_index", idx),
                        "start": metadata.get("chunk_start", 0),
                        "end": metadata.get("chunk_end", 0),
                        "text": doc,
                    }
                )

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
            for idx, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                search_results.append(
                    {
                        "corpus_id": metadata.get("corpus_id"),
                        "file_name": metadata.get("file_name"),
                        "chunk_index": metadata.get("chunk_index"),
                        "text": doc,
                        "score": 1 - distance,  # 转换为相似度分数
                    }
                )

            return search_results

        except Exception as e:
            logger.error(f"语料搜索失败: {str(e)}")
            raise FileProcessingException(f"语料搜索失败: {str(e)}") from e

    def get_esg_metrics_by_corpus(self, corpus_id: str) -> List[Dict[str, Any]]:
        """
        获取指定语料的 ESG 指标
        """
        try:
            results = self._metrics_collection.get(where={"corpus_id": corpus_id})

            metrics = []
            for metadata in results["metadatas"]:
                metrics.append(
                    {
                        "metric_key": metadata.get("metric_key"),
                        "metric_name": metadata.get("metric_name"),
                        "original_value": metadata.get("original_value"),
                        "original_unit": metadata.get("original_unit"),
                        "normalized_value": metadata.get("normalized_value"),
                        "normalized_unit": metadata.get("normalized_unit"),
                        "confidence": metadata.get("confidence"),
                        "original_text": metadata.get("original_text"),
                    }
                )

            return metrics

        except Exception as e:
            logger.error(f"ESG指标查询失败: {str(e)}")
            return []

    # ==================== RAG增强提取功能 ====================

    def retrieve_for_extraction(
        self,
        query: str,
        top_k: int = None,
        score_threshold: float = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        """
        检索相关文本块（用于RAG增强提取）
        :param query: 查询文本
        :param top_k: 返回结果数量
        :param score_threshold: 相似度阈值
        :param filter_criteria: 过滤条件
        :return: 检索到的文本块列表
        """
        top_k = top_k or RAG_EXTRACTION_TOP_K
        score_threshold = score_threshold or RAG_EXTRACTION_THRESHOLD

        try:
            logger.debug(f"开始RAG检索: query='{query[:50]}...', top_k={top_k}")

            # 构建where条件
            where_clause = None
            if filter_criteria:
                where_clause = filter_criteria

            # 执行向量检索
            results = self._corpus_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause,
            )

            retrieved_chunks = []

            if results["ids"] and len(results["ids"]) > 0:
                for idx, (doc_id, doc, metadata, distance) in enumerate(
                    zip(
                        results["ids"][0],
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    # 将距离转换为相似度分数 (1 - distance)
                    score = 1 - distance

                    # 过滤低相似度结果
                    if score < score_threshold:
                        continue

                    chunk = RetrievedChunk(
                        text=doc,
                        score=score,
                        corpus_id=metadata.get("corpus_id", ""),
                        file_name=metadata.get("file_name", ""),
                        chunk_index=metadata.get("chunk_index", 0),
                        metadata=metadata,
                    )
                    retrieved_chunks.append(chunk)

            logger.info(f"RAG检索完成: 找到 {len(retrieved_chunks)} 个相关块")
            return retrieved_chunks

        except Exception as e:
            logger.error(f"RAG检索失败: {str(e)}")
            raise ValidationException(f"RAG检索失败: {str(e)}") from e

    def enhance_extraction(
        self,
        field_name: str,
        extracted_content: str,
        source_text: str,
        company_name: str = "",
        report_year: int = 0,
    ) -> ExtractionEnhancement:
        """
        增强单个字段的提取结果（RAG增强）
        :param field_name: 字段名称
        :param extracted_content: 原始提取内容
        :param source_text: 原文
        :param company_name: 企业名称
        :param report_year: 报告年份
        :return: 增强后的提取结果
        """
        if not USE_RAG_ENHANCEMENT:
            return ExtractionEnhancement(
                original_extraction=extracted_content,
                enhanced_extraction=extracted_content,
                confidence_boost=0.0,
                supporting_evidence=[],
                inconsistencies=[],
                suggestions=[],
            )

        try:
            logger.debug(f"开始RAG增强提取: {field_name}")

            # 1. 从知识库检索相关信息
            query = f"{field_name} {extracted_content} {company_name} {report_year}"
            retrieved_chunks = self.retrieve_for_extraction(query, top_k=3)

            # 2. 验证原始提取与知识库的一致性
            inconsistencies = []
            for chunk in retrieved_chunks:
                extracted_numbers = self._extract_numbers(extracted_content)
                chunk_numbers = self._extract_numbers(chunk.text)
                for num in extracted_numbers:
                    if num not in chunk_numbers:
                        inconsistencies.append(
                            f"提取的数值({num})在知识库参考文档中未找到"
                        )

            # 3. 构建增强Prompt
            try:
                enhancement_prompt = load_prompt_template(
                    "rag_extraction_enhancement_prompt"
                )
                context = self._format_retrieved_context(retrieved_chunks)

                prompt = enhancement_prompt.render(
                    field_name=field_name,
                    original_extraction=extracted_content,
                    source_text=source_text[:2000],
                    retrieved_context=context,
                    company_name=company_name,
                    report_year=report_year,
                )

                messages = [{"role": "user", "content": prompt}]
                llm_output = call_llm(messages, temperature=0.1)

                # 4. 解析增强结果
                enhancement_result = self._parse_enhancement_result(llm_output)
                enhanced_extraction = enhancement_result.get(
                    "enhanced_extraction", extracted_content
                )
                suggestions = enhancement_result.get("suggestions", [])
            except Exception as e:
                logger.warning(f"LLM增强失败: {str(e)}")
                enhanced_extraction = extracted_content
                suggestions = []

            # 5. 计算置信度提升
            confidence_boost = 0.0
            if retrieved_chunks:
                avg_score = sum(c.score for c in retrieved_chunks) / len(
                    retrieved_chunks
                )
                confidence_boost = min(avg_score * 0.1, 0.2)

            return ExtractionEnhancement(
                original_extraction=extracted_content,
                enhanced_extraction=enhanced_extraction,
                confidence_boost=confidence_boost,
                supporting_evidence=self._extract_supporting_evidence(retrieved_chunks),
                inconsistencies=inconsistencies,
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(f"RAG增强提取失败: {str(e)}")
            return ExtractionEnhancement(
                original_extraction=extracted_content,
                enhanced_extraction=extracted_content,
                confidence_boost=0.0,
                supporting_evidence=[],
                inconsistencies=[],
                suggestions=[],
            )

    def _extract_numbers(self, text: str) -> List[str]:
        """提取文本中的所有数字"""
        return re.findall(r"\d+[\.,]?\d*", text)

    def _format_retrieved_context(self, chunks: List[RetrievedChunk]) -> str:
        """格式化检索到的上下文"""
        if not chunks:
            return "无相关知识库内容"

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[参考{i}] 来源: {chunk.file_name} (相关度: {chunk.score:.1%})\n"
                f"{chunk.text[:500]}..."
            )

        return "\n\n".join(context_parts)

    def _parse_enhancement_result(self, llm_output: str) -> Dict[str, Any]:
        """解析LLM增强结果"""
        try:
            result = json.loads(llm_output)
            return result
        except Exception:
            return {
                "enhanced_extraction": llm_output.strip(),
                "suggestions": [],
            }

    def _extract_supporting_evidence(
        self, chunks: List[RetrievedChunk]
    ) -> List[Dict[str, Any]]:
        """提取支撑证据"""
        return [
            {
                "text": c.text[:200] + "...",
                "source": c.file_name,
                "relevance": round(c.score, 4),
            }
            for c in chunks[:3]
        ]

    # ==================== ESG标准条文检索（standards集合）====================

    def search_standards(
        self,
        query: str,
        n_results: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        从standards集合检索相关ESG标准条文
        供RetrievalAgent使用，识别议题时关联标准要求

        :param query: 查询文本（如议题关键词）
        :param n_results: 返回结果数量
        :param score_threshold: 相似度阈值
        :return: 检索到的标准条文列表
        """
        try:
            results = self._standards_collection.query(
                query_texts=[query],
                n_results=n_results,
            )

            search_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for idx, (doc_id, doc, metadata, distance) in enumerate(
                    zip(
                        results["ids"][0],
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    score = 1 - distance  # 转换为相似度分数
                    if score < score_threshold:
                        continue

                    search_results.append(
                        {
                            "id": doc_id,
                            "content": doc,
                            "source": metadata.get("source", "Unknown"),
                            "clause_id": metadata.get("clause_id", ""),
                            "standard_name": metadata.get("standard_name", ""),
                            "score": round(score, 4),
                            **{
                                k: v
                                for k, v in metadata.items()
                                if k not in ["source", "clause_id", "standard_name"]
                            },
                        }
                    )

            logger.info(
                f"标准条文检索完成: query='{query[:50]}...', 找到 {len(search_results)} 条"
            )
            return search_results

        except Exception as e:
            logger.error(f"标准条文检索失败: {str(e)}")
            # 预留阶段：集合为空时返回空列表，不阻断流程
            return []

    def search_peer_reports(
        self,
        query: str,
        n_results: int = 3,
        score_threshold: float = 0.5,
        filter_industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        从peer_reports集合检索同行业优秀披露案例
        供RetrievalAgent使用，为差距分析提供同行参考

        :param query: 查询文本（如议题描述）
        :param n_results: 返回结果数量
        :param score_threshold: 相似度阈值
        :param filter_industry: 可选的行业过滤
        :return: 检索到的同行案例列表
        """
        try:
            # 构建where条件（如果指定了行业）
            where_clause = None
            if filter_industry:
                where_clause = {"industry": filter_industry}

            results = self._peer_reports_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
            )

            search_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for idx, (doc_id, doc, metadata, distance) in enumerate(
                    zip(
                        results["ids"][0],
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    score = 1 - distance
                    if score < score_threshold:
                        continue

                    search_results.append(
                        {
                            "id": doc_id,
                            "content": doc,
                            "company": metadata.get("company", "Unknown"),
                            "year": metadata.get("year", ""),
                            "industry": metadata.get("industry", ""),
                            "topic": metadata.get("topic", ""),
                            "score": round(score, 4),
                            **{
                                k: v
                                for k, v in metadata.items()
                                if k not in ["company", "year", "industry", "topic"]
                            },
                        }
                    )

            logger.info(
                f"同行案例检索完成: query='{query[:50]}...', 找到 {len(search_results)} 条"
            )
            return search_results

        except Exception as e:
            logger.error(f"同行案例检索失败: {str(e)}")
            # 预留阶段：集合为空时返回空列表，不阻断流程
            return []

    def get_standards_collection_info(self) -> Dict[str, Any]:
        """获取standards集合信息（用于调试/监控）"""
        try:
            count = self._standards_collection.count()
            return {
                "name": "standards",
                "count": count,
                "status": "ready" if count > 0 else "empty (reserved)",
            }
        except Exception as e:
            return {"name": "standards", "count": 0, "status": f"error: {str(e)}"}

    def get_peer_reports_collection_info(self) -> Dict[str, Any]:
        """获取peer_reports集合信息（用于调试/监控）"""
        try:
            count = self._peer_reports_collection.count()
            return {
                "name": "peer_reports",
                "count": count,
                "status": "ready" if count > 0 else "empty (reserved)",
            }
        except Exception as e:
            return {"name": "peer_reports", "count": 0, "status": f"error: {str(e)}"}


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


def enhance_extraction_with_rag(
    field_name: str,
    extracted_content: str,
    source_text: str,
    company_name: str = "",
    report_year: int = 0,
) -> ExtractionEnhancement:
    """便捷函数：使用RAG增强提取"""
    manager = get_chroma_manager()
    return manager.enhance_extraction(
        field_name=field_name,
        extracted_content=extracted_content,
        source_text=source_text,
        company_name=company_name,
        report_year=report_year,
    )


def search_standards(
    query: str, n_results: int = 5, score_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """便捷函数：检索ESG标准条文（供RetrievalAgent使用）"""
    manager = get_chroma_manager()
    return manager.search_standards(query, n_results, score_threshold)


def search_peer_reports(
    query: str,
    n_results: int = 3,
    score_threshold: float = 0.5,
    filter_industry: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """便捷函数：检索同行报告案例（供RetrievalAgent使用）"""
    manager = get_chroma_manager()
    return manager.search_peer_reports(
        query, n_results, score_threshold, filter_industry
    )


def get_knowledge_base_info() -> Dict[str, Any]:
    """获取知识库集合状态信息（用于监控）"""
    manager = get_chroma_manager()
    return {
        "standards": manager.get_standards_collection_info(),
        "peer_reports": manager.get_peer_reports_collection_info(),
    }
