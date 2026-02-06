"""PDF文本提取器"""

import logging
import os
import re

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

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """PDF文本提取器"""
    
    def extract(self, pdf_path: str) -> str:
        """提取PDF文本"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        if HAS_PDFPLUMBER:
            try:
                return self._extract_with_pdfplumber(pdf_path)
            except (pdfplumber.exceptions.PDFSyntaxError, 
                    pdfplumber.exceptions.PasswordRequired,
                    OSError, IOError) as e:
                logger.warning(f"pdfplumber提取失败: {type(e).__name__}: {e}, 尝试PyPDF2")
        
        if HAS_PYPDF2:
            return self._extract_with_pypdf2(pdf_path)
        
        raise RuntimeError("无可用PDF提取库")
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """使用pdfplumber提取"""
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """使用PyPDF2提取"""
        text_parts = []
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    
    def extract_with_metadata(self, pdf_path: str) -> dict:
        """提取文本和元数据"""
        text = self.extract(pdf_path)
        filename = os.path.basename(pdf_path)
        
        return {
            'text': text,
            'filename': filename,
            'company_name': self._extract_company_name(filename),
            'year': self._extract_year(filename)
        }
    
    def _extract_company_name(self, filename: str) -> str:
        """提取公司名"""
        if 'xiaomi' in filename.lower() or '小米' in filename:
            return "小米集团"
        return "未知公司"
    
    def _extract_year(self, filename: str) -> str:
        """提取年份"""
        match = re.search(r'20\d{2}', filename)
        return match.group() if match else "2023"