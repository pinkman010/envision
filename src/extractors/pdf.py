"""PDF文本提取"""

import re
from pathlib import Path

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


class PDFExtractor:
    """PDF提取器"""
    
    def extract(self, pdf_path: str) -> str:
        """提取PDF文本"""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF不存在: {pdf_path}")
        
        # 优先使用pdfplumber
        if HAS_PDFPLUMBER:
            try:
                return self._extract_pdfplumber(pdf_path)
            except Exception as e:
                print(f"pdfplumber失败: {e}")
        
        # 回退到PyPDF2
        if HAS_PYPDF2:
            return self._extract_pypdf2(pdf_path)
        
        raise RuntimeError("无PDF提取库，请安装: pip install pdfplumber")
    
    def _extract_pdfplumber(self, path: str) -> str:
        """使用pdfplumber提取"""
        texts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
        return "\n\n".join(texts)
    
    def _extract_pypdf2(self, path: str) -> str:
        """使用PyPDF2提取"""
        texts = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
        return "\n\n".join(texts)
    
    def extract_with_meta(self, pdf_path: str) -> dict:
        """提取文本和元数据"""
        text = self.extract(pdf_path)
        filename = Path(pdf_path).name
        
        return {
            "text": text,
            "filename": filename,
            "company": self._extract_company(filename),
            "year": self._extract_year(filename)
        }
    
    def _extract_company(self, filename: str) -> str:
        """提取公司名"""
        if "xiaomi" in filename.lower() or "小米" in filename:
            return "小米集团"
        return "未知"
    
    def _extract_year(self, filename: str) -> str:
        """提取年份"""
        match = re.search(r"20\d{2}", filename)
        return match.group() if match else "2023"
