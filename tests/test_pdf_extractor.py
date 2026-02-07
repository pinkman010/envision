"""PDF提取器单元测试

覆盖PDFExtractor的各种使用场景和边界情况。
"""

import unittest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractor.pdf_extractor import (
    PDFExtractor, PDFContent, PDFMetadata,
    PDFNotFoundError, PDFExtractionError, PDFLibraryNotFoundError
)


class TestPDFExtractor(unittest.TestCase):
    """PDF提取器测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = Path(self.temp_dir) / "test_report.pdf"
        self.nonexistent_path = Path(self.temp_dir) / "nonexistent.pdf"
        
        # 创建一个虚拟的PDF文件（仅用于存在性测试）
        self.test_pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")
    
    def tearDown(self):
        """测试后置清理"""
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_default_backend(self):
        """测试默认后端初始化"""
        extractor = PDFExtractor()
        self.assertIsNone(extractor.preferred_backend)
    
    def test_init_with_pdfplumber_backend(self):
        """测试指定pdfplumber后端"""
        extractor = PDFExtractor(preferred_backend='pdfplumber')
        self.assertEqual(extractor.preferred_backend, 'pdfplumber')
    
    def test_init_with_pypdf2_backend(self):
        """测试指定PyPDF2后端"""
        extractor = PDFExtractor(preferred_backend='pypdf2')
        self.assertEqual(extractor.preferred_backend, 'pypdf2')
    
    @patch('src.extractor.pdf_extractor.HAS_PDFPLUMBER', False)
    @patch('src.extractor.pdf_extractor.HAS_PYPDF2', False)
    def test_init_without_libraries(self):
        """测试无PDF库时抛出异常"""
        with self.assertRaises(PDFLibraryNotFoundError):
            PDFExtractor()
    
    def test_extract_file_not_found(self):
        """测试文件不存在场景"""
        extractor = PDFExtractor()
        with self.assertRaises(PDFNotFoundError) as context:
            extractor.extract(self.nonexistent_path)
        self.assertIn("PDF 文件不存在", str(context.exception))
    
    def test_extract_non_pdf_file(self):
        """测试非PDF文件场景"""
        txt_file = Path(self.temp_dir) / "test.txt"
        txt_file.write_text("not a pdf")
        
        extractor = PDFExtractor()
        with self.assertRaises(PDFExtractionError) as context:
            extractor.extract(txt_file)
        self.assertIn("文件不是 PDF 格式", str(context.exception))
    
    def test_path_traversal_attack_prevention_absolute(self):
        """测试绝对路径遍历攻击防护"""
        extractor = PDFExtractor()
        # 尝试访问系统文件（使用不存在的路径）
        malicious_path = "/etc/passwd"
        with self.assertRaises(PDFNotFoundError):
            extractor.extract(malicious_path)
    
    def test_path_traversal_attack_prevention_relative(self):
        """测试相对路径遍历攻击防护"""
        extractor = PDFExtractor()
        # 尝试使用../遍历
        malicious_path = "../../../etc/passwd"
        with self.assertRaises(PDFNotFoundError):
            extractor.extract(malicious_path)
    
    def test_path_traversal_with_null_bytes(self):
        """测试包含空字节的路径"""
        extractor = PDFExtractor()
        # 空字节在文件路径中是危险的
        with self.assertRaises((PDFNotFoundError, ValueError)):
            extractor.extract("test\x00.pdf")
    
    @patch('src.extractor.pdf_extractor.HAS_PDFPLUMBER', True)
    @patch('src.extractor.pdf_extractor.pdfplumber')
    def test_extract_with_pdfplumber(self, mock_pdfplumber):
        """测试使用pdfplumber提取"""
        # 设置mock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "测试页面内容"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {"Title": "测试报告", "Author": "测试作者"}
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        extractor = PDFExtractor(preferred_backend='pdfplumber')
        result = extractor.extract(self.test_pdf_path)
        
        self.assertIsInstance(result, PDFContent)
        self.assertEqual(result.text, "测试页面内容")
        self.assertEqual(result.metadata.title, "测试报告")
        self.assertEqual(result.metadata.author, "测试作者")
        self.assertEqual(result.metadata.total_pages, 1)
    
    @patch('src.extractor.pdf_extractor.HAS_PYPDF2', True)
    @patch('builtins.open', mock_open(read_data=b'%PDF-1.4 fake'))
    def test_extract_with_pypdf2(self):
        """测试使用PyPDF2提取"""
        # 在模块级别模拟PyPDF2
        mock_pypdf2 = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PyPDF2测试内容"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = MagicMock()
        mock_reader.metadata.title = "PyPDF2报告"
        mock_reader.metadata.author = "PyPDF2作者"
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # 临时替换模块中的PyPDF2
        import src.extractor.pdf_extractor as pdf_module
        original_pypdf2 = getattr(pdf_module, 'PyPDF2', None)
        pdf_module.PyPDF2 = mock_pypdf2
        
        try:
            extractor = PDFExtractor(preferred_backend='pypdf2')
            result = extractor.extract(self.test_pdf_path)
            
            self.assertIsInstance(result, PDFContent)
            self.assertEqual(result.text, "PyPDF2测试内容")
            self.assertEqual(result.metadata.total_pages, 1)
        finally:
            # 恢复原始值
            if original_pypdf2:
                pdf_module.PyPDF2 = original_pypdf2
    
    @patch('src.extractor.pdf_extractor.HAS_PDFPLUMBER', True)
    @patch('src.extractor.pdf_extractor.HAS_PYPDF2', True)
    @patch('src.extractor.pdf_extractor.pdfplumber')
    @patch('builtins.open', mock_open(read_data=b'%PDF-1.4 fake'))
    def test_extract_backend_fallback(self, mock_pdfplumber):
        """测试后端失败回退"""
        # 使pdfplumber失败
        mock_pdfplumber.open.side_effect = Exception("pdfplumber error")
        
        # 在模块级别模拟PyPDF2
        mock_pypdf2 = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "回退内容"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        import src.extractor.pdf_extractor as pdf_module
        original_pypdf2 = getattr(pdf_module, 'PyPDF2', None)
        pdf_module.PyPDF2 = mock_pypdf2
        
        try:
            extractor = PDFExtractor(preferred_backend='pdfplumber')
            result = extractor.extract(self.test_pdf_path)
            
            self.assertEqual(result.text, "回退内容")
        finally:
            if original_pypdf2:
                pdf_module.PyPDF2 = original_pypdf2
    
    def test_extract_company_from_filename(self):
        """测试从文件名提取公司名称"""
        extractor = PDFExtractor()
        
        # 测试各种公司名称匹配
        test_cases = [
            ("xiaomi_2024_report.pdf", "小米集团"),
            ("huawei_esg_2024.pdf", "华为"),
            ("alibaba_report.pdf", "阿里巴巴"),
            ("腾讯2024ESG报告.pdf", "腾讯"),
            ("unknown_company.pdf", "未知"),
        ]
        
        for filename, expected_company in test_cases:
            company = extractor._extract_company(filename)
            self.assertEqual(company, expected_company, f"文件名: {filename}")
    
    def test_extract_company_from_text(self):
        """测试从文本内容提取公司名称"""
        extractor = PDFExtractor()
        
        text = "小米集团致力于可持续发展，我们的ESG报告展示了..."
        company = extractor._extract_company("unknown.pdf", text)
        self.assertEqual(company, "小米集团")
    
    def test_extract_year_from_filename(self):
        """测试从文件名提取年份"""
        extractor = PDFExtractor()
        
        test_cases = [
            ("report_2024.pdf", "2024"),
            ("esg_2023_china.pdf", "2023"),
            ("company_2022_annual.pdf", "2022"),
            ("noyear_report.pdf", ""),
        ]
        
        for filename, expected_year in test_cases:
            year = extractor._extract_year(filename)
            self.assertEqual(year, expected_year, f"文件名: {filename}")
    
    def test_extract_year_from_text(self):
        """测试从文本内容提取年份"""
        extractor = PDFExtractor()
        
        # 使用匹配正则的格式："2024年"（数字后跟年）
        # 注意：文件名没有年份时才会查文本
        text = "2024年度报告：本报告涵盖公司的ESG表现..."
        year = extractor._extract_year("report.pdf", text)
        self.assertEqual(year, "2024")
        
        # 测试"年度"格式
        text2 = "本报告是2023年度企业社会责任报告"
        year2 = extractor._extract_year("report_no_year.pdf", text2)
        self.assertEqual(year2, "2023")
    
    def test_extract_batch(self):
        """测试批量提取"""
        # 创建多个测试文件
        pdf2 = Path(self.temp_dir) / "test2.pdf"
        pdf3 = Path(self.temp_dir) / "test3.pdf"
        pdf2.write_bytes(b"%PDF-1.4 fake")
        pdf3.write_bytes(b"%PDF-1.4 fake")
        
        with patch.object(PDFExtractor, 'extract') as mock_extract:
            mock_extract.return_value = PDFContent(
                text="测试内容",
                metadata=PDFMetadata(filename="test.pdf")
            )
            
            extractor = PDFExtractor()
            results = extractor.extract_batch([self.test_pdf_path, pdf2, pdf3])
            
            self.assertEqual(len(results), 3)
            self.assertIn("test_report.pdf", results)
            self.assertIn("test2.pdf", results)
            self.assertIn("test3.pdf", results)
    
    def test_extract_batch_with_failure(self):
        """测试批量提取中部分失败"""
        pdf2 = Path(self.temp_dir) / "nonexistent.pdf"
        
        with patch.object(PDFExtractor, 'extract') as mock_extract:
            def side_effect(path):
                if "nonexistent" in str(path):
                    raise PDFNotFoundError("文件不存在")
                return PDFContent(
                    text="测试内容",
                    metadata=PDFMetadata(filename="test.pdf")
                )
            
            mock_extract.side_effect = side_effect
            
            extractor = PDFExtractor()
            results = extractor.extract_batch([self.test_pdf_path, pdf2])
            
            self.assertEqual(len(results), 2)
            self.assertIsNotNone(results["test_report.pdf"])
            self.assertIsNone(results["nonexistent.pdf"])
    
    def test_pdf_content_dataclass(self):
        """测试PDFContent数据类"""
        content = PDFContent(
            text="测试文本",
            metadata=PDFMetadata(filename="test.pdf"),
            pages=["页1", "页2"]
        )
        
        self.assertEqual(content.text, "测试文本")
        self.assertEqual(content.metadata.filename, "test.pdf")
        self.assertEqual(len(content.pages), 2)
    
    def test_pdf_metadata_dataclass(self):
        """测试PDFMetadata数据类"""
        metadata = PDFMetadata(
            filename="test.pdf",
            company="测试公司",
            year="2024",
            total_pages=10,
            title="测试标题",
            author="测试作者"
        )
        
        self.assertEqual(metadata.filename, "test.pdf")
        self.assertEqual(metadata.company, "测试公司")
        self.assertEqual(metadata.year, "2024")
        self.assertEqual(metadata.total_pages, 10)
    
    def test_pdf_metadata_defaults(self):
        """测试PDFMetadata默认值"""
        metadata = PDFMetadata(filename="test.pdf")
        
        self.assertEqual(metadata.company, "未知")
        self.assertEqual(metadata.year, "")
        self.assertEqual(metadata.total_pages, 0)
        self.assertEqual(metadata.title, "")
        self.assertEqual(metadata.author, "")


class TestPDFExtractorEdgeCases(unittest.TestCase):
    """PDF提取器边界情况测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.extractor.pdf_extractor.HAS_PDFPLUMBER', True)
    @patch('src.extractor.pdf_extractor.pdfplumber')
    def test_extract_empty_pdf(self, mock_pdfplumber):
        """测试空PDF文件"""
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.metadata = None
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        test_pdf = Path(self.temp_dir) / "empty.pdf"
        test_pdf.write_bytes(b"%PDF-1.4")
        
        extractor = PDFExtractor(preferred_backend='pdfplumber')
        result = extractor.extract(test_pdf)
        
        self.assertEqual(result.text, "")
        self.assertEqual(result.metadata.total_pages, 0)
    
    @patch('src.extractor.pdf_extractor.HAS_PDFPLUMBER', True)
    @patch('src.extractor.pdf_extractor.pdfplumber')
    def test_extract_pdf_with_empty_pages(self, mock_pdfplumber):
        """测试包含空白页面的PDF"""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = None  # 空白页
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "   "  # 只有空白字符
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "有效内容"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.metadata = {}
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        test_pdf = Path(self.temp_dir) / "sparse.pdf"
        test_pdf.write_bytes(b"%PDF-1.4")
        
        extractor = PDFExtractor(preferred_backend='pdfplumber')
        result = extractor.extract(test_pdf)
        
        # 空白页面应该被过滤或保留（取决于实现）
        self.assertIn("有效内容", result.text)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestPDFExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestPDFExtractorEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
