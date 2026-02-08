"""文档加载器

提供从多种来源加载和预处理文档的功能，包括:
- 从 data 目录加载 JSON 文件
- 解析 PDF 文本
- 文档分块处理
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass

from src.esg.config import DATA_DIR

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """文档块数据类
    
    Attributes:
        text: 文本内容
        source: 文档来源
        chunk_index: 块索引
        total_chunks: 总块数
        metadata: 附加元数据
    """
    text: str
    source: str
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any]


class DocumentLoader:
    """文档加载器
    
    支持加载 JSON 文件、解析 PDF 文本，并进行智能分块处理。
    
    Example:
        >>> loader = DocumentLoader()
        >>> # 加载 JSON 文件
        >>> docs = loader.load_json("data/extracted_esg_data.json")
        >>> # 解析 PDF
        >>> pdf_docs = loader.load_pdf("data/report.pdf")
        >>> # 分块处理
        >>> chunks = loader.chunk_documents(docs, chunk_size=500, overlap=50)
    """
    
    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        """初始化文档加载器
        
        Args:
            data_dir: 数据目录路径，默认使用配置中的 DATA_DIR
        """
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
    
    def load_json(
        self, 
        filepath: Union[str, Path],
        text_field: str = "text",
        source_field: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """从 JSON 文件加载文档
        
        支持加载 JSON 对象列表或包含文档列表的对象。
        
        Args:
            filepath: JSON 文件路径（相对 data 目录或绝对路径）
            text_field: 文本内容字段名，默认为 "text"
            source_field: 来源字段名，如果为 None 则使用文件名
            
        Returns:
            List[Dict]: 文档列表，每个文档包含 text 和 source 字段
            
        Raises:
            FileNotFoundError: 当文件不存在时
            json.JSONDecodeError: 当 JSON 格式无效时
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"JSON 文件不存在: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        documents: List[Dict[str, Any]] = []
        
        # 处理不同类型的 JSON 结构
        if isinstance(data, list):
            # 直接是列表
            items = data
        elif isinstance(data, dict):
            # 尝试找到列表字段
            if "documents" in data:
                items = data["documents"]
            elif "data" in data:
                items = data["data"]
            elif "items" in data:
                items = data["items"]
            else:
                # 单文档对象
                items = [data]
        else:
            items = []
        
        # 转换为统一格式
        for i, item in enumerate(items):
            if isinstance(item, str):
                # 简单字符串列表
                doc = {"text": item, "source": str(path)}
            elif isinstance(item, dict):
                # 字典对象
                doc = dict(item)
                
                # 提取文本字段
                if text_field in item:
                    doc["text"] = item[text_field]
                elif "content" in item:
                    doc["text"] = item["content"]
                
                # 设置来源
                if source_field and source_field in item:
                    doc["source"] = item[source_field]
                elif "source" not in doc:
                    doc["source"] = str(path)
            else:
                continue
            
            if doc.get("text"):
                documents.append(doc)
        
        return documents
    
    def load_jsonl(self, filepath: Union[str, Path]) -> List[Dict[str, Any]]:
        """从 JSONL 文件加载文档
        
        Args:
            filepath: JSONL 文件路径
            
        Returns:
            List[Dict]: 文档列表
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"JSONL 文件不存在: {path}")
        
        documents: List[Dict[str, Any]] = []
        
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        doc = dict(item)
                        if "text" not in doc and "content" in doc:
                            doc["text"] = doc["content"]
                        if "source" not in doc:
                            doc["source"] = f"{path}#{line_num}"
                        
                        if doc.get("text"):
                            documents.append(doc)
                except json.JSONDecodeError:
                    continue
        
        return documents
    
    def load_pdf(
        self, 
        filepath: Union[str, Path],
        extractor: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """加载 PDF 文档
        
        使用项目中的 PDFExtractor 解析 PDF 文本。
        
        Args:
            filepath: PDF 文件路径
            extractor: 可选的 PDF 提取器实例，如果为 None 则尝试创建
            
        Returns:
            List[Dict]: 文档列表，每页作为一个文档
            
        Raises:
            FileNotFoundError: 当文件不存在时
            ImportError: 当 PDF 提取库未安装时
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {path}")
        
        # 尝试使用项目中已有的 PDFExtractor
        if extractor is None:
            try:
                from src.esg.extraction.pdf_extractor import PDFExtractor
                extractor = PDFExtractor()
            except ImportError:
                raise ImportError(
                    "PDF 提取库未安装，请安装: pip install pdfplumber 或 PyPDF2"
                )
        
        # 提取内容
        content = extractor.extract(path)
        
        documents: List[Dict[str, Any]] = []
        
        # 每页作为一个文档
        for i, page_text in enumerate(content.pages, 1):
            if page_text.strip():
                documents.append({
                    "text": page_text.strip(),
                    "source": str(path),
                    "position": f"page_{i}",
                    "page_number": i,
                    "total_pages": content.metadata.total_pages,
                    "company": content.metadata.company,
                    "year": content.metadata.year
                })
        
        return documents
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n"
    ) -> List[DocumentChunk]:
        """将文档分块处理
        
        使用递归字符分割策略，优先在段落、句子边界处分割。
        
        Args:
            documents: 文档列表
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separator: 主要分隔符
            
        Returns:
            List[DocumentChunk]: 分块后的文档块列表
        """
        chunks: List[DocumentChunk] = []
        
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
            
            source = doc.get("source", "unknown")
            
            # 分割文档
            text_chunks = self._split_text(
                text, 
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap,
                separator=separator
            )
            
            total = len(text_chunks)
            for i, chunk_text in enumerate(text_chunks):
                # 复制原始元数据（排除 text）
                metadata = {k: v for k, v in doc.items() if k != "text"}
                
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    source=source,
                    chunk_index=i,
                    total_chunks=total,
                    metadata=metadata
                ))
        
        return chunks
    
    def _split_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        separator: str = "\n"
    ) -> List[str]:
        """分割文本为块
        
        使用递归字符分割，优先在段落、句子边界处分割。
        
        Args:
            text: 要分割的文本
            chunk_size: 块大小
            chunk_overlap: 重叠大小
            separator: 分隔符
            
        Returns:
            List[str]: 文本块列表
        """
        # 清理文本
        text = text.strip()
        if not text:
            return []
        
        # 如果文本长度小于块大小，直接返回
        if len(text) <= chunk_size:
            return [text]
        
        chunks: List[str] = []
        
        # 定义分隔符优先级（从粗到细）
        separators = ["\n\n", "\n", "。", "；", "，", " ", ""]
        if separator not in separators:
            separators.insert(0, separator)
        
        def recursive_split(t: str, sep_idx: int) -> List[str]:
            """递归分割文本"""
            if len(t) <= chunk_size or sep_idx >= len(separators):
                return [t] if t else []
            
            sep = separators[sep_idx]
            if not sep:
                # 最后按字符分割
                result: List[str] = []
                for i in range(0, len(t), chunk_size - chunk_overlap):
                    result.append(t[i:i + chunk_size])
                return result
            
            parts = t.split(sep)
            if len(parts) == 1:
                # 当前分隔符无效，尝试下一个
                return recursive_split(t, sep_idx + 1)
            
            # 合并部分以达到块大小
            current_chunk = ""
            result = []
            
            for part in parts:
                # 恢复分隔符
                part_with_sep = part + sep if part else ""
                
                if len(current_chunk) + len(part_with_sep) <= chunk_size:
                    current_chunk += part_with_sep
                else:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    
                    # 处理剩余重叠
                    if chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-chunk_overlap:]
                        current_chunk = overlap_text + part_with_sep
                    else:
                        current_chunk = part_with_sep
                    
                    # 如果单部分超过块大小，需要进一步分割
                    if len(current_chunk) > chunk_size:
                        result.extend(recursive_split(current_chunk, sep_idx + 1))
                        current_chunk = ""
            
            if current_chunk:
                result.append(current_chunk.strip())
            
            return result
        
        return recursive_split(text, 0)
    
    def load_directory(
        self,
        directory: Optional[Union[str, Path]] = None,
        pattern: str = "*.json",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """加载目录中的所有匹配文件
        
        Args:
            directory: 目录路径，默认为 data 目录
            pattern: 文件匹配模式
            recursive: 是否递归子目录
            
        Returns:
            List[Dict]: 所有文档的合并列表
        """
        dir_path = Path(directory) if directory else self.data_dir
        
        if not dir_path.exists():
            return []
        
        documents: List[Dict[str, Any]] = []
        
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        for file_path in files:
            try:
                if file_path.suffix.lower() == ".json":
                    docs = self.load_json(file_path)
                elif file_path.suffix.lower() == ".jsonl":
                    docs = self.load_jsonl(file_path)
                else:
                    continue
                
                documents.extend(docs)
            except Exception as e:
                logger.warning(f"加载文件失败 [{file_path}]: {e}")
                continue
        
        return documents
    
    def _resolve_path(self, filepath: Union[str, Path]) -> Path:
        """解析文件路径
        
        如果路径不是绝对路径，则相对于 data 目录解析。
        
        Args:
            filepath: 文件路径
            
        Returns:
            Path: 解析后的绝对路径
        """
        path = Path(filepath)
        if not path.is_absolute():
            path = self.data_dir / path
        return path


def load_documents_for_rag(
    data_dir: Optional[Union[str, Path]] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """便捷函数：加载并分块处理所有文档
    
    Args:
        data_dir: 数据目录
        chunk_size: 分块大小
        chunk_overlap: 重叠大小
        
    Returns:
        List[Dict]: 分块后的文档列表
    """
    loader = DocumentLoader(data_dir)
    
    # 加载所有 JSON 文件
    documents = loader.load_directory(pattern="*.json")
    documents.extend(loader.load_directory(pattern="*.jsonl"))
    
    # 分块处理
    chunks = loader.chunk_documents(documents, chunk_size, chunk_overlap)
    
    # 转换为普通字典列表
    return [
        {
            "text": chunk.text,
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            **chunk.metadata
        }
        for chunk in chunks
    ]


__all__ = ["DocumentLoader", "DocumentChunk", "load_documents_for_rag"]
