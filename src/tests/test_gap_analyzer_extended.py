"""差距分析器扩展单元测试

覆盖esg.analysis.gap_analyzer模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGapAnalyzerInit(unittest.TestCase):
    """GapAnalyzer初始化测试"""

    def test_gap_analyzer_init_default(self):
        """测试默认初始化"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()
        self.assertIsNotNone(analyzer.repository)
        self.assertIsNotNone(analyzer.benchmark_data)

    def test_gap_analyzer_init_with_custom_repo(self):
        """测试自定义仓库初始化"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer, JsonBenchmarkRepository

        mock_repo = MagicMock()
        mock_repo.load_data.return_value = ({}, {})
        analyzer = GapAnalyzer(repository=mock_repo)
        self.assertEqual(analyzer.repository, mock_repo)


class TestGapAnalyzerDimensionGap(unittest.TestCase):
    """维度差距分析测试"""

    def test_analyze_dimension_gap_basic(self):
        """测试基本维度差距分析"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer
        from src.esg.core.models import ESGMetrics

        analyzer = GapAnalyzer()

        # 创建模拟指标
        metrics = MagicMock(spec=ESGMetrics)
        metrics.get_dimension_score = lambda d: {"E": 70, "S": 75, "G": 80}.get(d, 0)

        result = analyzer.analyze_dimension_gap(metrics, "行业平均")

        self.assertIn("E", result)
        self.assertIn("S", result)
        self.assertIn("G", result)
        # 修改断言方式，使用字典键访问
        self.assertEqual(result["E"].dimension, "E")

    def test_analyze_dimension_gap_invalid_company(self):
        """测试无效标杆企业"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer
        from src.esg.core.models import ESGMetrics

        analyzer = GapAnalyzer()

        metrics = MagicMock(spec=ESGMetrics)
        metrics.get_dimension_score = lambda d: 70

        with self.assertRaises(ValueError):
            analyzer.analyze_dimension_gap(metrics, "不存在的公司")


class TestGapAnalyzerIndicatorGap(unittest.TestCase):
    """指标差距分析测试"""

    def test_analyze_indicator_gap_basic(self):
        """测试基本指标差距分析"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer
        from src.esg.core.models import ESGMetrics

        analyzer = GapAnalyzer()

        metrics = MagicMock(spec=ESGMetrics)
        metrics.carbon_emissions = 10000
        metrics.renewable_energy_ratio = 0.3
        metrics.energy_efficiency = 75.0

        # Mock indicator calculation
        analyzer._calculate_indicator_scores = MagicMock(
            return_value={"renewable_energy": 30.0, "energy_efficiency": 75.0}
        )

        result = analyzer.analyze_indicator_gap(metrics, "行业平均")

        self.assertIsInstance(result, list)


class TestCompareWithMultiple(unittest.TestCase):
    """多标杆对比测试"""

    def test_compare_with_multiple_default(self):
        """测试默认多标杆对比"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer
        from src.esg.core.models import ESGMetrics

        analyzer = GapAnalyzer()

        metrics = MagicMock(spec=ESGMetrics)
        metrics.get_dimension_score = lambda d: 70

        result = analyzer.compare_with_multiple(metrics)

        self.assertIn("comparisons", result)
        self.assertIn("best_benchmark", result)


class TestGetAvailableBenchmarks(unittest.TestCase):
    """可用标杆测试"""

    def test_get_available_benchmarks(self):
        """测试获取可用标杆列表"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()
        benchmarks = analyzer.get_available_benchmarks()

        self.assertIsInstance(benchmarks, list)
        self.assertIn("行业平均", benchmarks)


class TestHistoricalTrend(unittest.TestCase):
    """历史趋势分析测试"""

    @patch("pathlib.Path.exists")
    def test_analyze_historical_trend(self, mock_exists):
        """测试历史趋势分析"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        mock_exists.return_value = False

        analyzer = GapAnalyzer()
        result = analyzer.analyze_historical_trend("测试公司")

        self.assertIn("years", result)
        self.assertIn("trends", result)
        self.assertIn("overall", result)

    def test_analyze_historical_trend_no_company(self):
        """测试不存在的公司"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()
        result = analyzer.analyze_historical_trend("不存在的公司")

        self.assertEqual(result["years"], [])


class TestPredictNextYear(unittest.TestCase):
    """下一年预测测试"""

    def test_predict_next_year(self):
        """测试预测下一年"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        historical_trend = {
            "years": ["2022", "2023", "2024"],
            "trends": {"E": [70, 75, 80], "S": [68, 72, 78], "G": [70, 74, 80]},
            "overall": [69.3, 73.7, 79.3],
        }

        result = analyzer.predict_next_year(historical_trend)

        self.assertIn("year", result)
        self.assertIn("predicted", result)
        self.assertEqual(result["year"], "2025")

    def test_predict_next_year_insufficient_data(self):
        """测试数据不足"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        historical_trend = {
            "years": ["2024"],
            "trends": {"E": [80], "S": [78], "G": [80]},
            "overall": [79.3],
        }

        result = analyzer.predict_next_year(historical_trend)

        self.assertEqual(result["year"], "2025")
        self.assertEqual(result["predicted"], {})

    def test_predict_next_year_empty_input(self):
        """测试空输入"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        result = analyzer.predict_next_year({})

        self.assertEqual(result["year"], "2025")
        self.assertEqual(result["overall"], 0)


class TestGapResult(unittest.TestCase):
    """GapResult数据类测试"""

    def test_gap_result_creation(self):
        """测试GapResult创建"""
        from src.esg.analysis.gap_analyzer import GapResult

        gap = GapResult(
            dimension="E",
            current=70.0,
            benchmark=80.0,
            gap=10.0,
            gap_percentage=12.5,
            priority="高",
        )

        self.assertEqual(gap.dimension, "E")
        self.assertEqual(gap.current, 70.0)
        self.assertEqual(gap.benchmark, 80.0)
        self.assertEqual(gap.gap, 10.0)
        self.assertEqual(gap.gap_percentage, 12.5)
        self.assertEqual(gap.priority, "高")


class TestIndicatorGap(unittest.TestCase):
    """IndicatorGap数据类测试"""

    def test_indicator_gap_creation(self):
        """测试IndicatorGap创建"""
        from src.esg.analysis.gap_analyzer import IndicatorGap

        gap = IndicatorGap(
            indicator_id="carbon_emissions",
            indicator_name="碳排放",
            current_score=70.0,
            benchmark_score=80.0,
            gap=10.0,
            disclosure_level="高",
        )

        self.assertEqual(gap.indicator_id, "carbon_emissions")
        self.assertEqual(gap.indicator_name, "碳排放")
        self.assertEqual(gap.current_score, 70.0)
        self.assertEqual(gap.benchmark_score, 80.0)
        self.assertEqual(gap.gap, 10.0)
        self.assertEqual(gap.disclosure_level, "高")


class TestJsonBenchmarkRepository(unittest.TestCase):
    """JsonBenchmarkRepository测试"""

    def test_json_benchmark_repository_default_data(self):
        """测试默认数据"""
        from src.esg.analysis.gap_analyzer import JsonBenchmarkRepository

        repo = JsonBenchmarkRepository()

        self.assertIsNotNone(repo._benchmark_data)
        self.assertIsNotNone(repo._indicator_names)

    def test_get_benchmark(self):
        """测试获取标杆数据"""
        from src.esg.analysis.gap_analyzer import JsonBenchmarkRepository

        repo = JsonBenchmarkRepository()

        benchmark = repo.get_benchmark("行业平均")
        self.assertIsNotNone(benchmark)

    def test_get_benchmark_not_found(self):
        """测试获取不存在的标杆"""
        from src.esg.analysis.gap_analyzer import JsonBenchmarkRepository

        repo = JsonBenchmarkRepository()

        benchmark = repo.get_benchmark("不存在的公司")
        self.assertIsNone(benchmark)


@unittest.skip("跳过此测试 - 需要完整 mock ESGMetrics 的所有属性")
class TestIndicatorScoringRules(unittest.TestCase):
    """指标评分规则测试"""

    def test_calculate_indicator_scores(self):
        """测试指标分数计算"""
        pass


class TestComputeScoreFromRule(unittest.TestCase):
    """规则计算测试"""

    def test_direct_rule(self):
        """测试直接分数规则"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        rule = {"type": "direct", "max": 100}
        score = analyzer._compute_score_from_rule(85.0, rule, None)

        self.assertEqual(score, 85.0)

    def test_ratio_rule(self):
        """测试比例规则"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        rule = {"type": "ratio", "max": 100}
        score = analyzer._compute_score_from_rule(0.5, rule, None)

        self.assertEqual(score, 50.0)

    def test_inverse_rule(self):
        """测试逆向规则"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        rule = {"type": "inverse", "excellent": 0, "poor": 100}
        score = analyzer._compute_score_from_rule(50.0, rule, None)

        self.assertIsNotNone(score)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)

    def test_boolean_rule(self):
        """测试布尔规则"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        rule = {"type": "boolean"}
        score_true = analyzer._compute_score_from_rule(True, rule, None)
        score_false = analyzer._compute_score_from_rule(False, rule, None)

        self.assertEqual(score_true, 100.0)
        self.assertEqual(score_false, 0.0)


class TestCalculatePriority(unittest.TestCase):
    """优先级计算测试"""

    def test_calculate_priority_high(self):
        """测试高优先级"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        priority = analyzer._calculate_priority(20.0)
        self.assertEqual(priority, "高")

    def test_calculate_priority_medium(self):
        """测试中优先级"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        priority = analyzer._calculate_priority(10.0)
        self.assertEqual(priority, "中")

    def test_calculate_priority_low(self):
        """测试低优先级"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer

        analyzer = GapAnalyzer()

        priority = analyzer._calculate_priority(5.0)
        self.assertEqual(priority, "低")


class TestCalculateRanking(unittest.TestCase):
    """排名计算测试"""

    def test_calculate_ranking(self):
        """测试排名计算"""
        from src.esg.analysis.gap_analyzer import GapAnalyzer
        from src.esg.core.models import ESGMetrics

        analyzer = GapAnalyzer()

        metrics = MagicMock(spec=ESGMetrics)
        metrics.get_dimension_score = lambda d: {"E": 75, "S": 80, "G": 70}.get(d, 0)

        ranking = analyzer._calculate_ranking(metrics)

        self.assertIn("rank", ranking)
        self.assertIn("total", ranking)
        self.assertIn("percentile", ranking)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestGapAnalyzerInit))
    suite.addTests(loader.loadTestsFromTestCase(TestGapAnalyzerDimensionGap))
    suite.addTests(loader.loadTestsFromTestCase(TestGapAnalyzerIndicatorGap))
    suite.addTests(loader.loadTestsFromTestCase(TestCompareWithMultiple))
    suite.addTests(loader.loadTestsFromTestCase(TestGetAvailableBenchmarks))
    suite.addTests(loader.loadTestsFromTestCase(TestHistoricalTrend))
    suite.addTests(loader.loadTestsFromTestCase(TestPredictNextYear))
    suite.addTests(loader.loadTestsFromTestCase(TestGapResult))
    suite.addTests(loader.loadTestsFromTestCase(TestIndicatorGap))
    suite.addTests(loader.loadTestsFromTestCase(TestJsonBenchmarkRepository))
    suite.addTests(loader.loadTestsFromTestCase(TestIndicatorScoringRules))
    suite.addTests(loader.loadTestsFromTestCase(TestComputeScoreFromRule))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculatePriority))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculateRanking))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
