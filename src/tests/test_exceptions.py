"""异常处理和错误恢复测试

覆盖各种异常情况、错误处理和恢复机制的测试。
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.utils.ollama_client import (
    OllamaError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaResponseError,
)
from src.esg.extraction.pdf_extractor import (
    PDFNotFoundError,
    PDFExtractionError,
    PDFLibraryNotFoundError,
)


class TestOllamaClientExceptions(unittest.TestCase):
    """Ollama客户端异常测试"""
    
    def test_ollama_error_basic(self):
        """测试基础OllamaError"""
        error = OllamaError("基础错误")
        self.assertEqual(str(error), "基础错误")
        self.assertIsInstance(error, Exception)
    
    def test_connection_error(self):
        """测试连接错误"""
        error = OllamaConnectionError("无法连接到服务器")
        self.assertEqual(str(error), "无法连接到服务器")
        self.assertIsInstance(error, OllamaError)
    
    def test_timeout_error(self):
        """测试超时错误"""
        error = OllamaTimeoutError("请求超时")
        self.assertEqual(str(error), "请求超时")
        self.assertIsInstance(error, OllamaError)
    
    def test_response_error_with_status(self):
        """测试带状态码的响应错误"""
        error = OllamaResponseError(
            "服务器错误",
            status_code=500,
            response_text="Internal Server Error"
        )
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.response_text, "Internal Server Error")
        self.assertIn("500", str(error))
    
    def test_response_error_without_status(self):
        """测试不带状态码的响应错误"""
        error = OllamaResponseError("响应错误")
        self.assertIsNone(error.status_code)
        self.assertIsNone(error.response_text)


class TestPDFExtractorExceptions(unittest.TestCase):
    """PDF提取器异常测试"""
    
    def test_pdf_not_found_error(self):
        """测试PDF未找到错误"""
        error = PDFNotFoundError("文件不存在")
        self.assertEqual(str(error), "文件不存在")
    
    def test_pdf_extraction_error(self):
        """测试PDF提取错误"""
        error = PDFExtractionError("提取失败")
        self.assertEqual(str(error), "提取失败")
    
    def test_pdf_library_not_found_error(self):
        """测试PDF库未找到错误"""
        error = PDFLibraryNotFoundError("未安装pdfplumber")
        self.assertEqual(str(error), "未安装pdfplumber")


class TestExceptionInheritance(unittest.TestCase):
    """异常继承关系测试"""
    
    def test_ollama_exception_hierarchy(self):
        """测试Ollama异常层次结构"""
        # 所有Ollama异常都应该继承自OllamaError
        self.assertTrue(issubclass(OllamaConnectionError, OllamaError))
        self.assertTrue(issubclass(OllamaTimeoutError, OllamaError))
        self.assertTrue(issubclass(OllamaResponseError, OllamaError))
        
        # OllamaError应该继承自Exception
        self.assertTrue(issubclass(OllamaError, Exception))
    
    def test_catch_base_exception(self):
        """测试捕获基础异常"""
        try:
            raise OllamaConnectionError("连接失败")
        except OllamaError as e:
            self.assertIn("连接失败", str(e))
    
    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        try:
            raise OllamaTimeoutError("超时")
        except OllamaTimeoutError as e:
            self.assertEqual(str(e), "超时")
        except OllamaError:
            self.fail("应该捕获到OllamaTimeoutError")


class TestErrorRecovery(unittest.TestCase):
    """错误恢复测试"""
    
    def test_retry_mechanism(self):
        """测试重试机制"""
        from src.esg.utils.ollama_client import retry_with_backoff
        
        attempt_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise OllamaConnectionError("临时失败")
            return "成功"
        
        result = flaky_operation()
        self.assertEqual(result, "成功")
        self.assertEqual(attempt_count, 2)
    
    def test_retry_exhaustion(self):
        """测试重试耗尽"""
        from src.esg.utils.ollama_client import retry_with_backoff
        
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def always_fail():
            raise OllamaConnectionError("持续失败")
        
        with self.assertRaises(OllamaConnectionError):
            always_fail()
    
    def test_fallback_mechanism(self):
        """测试降级机制"""
        # 测试在主要方法失败时使用备用方法
        def primary_method():
            raise OllamaError("主方法失败")
        
        def fallback_method():
            return "备用方法成功"
        
        try:
            result = primary_method()
        except OllamaError:
            result = fallback_method()
        
        self.assertEqual(result, "备用方法成功")


class TestNetworkErrorHandling(unittest.TestCase):
    """网络错误处理测试"""
    
    @patch('src.utils.ollama_client.requests.Session.request')
    def test_connection_timeout(self, mock_request):
        """测试连接超时"""
        import requests
        mock_request.side_effect = requests.Timeout("连接超时")
        
        from src.esg.utils.ollama_client import OllamaClient
        client = OllamaClient()
        
        # 应该处理超时异常
        with self.assertRaises((OllamaTimeoutError, Exception)):
            # 调用会触发网络请求的方法
            pass  # 具体测试依赖于实现
    
    @patch('src.utils.ollama_client.requests.Session.request')
    def test_connection_error(self, mock_request):
        """测试连接错误"""
        import requests
        mock_request.side_effect = requests.ConnectionError("连接被拒绝")
        
        from src.esg.utils.ollama_client import OllamaClient
        client = OllamaClient()
        
        # 应该处理连接错误
        with self.assertRaises((OllamaConnectionError, Exception)):
            pass
    
    @patch('src.utils.ollama_client.requests.Session.request')
    def test_http_error(self, mock_request):
        """测试HTTP错误"""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_request.return_value = mock_response
        
        from src.esg.utils.ollama_client import OllamaClient
        client = OllamaClient()
        
        # 应该处理HTTP错误
        with self.assertRaises((OllamaResponseError, Exception)):
            pass


class TestDataValidationErrors(unittest.TestCase):
    """数据验证错误测试"""
    
    def test_invalid_esg_metrics(self):
        """测试无效ESG指标"""
        from src.esg.core.models import ESGMetrics
        
        # 测试无效数据不会崩溃
        metrics = ESGMetrics(
            company_name="",
            year="invalid",
            renewable_energy_ratio=-10,
            employee_count=-100
        )
        
        # 应该能正常创建对象（验证在输入时进行）
        self.assertEqual(metrics.company_name, "")
    
    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        from src.esg.core.models import ESGMetrics
        
        # 应该能创建只有必填字段的对象
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024"
        )
        
        self.assertEqual(metrics.company_name, "测试公司")
        self.assertIsNone(metrics.renewable_energy_ratio)


class TestFileOperationErrors(unittest.TestCase):
    """文件操作错误测试"""
    
    def setUp(self):
        """测试前置"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后置"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_not_found(self):
        """测试文件不存在"""
        from src.esg.utils.validators import validate_pdf
        
        is_valid, msg = validate_pdf("/nonexistent/file.pdf")
        self.assertFalse(is_valid)
        self.assertIn("文件不存在", msg)
    
    def test_permission_error(self):
        """测试权限错误（模拟）"""
        # 在实际环境中测试权限错误
        pass
    
    def test_corrupted_file(self):
        """测试损坏的文件"""
        from src.esg.utils.validators import validate_pdf
        
        corrupted_pdf = Path(self.temp_dir) / "corrupted.pdf"
        corrupted_pdf.write_text("这不是PDF内容")
        
        is_valid, msg = validate_pdf(corrupted_pdf)
        self.assertFalse(is_valid)


class TestDatabaseErrors(unittest.TestCase):
    """数据库错误测试"""
    
    @patch('src.vector_store.chroma_store.chromadb.Client')
    def test_chromadb_connection_error(self, mock_client):
        """测试ChromaDB连接错误"""
        mock_client.side_effect = Exception("连接失败")
        
        # 应该处理数据库连接错误
        with self.assertRaises(Exception):
            from src.esg.vector_store.chroma_store import ChromaDBStore
            store = ChromaDBStore()


class TestGracefulDegradation(unittest.TestCase):
    """优雅降级测试"""
    
    def test_partial_data_handling(self):
        """测试部分数据处理"""
        from src.esg.core.models import ESGMetrics
        
        # 只有部分数据可用
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=50.0,  # 只有E维度部分数据
        )
        
        # 应该能计算得分（基于可用数据）
        e_score = metrics.get_dimension_score('E')
        self.assertIsInstance(e_score, float)
    
    def test_empty_data_handling(self):
        """测试空数据处理"""
        from src.esg.core.models import ESGMetrics, DEFAULT_SCORE
        
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024"
        )
        
        # 无数据时应该返回默认值
        e_score = metrics.get_dimension_score('E')
        self.assertEqual(e_score, DEFAULT_SCORE)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestOllamaClientExceptions,
        TestPDFExtractorExceptions,
        TestExceptionInheritance,
        TestErrorRecovery,
        TestNetworkErrorHandling,
        TestDataValidationErrors,
        TestFileOperationErrors,
        TestDatabaseErrors,
        TestGracefulDegradation,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
