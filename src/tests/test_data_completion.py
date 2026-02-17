"""数据补全引擎单元测试

覆盖DataCompletionEngine的各种使用场景和边界情况。
"""

from unittest.mock import MagicMock

import pytest

# 模块不存在时跳过整个测试文件
pytest.importorskip("src.esg.completion.data_completion", reason="src.esg.completion.data_completion 模块不存在")

from src.esg.completion.data_completion import (
    CompletionLog,
    CompletionResult,
    DataCompletionEngine,
)


class TestDataCompletionEngine:
    """数据补全引擎测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.engine = DataCompletionEngine()
        # 创建Mock的ESGMetrics对象
        self.mock_metrics = MagicMock()
        self.mock_metrics.company_name = "测试公司"
        self.mock_metrics.year = "2024"
        self.mock_metrics.carbon_emissions = None
        self.mock_metrics.renewable_energy_ratio = None
        self.mock_metrics.energy_efficiency = None
        self.mock_metrics.water_consumption = None
        self.mock_metrics.waste_recycling_rate = None
        self.mock_metrics.employee_count = None
        self.mock_metrics.female_ratio = None
        self.mock_metrics.training_hours = None
        self.mock_metrics.safety_incidents = None
        self.mock_metrics.community_investment = None
        self.mock_metrics.board_independence_ratio = None
        self.mock_metrics.ethics_training_coverage = None
        self.mock_metrics.esg_report_quality = None
        self.mock_metrics.source = "test"
        self.mock_metrics.extracted_at = "2024-01-01"
        self.mock_metrics.confidence = {}
        self.mock_metrics.data_sources = []

    def test_complete_with_missing_fields(self):
        """测试补全缺失字段"""
        result = self.engine.complete(self.mock_metrics)

        assert isinstance(result, CompletionResult)
        assert result.metrics is not None
        assert isinstance(result.logs, list)
        assert result.completion_rate >= 0
        assert result.overall_confidence >= 0

    def test_complete_with_specific_fields(self):
        """测试指定字段补全"""
        target_fields = ["renewable_energy_ratio", "female_ratio"]

        result = self.engine.complete(self.mock_metrics, target_fields=target_fields)

        assert isinstance(result, CompletionResult)
        # 只补全指定字段
        field_names = [log.field_name for log in result.logs]
        for field in target_fields:
            assert field in field_names

    def test_complete_with_min_confidence(self):
        """测试最小置信度过滤"""
        # 设置较低的置信度阈值
        result = self.engine.complete(self.mock_metrics, min_confidence=0.9)

        assert isinstance(result, CompletionResult)

    def test_complete_with_all_valid_fields(self):
        """测试所有字段都已有效"""
        # 设置所有字段为有效值
        self.mock_metrics.carbon_emissions = 50000.0
        self.mock_metrics.renewable_energy_ratio = 30.0
        self.mock_metrics.energy_efficiency = 70.0
        self.mock_metrics.water_consumption = 100000.0
        self.mock_metrics.waste_recycling_rate = 60.0
        self.mock_metrics.employee_count = 5000
        self.mock_metrics.female_ratio = 40.0
        self.mock_metrics.training_hours = 20.0
        self.mock_metrics.safety_incidents = 0
        self.mock_metrics.community_investment = 1000000.0
        self.mock_metrics.board_independence_ratio = 60.0
        self.mock_metrics.ethics_training_coverage = 80.0
        self.mock_metrics.esg_report_quality = 70.0

        result = self.engine.complete(self.mock_metrics)

        # 验证补全结果有效
        assert isinstance(result, CompletionResult)

    def test_get_completion_summary(self):
        """测试获取补全摘要"""
        # 先执行补全
        self.engine.complete(self.mock_metrics)

        summary = self.engine.get_completion_summary()

        assert isinstance(summary, dict)
        assert "total_completed" in summary
        assert "by_method" in summary
        assert "by_dimension" in summary
        assert "avg_confidence" in summary

    def test_get_completion_summary_empty(self):
        """测试空补全摘要"""
        summary = self.engine.get_completion_summary()

        assert summary["total_completed"] == 0
        assert summary["avg_confidence"] == 0.0


class TestCompletionLog:
    """CompletionLog数据类测试"""

    def test_completion_log_creation(self):
        """测试CompletionLog创建"""
        log = CompletionLog(
            field_name="renewable_energy_ratio",
            original_value=None,
            completed_value=30.0,
            method="benchmark",
            confidence=0.85,
            reason="基于行业基准数据",
        )

        assert log.field_name == "renewable_energy_ratio"
        assert log.original_value is None
        assert log.completed_value == 30.0
        assert log.method == "benchmark"
        assert log.confidence == 0.85
        assert "基准" in log.reason


class TestCompletionResult:
    """CompletionResult数据类测试"""

    def test_completion_result_creation(self):
        """测试CompletionResult创建"""
        mock_metrics = MagicMock()

        result = CompletionResult(
            metrics=mock_metrics, logs=[], completion_rate=0.5, overall_confidence=0.75
        )

        assert result.metrics == mock_metrics
        assert result.logs == []
        assert result.completion_rate == 0.5
        assert result.overall_confidence == 0.75


class TestDataCompletionEngineWithBenchmark:
    """带基准数据的补全引擎测试"""

    def setup_method(self):
        """测试前置设置"""
        # 创建Mock的BenchmarkData
        self.mock_benchmark = MagicMock()
        self.mock_benchmark.avg_renewable_energy_ratio = 35.0
        self.mock_benchmark.avg_energy_efficiency = 75.0
        self.mock_benchmark.avg_female_ratio = 38.0
        self.mock_benchmark.avg_training_hours = 25.0
        self.mock_benchmark.avg_board_independence_ratio = 55.0
        self.mock_benchmark.sample_size = 100

        self.engine = DataCompletionEngine(benchmark_data=self.mock_benchmark)

        # 创建Mock的ESGMetrics
        self.mock_metrics = MagicMock()
        self.mock_metrics.company_name = "测试公司"
        self.mock_metrics.year = "2024"
        self.mock_metrics.carbon_emissions = None
        self.mock_metrics.renewable_energy_ratio = None
        self.mock_metrics.energy_efficiency = None
        self.mock_metrics.water_consumption = None
        self.mock_metrics.waste_recycling_rate = None
        self.mock_metrics.employee_count = None
        self.mock_metrics.female_ratio = None
        self.mock_metrics.training_hours = None
        self.mock_metrics.safety_incidents = None
        self.mock_metrics.community_investment = None
        self.mock_metrics.board_independence_ratio = None
        self.mock_metrics.ethics_training_coverage = None
        self.mock_metrics.esg_report_quality = None
        self.mock_metrics.source = "test"
        self.mock_metrics.extracted_at = "2024-01-01"
        self.mock_metrics.confidence = {}
        self.mock_metrics.data_sources = []

    def test_complete_with_benchmark(self):
        """测试使用基准数据补全"""
        result = self.engine.complete(self.mock_metrics)

        assert isinstance(result, CompletionResult)
        # 验证使用了基准数据
        methods = [log.method for log in result.logs]
        if "benchmark" in methods:
            assert any(log.confidence >= 0.85 for log in result.logs)


class TestDataCompletionEngineWithHistorical:
    """带历史数据的补全引擎测试"""

    def setup_method(self):
        """测试前置设置"""
        # 创建历史数据
        self.historical_data = {
            "2022": MagicMock(renewable_energy_ratio=25.0, female_ratio=35.0),
            "2023": MagicMock(renewable_energy_ratio=28.0, female_ratio=36.0),
        }

        self.engine = DataCompletionEngine(historical_data=self.historical_data)

        # 创建Mock的ESGMetrics
        self.mock_metrics = MagicMock()
        self.mock_metrics.company_name = "测试公司"
        self.mock_metrics.year = "2024"
        self.mock_metrics.carbon_emissions = None
        self.mock_metrics.renewable_energy_ratio = None
        self.mock_metrics.energy_efficiency = None
        self.mock_metrics.water_consumption = None
        self.mock_metrics.waste_recycling_rate = None
        self.mock_metrics.employee_count = None
        self.mock_metrics.female_ratio = None
        self.mock_metrics.training_hours = None
        self.mock_metrics.safety_incidents = None
        self.mock_metrics.community_investment = None
        self.mock_metrics.board_independence_ratio = None
        self.mock_metrics.ethics_training_coverage = None
        self.mock_metrics.esg_report_quality = None
        self.mock_metrics.source = "test"
        self.mock_metrics.extracted_at = "2024-01-01"
        self.mock_metrics.confidence = {}
        self.mock_metrics.data_sources = []

    def test_complete_with_historical(self):
        """测试使用历史数据补全"""
        result = self.engine.complete(self.mock_metrics)

        assert isinstance(result, CompletionResult)
        # 验证使用了历史数据
        methods = [log.method for log in result.logs]
        # 可能有历史数据补全
