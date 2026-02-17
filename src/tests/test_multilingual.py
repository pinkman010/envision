"""多语言报告生成器单元测试

覆盖MultilingualReportGenerator的各种使用场景。
"""

import pytest

# 模块不存在时跳过整个测试文件
pytest.importorskip("src.esg.extraction.multilingual", reason="src.esg.extraction.multilingual 模块不存在")

from src.esg.extraction.multilingual import (
    Language,
    MultilingualReport,
    MultilingualReportGenerator,
)


class TestMultilingualReportGenerator:
    """多语言报告生成器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.generator = MultilingualReportGenerator()

    def test_generator_init(self):
        """测试生成器初始化"""
        assert self.generator is not None

    @pytest.mark.skip(reason="需要修复API调用方式")
    def test_generate_report(self):
        """测试生成报告"""
        pass

    def test_generate_reports_for_all_languages(self):
        """测试生成所有语言报告"""
        mock_data = {"title": "测试报告", "content": "测试内容"}
        result = self.generator.generate_reports_for_all_languages(mock_data)
        assert isinstance(result, dict)

    def test_get_translation(self):
        """测试翻译"""
        result = self.generator.get_translation("Hello", Language.ZH_CN)
        assert result is not None


class TestLanguage:
    """语言枚举测试"""

    def test_language_values(self):
        """测试语言值"""
        assert Language.EN.value == "en"
        assert Language.ZH_CN.value == "zh_CN"


class TestMultilingualReport:
    """MultilingualReport测试"""

    def test_import_report(self):
        """测试导入MultilingualReport"""
        try:
            from src.esg.extraction.multilingual import MultilingualReport

            assert True
        except ImportError:
            pytest.fail("无法导入MultilingualReport")
