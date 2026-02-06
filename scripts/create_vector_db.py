# -*- coding: utf-8 -*-
"""
【ETL 脚本】知识库构建（优化版）
修改内容：
1. [新增] tqdm 进度条 - 提升用户体验
2. [新增] 文件哈希校验 - 支持增量更新
3. [优化] 文件类型判断使用字典映射
4. [新增] 引用配置中心
"""
import os
import sys
import hashlib
import json

# === 路径补丁 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from scripts.config import DATA_PATH, VECTOR_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP
from scripts.ollama_utils import OllamaEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 尝试导入进度条（修改点：可选依赖，优雅降级）
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = lambda x, **kwargs: x  # 降级为普通迭代器

# 文件加载器映射（修改点：替代 if-elif 链）
LOADER_MAPPING = {
    '.pdf': PyPDFLoader,
    '.txt': lambda p: TextLoader(p, encoding='utf-8'),
    '.docx': UnstructuredWordDocumentLoader,
    '.doc': UnstructuredWordDocumentLoader,
}

HASH_FILE = os.path.join(VECTOR_DB_PATH, "file_hashes.json")


def get_file_hash(file_path: str) -> str:
    """计算文件 SHA-256 哈希（更安全）"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()[:32]  # 取前32位节省存储


def load_existing_hashes() -> dict:
    """加载已处理文件的哈希记录"""
    if os.path.exists(HASH_FILE):
        try:  # [ADDED] 增加异常处理，防止文件损坏导致程序崩溃
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            # [ADDED] 记录警告日志并返回空字典，而非崩溃
            print(f"⚠️  哈希文件损坏或无法读取 ({e})，将重新处理所有文件")
            return {}
    return {}


def save_hashes(hashes: dict):
    """保存哈希记录"""
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)


def main():
    print("=" * 50)
    print("📚 向量数据库生成器 (ETL 流水线)")
    print("=" * 50)
    
    # 1. 环境检查
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"❌ 数据目录不存在，已创建: {DATA_PATH}")
        print("请放入文档后重试。")
        return

    files = [f for f in os.listdir(DATA_PATH) 
             if not f.startswith('~') and os.path.isfile(os.path.join(DATA_PATH, f))]
    
    if not files:
        print(f"❌ 数据目录为空: {DATA_PATH}")
        return

    # 2. 增量检测（修改点：跳过未变化的文件）
    existing_hashes = load_existing_hashes()
    new_hashes = {}
    files_to_process = []
    
    for file in files:
        file_path = os.path.join(DATA_PATH, file)
        current_hash = get_file_hash(file_path)
        new_hashes[file] = current_hash
        
        if existing_hashes.get(file) != current_hash:
            files_to_process.append(file)
        else:
            print(f"   ⏭️ 已跳过 (无变化): {file}")
    
    if not files_to_process:
        print("\n✅ 所有文件均已处理，无需重建。")
        print(f"   如需强制重建，请删除 {VECTOR_DB_PATH} 目录")
        return

    # 3. 文档加载
    print(f"\n[Phase 1] Loading {len(files_to_process)} Documents...")
    documents = []
    
    for file in tqdm(files_to_process, desc="Loading", disable=not HAS_TQDM):
        file_path = os.path.join(DATA_PATH, file)
        ext = os.path.splitext(file)[1].lower()
        
        loader_cls = LOADER_MAPPING.get(ext)
        if not loader_cls:
            print(f"   ⚠️ Skipped: {file} (Unsupported: {ext})")
            continue
        
        try:
            loader = loader_cls(file_path) if callable(loader_cls) else loader_cls
            docs = loader.load()
            documents.extend(docs)
            print(f"   ✅ {file} ({len(docs)} pages)")
        except Exception as e:
            print(f"   ❌ {file}: {e}")

    if not documents:
        print("\n❌ 无有效文档，退出。")
        return

    # 4. 文本切分
    print(f"\n[Phase 2] Chunking ({CHUNK_SIZE} chars, {CHUNK_OVERLAP} overlap)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   ✂️ Generated {len(chunks)} chunks")

    # 5. 向量化
    print("\n[Phase 3] Embedding & Indexing...")
    embeddings = OllamaEmbeddings()
    
    try:
        # 使用 tqdm 包装（如果可用）
        if HAS_TQDM:
            print("   ⏳ Processing embeddings (this may take a while)...")
        
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH
        )
        
        # 保存哈希（修改点：记录已处理文件）
        save_hashes(new_hashes)
        
        print(f"\n🎉 构建完成!")
        print(f"   数据库路径: {VECTOR_DB_PATH}")
        print(f"   向量总数: {vectorstore._collection.count()}")
        
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        print("💡 提示: 请确认 'ollama serve' 正在运行")


if __name__ == "__main__":
    main()