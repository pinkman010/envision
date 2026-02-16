"""差距分析器单元测试

覆盖GapAnalyzer的各种使用场景和边界情况。
"""

from unittest.mock import MagicMock, patch

import pytest

from src.esg.analysis.gap_analyzer import (
    BenchmarkRepository,
    GapAnalyzer,
    GapResult,
    IndicatorGap,
    JsonBenchmarkRepository,
)


class TestBenchmarkRepository:
    """标杆仓库测试类"""

    def test_json_benchmark_repository_default_data(self):
        """测试使用默认标杆数据"""
        repo = JsonBenchmarkRepository()
        companies = repo.get_available_companies()
        assert isinstance(companies, list)
        assert "行业平均" in companies
        assert "维斯塔斯" in companies
        assert "西门子歌美飒" in companies

    def test_get_benchmark(self):
        """测试获取标杆数据"""
        repo = JsonBenchmarkRepository()
        benchmark = repo.get_benchmark("行业平均")
        assert benchmark is not None
        assert "overall_score" in benchmark
        assert "dimensions" in benchmark

    def test_get_benchmark_not_found(self):
        """测试获取不存在的标杆"""
        repo = JsonBenchmarkRepository()
        benchmark = repo.get_benchmark("不存在的公司")
        assert benchmark is None


class TestGapAnalyzer:
    """差距分析器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.analyzer = GapAnalyzer()
        # 创建Mock的ESGMetrics对象
        self.mock_metrics = MagicMock()
        # 设置基础属性
        self.mock_metrics.company_name = "测试公司"
        self.mock_metrics.year = "2024"

    def test_analyze_dimension_gap(self):
        """测试维度差距分析"""
        # 模拟维度得分
        self.mock_metrics.get_dimension_score = MagicMock(
            side_effect=lambda d: {"E": 60, "S": 65, "G": 70}.get(d, 50)
        )

        result = self.analyzer.analyze_dimension_gap(self.mock_metrics, "行业平均")

        assert isinstance(result, dict)
        assert "E" in result
        assert "S" in result
        assert "G" in result

        # 验证GapResult结构
        for dim, gap_result in result.items():
            assert isinstance(gap_result, GapResult)
            assert gap_result.dimension == dim

    def test_analyze_dimension_gap_invalid_company(self):
        """测试无效标杆企业"""
        self.mock_metrics.get_dimension_score = MagicMock(return_value=50)

        with pytest.raises(ValueError):
            self.analyzer.analyze_dimension_gap(self.mock_metrics, "不存在的公司")

    @pytest.mark.skip(reason="需要真实ESGMetrics对象")
    def test_analyze_indicator_gap(self):
        """测试指标差距分析"""
        pass

    def test_compare_with_multiple(self):
        """测试多标杆对比"""
        self.mock_metrics.get_dimension_score = MagicMock(
            side_effect=lambda d: {"E": 60, "S": 65, "G": 70}.get(d, 50)
        )

        result = self.analyzer.compare_with_multiple(self.mock_metrics)

        assert "comparisons" in result
        assert "best_benchmark" in result
        assert "overall_ranking" in result
        assert isinstance(result["comparisons"], list)

    @pytest.mark.skip(reason="需要真实ESGMetrics对象")
    def test_get_improvement_areas(self):
        """测试获取改进领域"""
        pass

    def test_get_available_benchmarks(self):
        """测试获取可用标杆列表"""
        benchmarks = self.analyzer.get_available_benchmarks()
        assert isinstance(benchmarks, list)
        assert "行业平均" in benchmarks

    def test_analyze_historical_trend(self):
        """测试历史趋势分析"""
        result = self.analyzer.analyze_historical_trend("绿色能源集团")

        assert isinstance(result, dict)
        assert "years" in result
        assert "trends" in result
        assert "overall" in result

    def test_analyze_historical_trend_no_company(self):
        """测试不存在的公司历史趋势"""
        result = self.analyzer.analyze_historical_trend("不存在的公司")

        assert result == {"years": [], "trends": {}, "overall": []}

    def test_predict_next_year(self):
        """测试下一年预测"""
        # 模拟历史趋势数据
        historical_trend = {
            "years": ["2022", "2023", "2024"],
            "trends": {"E": [70, 75, 80], "S": [68, 72, 78], "G": [70, 74, 80]},
            "overall": [69.3, 73.7, 79.3],
        }

        result = self.analyzer.predict_next_year(historical_trend)

        assert "year" in result
        assert result["year"] == "2025"
        assert "predicted" in result
        assert "overall" in result

    def test_predict_next_year_insufficient_data(self):
        """测试数据不足时的预测"""
        historical_trend = {"years": ["2024"], "trends": {"E": [80]}, "overall": [80]}

        result = self.analyzer.predict_next_year(historical_trend)

        # 数据不足时应返回空预测
        assert result["predicted"] == {}

    def test_predict_next_year_empty_input(self):
        """测试空输入预测"""
        result = self.analyzer.predict_next_year({})

        assert result["predicted"] == {}
        assert result["overall"] == 0


class TestGapResult:
    """GapResult数据类测试"""

    def test_gap_result_creation(self):
        """测试GapResult创建"""
        gap = GapResult(
            dimension="E",
            current=60.0,
            benchmark=80.0,
            gap=20.0,
            gap_percentage=25.0,
            priority="高",
        )

        assert gap.dimension == "E"
        assert gap.current == 60.0
        assert gap.benchmark == 80.0
        assert gap.gap == 20.0
        assert gap.gap_percentage == 25.0
        assert gap.priority == "高"


class TestIndicatorGap:
    """IndicatorGap数据类测试"""

    def test_indicator_gap_creation(self):
        """测试IndicatorGap创建"""
        gap = IndicatorGap(
            indicator_id="carbon_intensity",
            indicator_name="碳强度",
            current_score=60.0,
            benchmark_score=80.0,
            gap=20.0,
            disclosure_level="高",
        )

        assert gap.indicator_id == "carbon_intensity"
        assert gap.indicator_name == "碳强度"
        assert gap.current_score == 60.0
        assert gap.benchmark_score == 80.0
        assert gap.gap == 20.0
        assert gap.disclosure_level == "高"
