"""PDF 文本提取器模块

支持使用 pdfplumber 和 PyPDF2 提取 PDF 文本内容及元数据
"""

import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

# 配置日志
logger = logging.getLogger(__name__)

# 安全：定义允许的根目录（防止路径遍历攻击）
# 获取项目根目录（当前文件的祖父目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# 系统临时目录
TEMP_DIR = Path(tempfile.gettempdir()).resolve()
# 允许访问的目录列表
ALLOWED_DIRECTORIES = [PROJECT_ROOT, TEMP_DIR]

# 尝试导入可选的 PDF 库
try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


@dataclass
class PDFMetadata:
    """PDF 元数据类

    存储从 PDF 中提取的元数据信息

    Attributes:
        filename: 文件名
        company: 公司名称
        year: 报告年份
        total_pages: 总页数
        title: 文档标题
        author: 文档作者
    """

    filename: str
    company: str = "未知"
    year: str = ""
    total_pages: int = 0
    title: str = ""
    author: str = ""


@dataclass
class PDFContent:
    """PDF 内容类

    存储从 PDF 中提取的文本内容和相关元数据

    Attributes:
        text: 提取的完整文本
        metadata: PDF 元数据
        pages: 每页的文本内容列表
    """

    text: str
    metadata: PDFMetadata
    pages: List[str] = field(default_factory=list)


class PDFExtractionError(Exception):
    """PDF 提取异常基类"""

    pass


class PDFNotFoundError(PDFExtractionError):
    """PDF 文件不存在异常"""

    pass


class PDFLibraryNotFoundError(PDFExtractionError):
    """PDF 库未安装异常"""

    pass


class PDFExtractor:
    """PDF 文本提取器

    支持使用 pdfplumber 和 PyPDF2 两种库提取 PDF 文本内容。
    优先使用 pdfplumber，失败时回退到 PyPDF2。

    Example:
        >>> extractor = PDFExtractor()
        >>> content = extractor.extract("report.pdf")
        >>> print(content.text[:100])
        >>> print(content.metadata.company)
    """

    # 公司名称映射表
    COMPANY_PATTERNS = {
        r"xiaomi|小米": "小米集团",
        r"huawei|华为": "华为",
        r"alibaba|阿里": "阿里巴巴",
        r"tencent|腾讯": "腾讯",
        r"baidu|百度": "百度",
        r"jd|京东": "京东",
        r"meituan|美团": "美团",
        r"byd|比亚迪": "比亚迪",
        r"catl|宁德": "宁德时代",
        r"pingan|平安": "中国平安",
    }

    def __init__(self, preferred_backend: Optional[str] = None) -> None:
        """初始化 PDF 提取器

        Args:
            preferred_backend: 首选后端，可选 'pdfplumber' 或 'pypdf2'，
                              默认为 None（自动选择）
        """
        self.preferred_backend = preferred_backend
        self._validate_libraries()

    def _validate_libraries(self) -> None:
        """验证必要的 PDF 库是否已安装"""
        if not HAS_PDFPLUMBER and not HAS_PYPDF2:
            raise PDFLibraryNotFoundError(
                "未找到可用的 PDF 提取库，请安装：pip install pdfplumber 或 pip install PyPDF2"
            )

    def _validate_path_security(self, path: Path) -> Path:
        """验证路径安全性（防止路径遍历攻击）

        Args:
            path: 输入的文件路径

        Returns:
            Path: 解析后的绝对路径

        Raises:
            PDFNotFoundError: 当路径不在允许的目录内时
        """
        # 安全：使用resolve()解析绝对路径，消除所有符号链接和..组件
        try:
            resolved_path = path.resolve()
        except (OSError, ValueError) as e:
            raise PDFNotFoundError(f"无效的文件路径: {path}") from e

        # 安全：检查解析后的路径是否在允许的目录内
        is_allowed = any(
            str(resolved_path).startswith(str(allowed_dir)) for allowed_dir in ALLOWED_DIRECTORIES
        )

        if not is_allowed:
            raise PDFNotFoundError(
                f"访问被拒绝：路径 '{path}' 不在允许的目录内。"
                f"只允许访问项目目录或临时目录内的文件。"
            )

        return resolved_path

    def extract(self, pdf_path: Union[str, Path]) -> PDFContent:
        """提取 PDF 文本内容

        从指定的 PDF 文件中提取文本内容，返回包含文本和元数据的对象。

        Args:
            pdf_path: PDF 文件路径

        Returns:
            PDFContent: 包含提取的文本和元数据的对象

        Raises:
            PDFNotFoundError: 当 PDF 文件不存在时或路径不安全时
            PDFExtractionError: 当提取过程失败时
        """
        path = Path(pdf_path)

        # 安全：验证路径防止路径遍历攻击
        path = self._validate_path_security(path)

        if not path.exists():
            raise PDFNotFoundError(f"PDF 文件不存在: {pdf_path}")

        if not path.suffix.lower() == ".pdf":
            raise PDFExtractionError(f"文件不是 PDF 格式: {pdf_path}")

        # 根据首选后端或自动选择提取方式
        backend = self._select_backend()

        try:
            if backend == "pdfplumber":
                return self._extract_with_pdfplumber(path)
            else:
                return self._extract_with_pypdf2(path)
        except Exception as e:
            # 如果首选后端失败，尝试另一个
            if backend == "pdfplumber" and HAS_PYPDF2:
                try:
                    return self._extract_with_pypdf2(path)
                except Exception as e2:
                    raise PDFExtractionError(
                        f"pdfplumber 和 PyPDF2 都提取失败。pdfplumber: {e}, PyPDF2: {e2}"
                    )
            elif backend == "pypdf2" and HAS_PDFPLUMBER:
                try:
                    return self._extract_with_pdfplumber(path)
                except Exception as e2:
                    raise PDFExtractionError(
                        f"PyPDF2 和 pdfplumber 都提取失败。PyPDF2: {e}, pdfplumber: {e2}"
                    )
            raise PDFExtractionError(f"PDF 提取失败: {e}")

    def _select_backend(self) -> str:
        """选择 PDF 提取后端"""
        if self.preferred_backend:
            return self.preferred_backend
        return "pdfplumber" if HAS_PDFPLUMBER else "pypdf2"

    def _extract_with_pdfplumber(self, path: Path) -> PDFContent:
        """使用 pdfplumber 提取 PDF

        Args:
            path: PDF 文件路径

        Returns:
            PDFContent: 提取的内容和元数据
        """
        pages_text: List[str] = []
        metadata = PDFMetadata(filename=path.name)

        with pdfplumber.open(path) as pdf:
            metadata.total_pages = len(pdf.pages)

            # 提取文档元数据（如果存在）
            if pdf.metadata:
                meta = pdf.metadata
                metadata.title = meta.get("Title", "")
                metadata.author = meta.get("Author", "")

            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())

        full_text = "\n\n".join(pages_text)
        metadata.company = self._extract_company(path.name, full_text)
        metadata.year = self._extract_year(path.name, full_text)

        return PDFContent(text=full_text, metadata=metadata, pages=pages_text)

    def _extract_with_pypdf2(self, path: Path) -> PDFContent:
        """使用 PyPDF2 提取 PDF

        Args:
            path: PDF 文件路径

        Returns:
            PDFContent: 提取的内容和元数据
        """
        pages_text: List[str] = []
        metadata = PDFMetadata(filename=path.name)

        with open(path, "rb", encoding=None) as f:
            reader = PyPDF2.PdfReader(f)
            metadata.total_pages = len(reader.pages)

            # 提取文档元数据（如果存在）
            if reader.metadata:
                meta = reader.metadata
                metadata.title = getattr(meta, "title", "") or ""
                metadata.author = getattr(meta, "author", "") or ""

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())

        full_text = "\n\n".join(pages_text)
        metadata.company = self._extract_company(path.name, full_text)
        metadata.year = self._extract_year(path.name, full_text)

        return PDFContent(text=full_text, metadata=metadata, pages=pages_text)

    def _extract_company(self, filename: str, text: str = "") -> str:
        """从文件名和文本中提取公司名称

        Args:
            filename: PDF 文件名
            text: PDF 文本内容

        Returns:
            str: 提取的公司名称，未知返回 "未知"
        """
        # 首先尝试从文件名匹配
        filename_lower = filename.lower()
        for pattern, company in self.COMPANY_PATTERNS.items():
            if re.search(pattern, filename_lower):
                return company

        # 尝试从文本内容匹配（前 1000 字符）
        text_prefix = text[:1000].lower() if text else ""
        for pattern, company in self.COMPANY_PATTERNS.items():
            if re.search(pattern, text_prefix):
                return company

        return "未知"

    def _extract_year(self, filename: str, text: str = "") -> str:
        """从文件名和文本中提取年份

        Args:
            filename: PDF 文件名
            text: PDF 文本内容

        Returns:
            str: 提取的年份，未找到返回空字符串
        """
        # 优先从文件名提取年份
        match = re.search(r"20\d{2}", filename)
        if match:
            return match.group()

        # 从文本中查找年份（前 2000 字符）
        if text:
            text_prefix = text[:2000]
            # 查找常见的年份格式
            patterns = [
                r"20\d{2}[^0-9]年",
                r"年度.*?(20\d{2})",
                r"财年.*?(20\d{2})",
                r"(\d{4}).{0,5}年.*?报告",
            ]
            for pattern in patterns:
                match = re.search(pattern, text_prefix)
                if match:
                    year = re.search(r"20\d{2}", match.group())
                    if year:
                        return year.group()

        return ""

    def extract_batch(self, pdf_paths: List[Union[str, Path]]) -> Dict[str, PDFContent]:
        """批量提取多个 PDF 文件

        Args:
            pdf_paths: PDF 文件路径列表

        Returns:
            Dict[str, PDFContent]: 文件名到内容的映射
        """
        results: Dict[str, PDFContent] = {}

        for path in pdf_paths:
            try:
                content = self.extract(path)
                results[Path(path).name] = content
            except PDFExtractionError as e:
                results[Path(path).name] = None  # type: ignore
                logger.error(f"提取失败 [{path}]: {e}")

        return results
