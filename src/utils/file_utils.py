"""
文件处理工具：PDF/Word解析、文本分块、文件保存
无业务耦合，仅做文件操作
"""

import re
from pathlib import Path
from typing import List, Tuple

from src.core_config.settings import MAX_FILE_SIZE, CHUNK_SIZE, CHUNK_OVERLAP
from src.utils.exception_utils import FileProcessingException
import io


def validate_file(file_path: Path) -> None:
    """
    校验文件合法性（大小、格式）
    :param file_path: 文件路径
    :raises FileProcessingException: 校验失败时抛出
    """
    if not file_path.exists():
        raise FileProcessingException(f"文件不存在: {file_path}")
    if file_path.stat().st_size > MAX_FILE_SIZE:
        raise FileProcessingException(f"文件大小超过限制（最大{MAX_FILE_SIZE/1024/1024}MB）")
    if file_path.suffix.lower() not in [".pdf", ".docx", ".doc", ".xlsx", ".xls"]:
        raise FileProcessingException(f"不支持的文件格式: {file_path.suffix}")


def extract_text_from_pdf(file_path: Path) -> str:
    """
    从PDF提取纯文本
    :param file_path: PDF文件路径
    :return: 纯文本内容
    """
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        # 简单的文本清洗（去除多余空白）
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        raise FileProcessingException(f"PDF解析失败: {str(e)}", original_exception=e) from e


def extract_text_from_docx(file_path: Path) -> str:
    """
    从Word提取纯文本
    :param file_path: Word文件路径
    :return: 纯文本内容
    """
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        raise FileProcessingException(f"Word解析失败: {str(e)}", original_exception=e) from e


def extract_text_from_excel(file_path: Path) -> str:
    """
    从Excel文件提取文本（将所有sheet转换为文本表格）
    :param file_path: Excel文件路径
    :return: 纯文本内容
    """
    try:
        import pandas as pd
        
        # 读取所有sheet
        excel_file = pd.ExcelFile(file_path)
        text_parts = []
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # 添加sheet标题
            text_parts.append(f"\n=== Sheet: {sheet_name} ===\n")
            
            # 将DataFrame转换为文本表格格式
            if not df.empty:
                # 表头
                headers = " | ".join(str(col) for col in df.columns)
                text_parts.append(headers)
                text_parts.append("-" * len(headers))
                
                # 数据行
                for _, row in df.iterrows():
                    row_text = " | ".join(str(val) for val in row.values)
                    text_parts.append(row_text)
        
        text = "\n".join(text_parts)
        # 清洗多余空白
        text = re.sub(r"\s+", " ", text).strip()
        return text
        
    except Exception as e:
        raise FileProcessingException(f"Excel解析失败: {str(e)}", original_exception=e) from e


def extract_text(file_path: Path) -> str:
    """统一文件提取入口"""
    validate_file(file_path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif suffix in [".xlsx", ".xls"]:
        return extract_text_from_excel(file_path)
    else:
        raise FileProcessingException(f"不支持的文件格式: {file_path.suffix}")


def split_text_into_chunks(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Tuple[int, int, str]]:
    """
    将文本按固定大小分块（带重叠）
    :param text: 原始文本
    :param chunk_size: 单块大小（字符数，默认使用配置文件中的CHUNK_SIZE）
    :param chunk_overlap: 重叠大小（字符数，默认使用配置文件中的CHUNK_OVERLAP）
    :return: 分块列表，每个块为（起始位置, 结束位置, 文本内容）
    """
    # 使用配置文件中的参数
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = CHUNK_OVERLAP
    
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append((start, end, chunk))
        start += chunk_size - chunk_overlap
    return chunks


def save_text_to_file(text: str, file_path: Path) -> None:
    """保存文本到文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
