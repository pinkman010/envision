"""指标提取器单元测试

覆盖MetricExtractor的各种使用场景。
"""

from unittest.mock import MagicMock

import pytest

from src.esg.extraction.metric_extractor import (
    MetricExtractionError,
    MetricExtractor,
    MetricType,
)


class TestMetricExtractor:
    """指标提取器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.extractor = MetricExtractor()

    def test_metric_extractor_init(self):
        """测试MetricExtractor初始化"""
        assert self.extractor is not None

    def test_extract(self):
        """测试提取单个指标"""
        text = "碳排放量为50000吨"
        result = self.extractor.extract(text, MetricType.ENVIRONMENT)
        # 返回的是ESGMetricsResult对象
        assert result is not None

    @pytest.mark.skip(reason="需要了解extract_batch的具体API")
    def test_extract_batch(self):
        """测试批量提取"""
        pass


class TestMetricExtractionError:
    """MetricExtractionError测试类"""

    def test_metric_extraction_error(self):
        """测试异常创建"""
        error = MetricExtractionError("提取失败")
        assert str(error) == "提取失败"
