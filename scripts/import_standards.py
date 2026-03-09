#!/usr/bin/env python3
"""
import_standards.py

将standards_kb.xlsx中的标准条款数据批量导入ChromaDB的standards_collection。
导入后RetrievalAgent的search_standards()即可检索到数据，
AnalystAgent的差距分析才有标准依据。

使用方法:
    python import_standards.py

依赖:
    pip install chromadb pandas openpyxl
"""

import os
import sys
import pandas as pd
import chromadb
from pathlib import Path
from typing import List, Dict, Any

# 把项目根目录加入sys.path，才能import src.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import CHROMA_DB_PERSIST_DIR, OLLAMA_BASE_URL, EMBEDDING_MODEL
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

# 配置
EXCEL_FILE = Path(__file__).parent.parent / "data" / "knowledge_base" / "standards" / "standards_kb.xlsx"
CHROMA_DB_PATH = CHROMA_DB_PERSIST_DIR   # 从.env读取，与chroma_utils.py保持一致
COLLECTION_NAME = "standards"            # 必须与chroma_utils.py一致（原为"standards_collection"）


def _get_embedding_function():
    """
    获取Ollama嵌入函数（与chroma_utils.py一致）
    
    Returns:
        OllamaEmbeddingFunction: 配置好的嵌入函数
    """
    return OllamaEmbeddingFunction(
        url=OLLAMA_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )


def init_chroma_client() -> chromadb.ClientAPI:
    """
    初始化ChromaDB客户端
    
    Returns:
        chromadb.ClientAPI: 配置好的ChromaDB客户端
    """
    # 确保数据库目录存在
    Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    
    # 创建客户端（使用新版API）
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client


def get_or_create_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """
    获取或创建standards集合
    
    Args:
        client: ChromaDB客户端
        
    Returns:
        chromadb.Collection: 标准条款集合
    """
    embedding_fn = _get_embedding_function()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,          # 与chroma_utils.py一致
        metadata={"description": "HKEX和ISSB标准条款知识库", "version": "1.0"}
    )
    return collection


def read_hkex_clauses(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    读取HKEX条款数据
    
    Args:
        df: HKEX条款DataFrame
        
    Returns:
        List[Dict]: 条款记录列表
    """
    records = []
    for _, row in df.iterrows():
        record = {
            "clause_id": str(row.get("clause_id", "")),
            "standard_name": str(row.get("standard_name", "")),
            "topic_id": str(row.get("topic_id", "")),
            "topic_taxonomy_id": str(row.get("topic_taxonomy_id", "")) if pd.notna(row.get("topic_taxonomy_id")) else "",
            "requirement_text": str(row.get("requirement_text", "")),
            "industry_applicability": str(row.get("industry_applicability", "")),
            "notes_gap": str(row.get("notes_gap", "")) if pd.notna(row.get("notes_gap")) else "",
            "notes_peer": str(row.get("notes_peer", "")) if pd.notna(row.get("notes_peer")) else "",
        }
        records.append(record)
    return records


def read_issb_clauses(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    读取ISSB条款数据
    
    Args:
        df: ISSB条款DataFrame
        
    Returns:
        List[Dict]: 条款记录列表
    """
    records = []
    for _, row in df.iterrows():
        record = {
            "clause_id": str(row.get("clause_id", "")),
            "standard_name": str(row.get("standard_name", "")),
            "topic_id": str(row.get("topic_id", "")),
            "topic_taxonomy_id": str(row.get("topic_taxonomy_id", "")) if pd.notna(row.get("topic_taxonomy_id")) else "",
            "requirement_text": str(row.get("requirement_text", "")),
            "industry_applicability": str(row.get("industry_applicability", "")),
            "notes_gap": str(row.get("notes_gap", "")) if pd.notna(row.get("notes_gap")) else "",
            "notes_peer": str(row.get("notes_peer", "")) if pd.notna(row.get("notes_peer")) else "",
        }
        records.append(record)
    return records


def import_to_chromadb(collection: chromadb.Collection, records: List[Dict[str, Any]]) -> int:
    """
    将条款记录导入ChromaDB
    
    Args:
        collection: ChromaDB集合
        records: 条款记录列表
        
    Returns:
        int: 成功导入的记录数
    """
    if not records:
        print("没有记录需要导入")
        return 0
    
    # 准备批量导入数据
    ids = []
    documents = []
    metadatas = []
    
    for record in records:
        # 使用clause_id作为唯一标识
        doc_id = f"{record['standard_name']}_{record['clause_id']}"
        ids.append(doc_id)
        
        # requirement_text是向量化的主体内容
        documents.append(record["requirement_text"])
        
        # 元数据用于检索过滤
        metadata = {
            "clause_id": record["clause_id"],
            "standard_name": record["standard_name"],
            "topic_id": record["topic_id"],
            "topic_taxonomy_id": record["topic_taxonomy_id"],
            "industry_applicability": record["industry_applicability"],
            "notes_gap": record["notes_gap"],
            "notes_peer": record["notes_peer"],
        }
        metadatas.append(metadata)
    
    # 批量添加到ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return len(records)


def verify_import(collection: chromadb.Collection) -> None:
    """
    验证导入结果
    
    Args:
        collection: ChromaDB集合
    """
    count = collection.count()
    print(f"\n验证: 集合中共有 {count} 条记录")
    
    # 测试查询
    print("\n测试查询示例 (topic_id='carbon_emission'):")
    results = collection.query(
        query_texts=["温室气体排放披露要求"],
        n_results=3,
        where={"topic_id": "carbon_emission"}
    )
    
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"][0]):
            print(f"  {i+1}. {doc_id}")
            if results["documents"] and results["documents"][0]:
                doc_preview = results["documents"][0][i][:100] + "..."
                print(f"     内容: {doc_preview}")


def main():
    """主函数"""
    print("=" * 60)
    print("标准条款知识库导入工具")
    print("=" * 60)
    
    # 检查Excel文件是否存在
    if not os.path.exists(EXCEL_FILE):
        print(f"错误: 找不到文件 {EXCEL_FILE}")
        print(f"请确保 {EXCEL_FILE} 在当前目录中")
        sys.exit(1)
    
    print(f"\n读取Excel文件: {EXCEL_FILE}")
    
    # 读取Excel文件
    try:
        excel_file = pd.ExcelFile(EXCEL_FILE)
        sheet_names = excel_file.sheet_names
        print(f"发现Sheet: {sheet_names}")
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        sys.exit(1)
    
    # 初始化ChromaDB
    print(f"\n初始化ChromaDB (路径: {CHROMA_DB_PATH})")
    client = init_chroma_client()
    collection = get_or_create_collection(client)
    
    # 清空现有数据（可选，如需增量导入请注释掉）
    existing_count = collection.count()
    if existing_count > 0:
        print(f"集合中已有 {existing_count} 条记录")
        response = input("是否清空现有数据? (y/N): ").strip().lower()
        if response == 'y':
            # 删除并重新创建集合
            client.delete_collection(COLLECTION_NAME)
            collection = get_or_create_collection(client)
            print("已清空现有数据")
    
    total_imported = 0
    
    # 导入HKEX条款
    if "HKEX条款" in sheet_names:
        print("\n" + "-" * 40)
        print("导入HKEX条款...")
        df_hkex = pd.read_excel(EXCEL_FILE, sheet_name="HKEX条款")
        print(f"  读取到 {len(df_hkex)} 条记录")
        
        records = read_hkex_clauses(df_hkex)
        count = import_to_chromadb(collection, records)
        print(f"  成功导入 {count} 条记录")
        total_imported += count
    
    # 导入ISSB条款
    if "ISSB条款" in sheet_names:
        print("\n" + "-" * 40)
        print("导入ISSB条款...")
        df_issb = pd.read_excel(EXCEL_FILE, sheet_name="ISSB条款")
        print(f"  读取到 {len(df_issb)} 条记录")
        
        records = read_issb_clauses(df_issb)
        count = import_to_chromadb(collection, records)
        print(f"  成功导入 {count} 条记录")
        total_imported += count
    
    # 验证导入
    print("\n" + "=" * 60)
    verify_import(collection)
    
    # 总结
    print("\n" + "=" * 60)
    print(f"导入完成! 共导入 {total_imported} 条记录")
    print(f"ChromaDB集合: {COLLECTION_NAME}")
    print(f"存储路径: {os.path.abspath(CHROMA_DB_PATH)}")
    print("=" * 60)
    
    print("\n下一步:")
    print("  1. RetrievalAgent可以使用search_standards()检索标准条款")
    print("  2. AnalystAgent可以基于这些标准进行差距分析")
    print("  3. AdvisorAgent可以使用notes_gap生成差距建议")
    print("  4. AdvisorAgent可以使用notes_peer生成同行对比")


if __name__ == "__main__":
    main()
