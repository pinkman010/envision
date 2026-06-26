#!/usr/bin/env python3
"""
import_peer_reports.py

将peer_reports目录下的ESG报告PDF批量导入ChromaDB的peer_reports集合。
导入后RetrievalAgent的search_peer_reports()即可检索到同行披露案例。

使用方法:
    python import_peer_reports.py

依赖:
    pip install chromadb pypdf pandas
"""

import os
import sys
import re
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader

# 把项目根目录加入sys.path，才能import src.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import CHROMA_DB_PERSIST_DIR, SILICONFLOW_API_KEY, EMBEDDING_MODEL
from src.utils.rule_match import get_rule_matcher
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction

# 配置
PEER_REPORTS_DIR = (
    Path(__file__).parent.parent / "data" / "knowledge_base" / "peer_reports"
)
CHROMA_DB_PATH = CHROMA_DB_PERSIST_DIR
COLLECTION_NAME = "peer_reports"

# 文本分块参数
CHUNK_SIZE = 2000  # 每个块的最大字符数
CHUNK_OVERLAP = 200  # 块之间的重叠字符数


def _get_embedding_function():
    """
    获取硅基流动 bge-m3 嵌入函数（与chroma_utils.py一致）
    """
    return OpenAIEmbeddingFunction(
        api_key=SILICONFLOW_API_KEY,
        model_name=EMBEDDING_MODEL,
        api_base="https://api.siliconflow.cn/v1",
    )


def init_chroma_client() -> chromadb.ClientAPI:
    """初始化ChromaDB客户端"""
    Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client


def get_or_create_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """获取或创建peer_reports集合"""
    embedding_fn = _get_embedding_function()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "同行业ESG报告披露案例", "version": "1.0"},
    )
    return collection


def parse_filename(filename: str) -> Dict[str, str]:
    """
    从文件名解析公司名、年份和语言
    文件命名格式: {company}_{year}_{lang}.pdf
    例如: Envision Energy 2021-zh.pdf, Goldwind_2022_en.pdf
    """
    name_without_ext = Path(filename).stem

    # 尝试匹配 "公司名 年份-语言" 或 "公司名_年份_语言" 格式
    # 模式1: Envision Energy 2021-zh
    pattern1 = r"^(.+?)\s+(\d{4})[-_](zh|en)$"
    match = re.match(pattern1, name_without_ext, re.IGNORECASE)
    if match:
        company = match.group(1).strip()
        year = match.group(2)
        lang = match.group(3).lower()
        return {"company": company, "year": year, "lang": lang}

    # 模式2: 公司名_年份_语言（下划线分隔）
    pattern2 = r"^(.+?)_(\d{4})[-_](zh|en)$"
    match = re.match(pattern2, name_without_ext, re.IGNORECASE)
    if match:
        company = match.group(1).strip()
        year = match.group(2)
        lang = match.group(3).lower()
        return {"company": company, "year": year, "lang": lang}

    # 无法解析时返回默认值
    return {"company": name_without_ext, "year": "unknown", "lang": "unknown"}


def extract_text_from_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> str:
    """
    从PDF提取文本

    Args:
        pdf_path: PDF文件路径
        max_pages: 最大提取页数（用于测试，None表示全部）

    Returns:
        提取的文本内容
    """
    try:
        reader = PdfReader(str(pdf_path))
        text_parts = []

        pages_to_read = max_pages if max_pages else len(reader.pages)

        for i in range(pages_to_read):
            page = reader.pages[i]
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n".join(text_parts)
    except Exception as e:
        print(f"  提取PDF文本失败 {pdf_path.name}: {e}")
        return ""


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    将文本分块

    Args:
        text: 原始文本
        chunk_size: 块大小
        overlap: 重叠大小

    Returns:
        文本块列表
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 尝试在句子边界切分
        if end < len(text):
            # 找最后一个句号或换行
            last_period = max(chunk.rfind("。"), chunk.rfind("."), chunk.rfind("\n"))
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append(chunk)
        start = end - overlap

    return chunks


def process_pdf(
    pdf_path: Path, max_pages: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    处理单个PDF文件，提取文本并分块

    Args:
        pdf_path: PDF文件路径
        max_pages: 最大提取页数

    Returns:
        记录列表
    """
    # 解析文件名
    file_info = parse_filename(pdf_path.name)

    # 提取文本
    print(f"  提取文本: {pdf_path.name} ...")
    full_text = extract_text_from_pdf(pdf_path, max_pages)

    if not full_text.strip():
        print(f"  警告: {pdf_path.name} 无法提取文本或文本为空")
        return []

    # 分块
    chunks = chunk_text(full_text)

    if not chunks:
        print(f"  警告: {pdf_path.name} 文本分块失败")
        return []

    print(f"  提取到 {len(chunks)} 个文本块，开始打标议题...")

    # 初始化 RuleMatcher，对每个 chunk 打 topic 标签
    matcher = get_rule_matcher()

    # 生成记录
    records = []
    for i, chunk in enumerate(chunks):
        matched = matcher.match_topic(chunk)
        topic_id = matched[0]["topic_id"] if matched else "unknown"

        record = {
            "company": file_info["company"],
            "year": file_info["year"],
            "lang": file_info["lang"],
            "industry": "新能源",
            "topic": topic_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text": chunk,
        }
        records.append(record)

    return records


def import_to_chromadb(
    collection: chromadb.Collection, records: List[Dict[str, Any]]
) -> int:
    """
    将记录导入ChromaDB

    Args:
        collection: ChromaDB集合
        records: 记录列表

    Returns:
        成功导入的记录数
    """
    if not records:
        return 0

    # 批量导入（每批100条）
    batch_size = 100
    total_imported = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]

        ids = []
        documents = []
        metadatas = []

        for record in batch:
            # 公司名空格替换为"-"，统一小写，避免 ChromaDB ID 含空格
            company_slug = record["company"].replace(" ", "-").lower()
            doc_id = f"{company_slug}_{record['year']}_{record['lang']}_chunk{record['chunk_index']}"
            ids.append(doc_id)

            # 文本内容作为向量化主体
            documents.append(record["text"])

            # 元数据
            metadata = {
                "company": record["company"],
                "year": record["year"],
                "lang": record["lang"],
                "industry": record["industry"],
                "topic": record["topic"],
                "chunk_index": record["chunk_index"],
                "total_chunks": record["total_chunks"],
            }
            metadatas.append(metadata)

        try:
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
            total_imported += len(batch)
        except Exception as e:
            print(f"  批量导入失败 (批次 {i // batch_size + 1}): {e}")

    return total_imported


def verify_import(collection: chromadb.Collection) -> None:
    """验证导入结果"""
    count = collection.count()
    print(f"\n验证: 集合中共有 {count} 条记录")

    # 按公司统计
    try:
        # 获取所有元数据
        results = collection.get()
        if results and results["metadatas"]:
            companies = set(m.get("company", "unknown") for m in results["metadatas"])
            print(f"涉及公司: {', '.join(sorted(companies))}")
    except Exception as e:
        print(f"  统计失败: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="导入同行ESG报告到ChromaDB")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="每个PDF最大提取页数（用于测试，默认全部）",
    )
    parser.add_argument("--dry-run", action="store_true", help="仅扫描文件，不实际导入")
    args = parser.parse_args()

    print("=" * 60)
    print("同行ESG报告导入工具")
    print("=" * 60)

    # 检查目录
    if not PEER_REPORTS_DIR.exists():
        print(f"错误: 目录不存在 {PEER_REPORTS_DIR}")
        sys.exit(1)

    # 查找所有PDF文件
    pdf_files = list(PEER_REPORTS_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"错误: 在 {PEER_REPORTS_DIR} 中未找到PDF文件")
        sys.exit(1)

    print(f"\n找到 {len(pdf_files)} 个PDF文件:")
    for pf in pdf_files:
        print(f"  - {pf.name}")

    if args.dry_run:
        print("\n[dry-run 模式] 仅扫描文件，不实际导入")
        return

    # 初始化ChromaDB
    print(f"\n初始化ChromaDB (路径: {CHROMA_DB_PATH})")
    client = init_chroma_client()
    collection = get_or_create_collection(client)

    # 清空现有数据
    existing_count = collection.count()
    if existing_count > 0:
        print(f"集合中已有 {existing_count} 条记录")
        response = input("是否清空现有数据? (y/N): ").strip().lower()
        if response == "y":
            client.delete_collection(COLLECTION_NAME)
            collection = get_or_create_collection(client)
            print("已清空现有数据")

    total_imported = 0
    total_chunks = 0

    # 处理每个PDF
    for pdf_path in pdf_files:
        print(f"\n处理: {pdf_path.name}")

        # 解析文件名
        file_info = parse_filename(pdf_path.name)
        print(
            f"  公司: {file_info['company']}, 年份: {file_info['year']}, 语言: {file_info['lang']}"
        )

        # 处理PDF
        records = process_pdf(pdf_path, max_pages=args.max_pages)

        if records:
            # 导入到ChromaDB
            count = import_to_chromadb(collection, records)
            total_imported += count
            total_chunks += len(records)
            print(f"  成功导入 {count} 条记录")

    # 验证
    print("\n" + "=" * 60)
    verify_import(collection)

    # 总结
    print("\n" + "=" * 60)
    print(f"导入完成!")
    print(f"  处理PDF文件: {len(pdf_files)} 个")
    print(f"  总文本块: {total_chunks} 个")
    print(f"  成功导入: {total_imported} 条")
    print(f"ChromaDB集合: {COLLECTION_NAME}")
    print(f"存储路径: {os.path.abspath(CHROMA_DB_PATH)}")
    print("=" * 60)

    print("\n下一步:")
    print("  1. RetrievalAgent可以使用search_peer_reports()检索同行案例")
    print("  2. AnalystAgent可以基于同行披露进行差距对比")


if __name__ == "__main__":
    main()
