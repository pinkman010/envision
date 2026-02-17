"""ESG评分计算器单元测试

覆盖ESGMetrics的各种评分计算方法和边界情况。
已更新：使用ESGMetrics.get_dimension_score()替代已删除的ScoreCalculator类。
"""

import sys
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 从models模块导入
from src.esg.core.models import (
    E_DIMENSION_WEIGHTS,
    S_DIMENSION_WEIGHTS,
    ESGMetrics,
    _calculate_weighted_score,
)


class TestESGMetricsScoring(unittest.TestCase):
    """ESGMetrics评分测试类"""

    def test_get_dimension_score_e_with_carbon_intensity(self):
        """测试E维度得分 - 碳强度评分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            industry_sector="new_energy_composite",
            carbon_intensity=0.1,  # 低于优秀阈值
        )
        score = metrics.get_dimension_score("E")
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_dimension_score_e_with_water_intensity(self):
        """测试E维度得分 - 水资源强度评分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            water_intensity=10.0,  # 低于优秀阈值
        )
        score = metrics.get_dimension_score("E")
        self.assertIsInstance(score, float)

    def test_get_dimension_score_s_basic(self):
        """测试S维度基本得分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            female_ratio=35.0,
            training_hours=30.0,
            employee_count=1000,
        )
        score = metrics.get_dimension_score("S")
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_dimension_score_g_basic(self):
        """测试G维度基本得分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            board_independence_ratio=50.0,
            ethics_training_coverage=90.0,
        )
        score = metrics.get_dimension_score("G")
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_all_dimension_scores(self):
        """测试获取所有维度得分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_intensity=0.3,
            female_ratio=35.0,
            board_independence_ratio=50.0,
        )
        scores = metrics.get_all_dimension_scores()
        self.assertIn("E", scores)
        self.assertIn("S", scores)
        self.assertIn("G", scores)
        self.assertIsInstance(scores["E"], float)
        self.assertIsInstance(scores["S"], float)
        self.assertIsInstance(scores["G"], float)

    def test_has_dimension_data(self):
        """测试维度数据检测"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_intensity=0.3,
        )
        self.assertTrue(metrics.has_dimension_data("E"))
        self.assertFalse(metrics.has_dimension_data("S"))
        self.assertFalse(metrics.has_dimension_data("G"))


class TestCarbonIntensityScore(unittest.TestCase):
    """碳强度评分测试"""

    def test_carbon_intensity_excellent(self):
        """测试碳强度得分 - 优秀水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            industry_sector="new_energy_composite",
            carbon_intensity=0.1,  # 低于优秀阈值(0.25)
        )
        # 通过_calculate_carbon_intensity_score方法测试
        score = metrics._calculate_carbon_intensity_score()
        self.assertEqual(score, 100.0)

    def test_carbon_intensity_poor(self):
        """测试碳强度得分 - 较差水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            industry_sector="new_energy_composite",
            carbon_intensity=1.0,  # 高于较差阈值(0.85)
        )
        score = metrics._calculate_carbon_intensity_score()
        self.assertEqual(score, 0.0)

    def test_carbon_intensity_middle(self):
        """测试碳强度得分 - 中等水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            industry_sector="new_energy_composite",
            carbon_intensity=0.55,  # 中间值
        )
        score = metrics._calculate_carbon_intensity_score()
        # (0.55 - 0.25) / (0.85 - 0.25) = 0.3/0.6 = 0.5
        # 100 * (1 - 0.5) = 50
        self.assertAlmostEqual(score, 50.0, places=5)

    def test_carbon_intensity_none(self):
        """测试碳强度得分 - None输入"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
        )
        score = metrics._calculate_carbon_intensity_score()
        self.assertIsNone(score)


class TestWaterIntensityScore(unittest.TestCase):
    """水资源强度评分测试"""

    def test_water_intensity_excellent(self):
        """测试水资源强度得分 - 优秀水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            water_intensity=10.0,  # 低于优秀阈值(15)
        )
        score = metrics._calculate_water_intensity_score()
        self.assertEqual(score, 100.0)

    def test_water_intensity_poor(self):
        """测试水资源强度得分 - 较差水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            water_intensity=100.0,  # 等于较差阈值
        )
        score = metrics._calculate_water_intensity_score()
        self.assertEqual(score, 0.0)

    def test_water_intensity_middle(self):
        """测试水资源强度得分 - 中等水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            water_intensity=50.0,
        )
        score = metrics._calculate_water_intensity_score()
        # (50 - 15) / (100 - 15) = 35/85 ≈ 0.412
        # 100 * (1 - 0.412) ≈ 58.8
        self.assertAlmostEqual(score, 58.82, places=1)

    def test_water_intensity_none(self):
        """测试水资源强度得分 - None输入"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
        )
        score = metrics._calculate_water_intensity_score()
        self.assertIsNone(score)


class TestCurtailmentScore(unittest.TestCase):
    """弃电率评分测试"""

    def test_curtailment_excellent(self):
        """测试弃电率得分 - 优秀水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            curtailment_rate=1.0,  # 低于2%
        )
        score = metrics._calculate_curtailment_score()
        self.assertEqual(score, 100.0)

    def test_curtailment_poor(self):
        """测试弃电率得分 - 较差水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            curtailment_rate=12.0,  # 高于10%
        )
        score = metrics._calculate_curtailment_score()
        self.assertEqual(score, 0.0)

    def test_curtailment_middle(self):
        """测试弃电率得分 - 中等水平"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            curtailment_rate=6.0,
        )
        score = metrics._calculate_curtailment_score()
        # (6 - 2) / 8 = 0.5
        # 100 * (1 - 0.5) = 50
        self.assertEqual(score, 50.0)

    def test_curtailment_none(self):
        """测试弃电率得分 - None输入"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
        )
        score = metrics._calculate_curtailment_score()
        self.assertIsNone(score)


class TestCalculateWeightedScore(unittest.TestCase):
    """加权得分计算测试"""

    def test_all_valid_scores(self):
        """测试全部有效得分"""
        scores = [80.0, 90.0, 70.0]
        weights = [0.5, 0.3, 0.2]
        result = _calculate_weighted_score(scores, weights)
        # 80*0.5 + 90*0.3 + 70*0.2 = 40 + 27 + 14 = 81
        self.assertEqual(result, 81.0)

    def test_with_none_scores(self):
        """测试包含None得分"""
        scores = [80.0, None, 70.0]
        weights = [0.5, 0.3, 0.2]
        result = _calculate_weighted_score(scores, weights)
        # 权重归一化: 0.5/0.7, 0.2/0.7
        # 80*0.5/0.7 + 70*0.2/0.7 = 57.14 + 20 = 77.14
        self.assertAlmostEqual(result, 77.14, places=1)

    def test_all_none_scores(self):
        """测试全部None得分"""
        scores = [None, None, None]
        weights = [0.5, 0.3, 0.2]
        result = _calculate_weighted_score(scores, weights, default_score=50.0)
        self.assertEqual(result, 50.0)

    def test_zero_total_weight(self):
        """测试总权重为0"""
        scores = [80.0, 90.0]
        weights = [0.0, 0.0]
        result = _calculate_weighted_score(scores, weights, default_score=60.0)
        self.assertEqual(result, 60.0)


class TestDimensionWeights(unittest.TestCase):
    """权重配置测试"""

    def test_e_dimension_weights_sum(self):
        """测试E维度权重总和
        
        注意：E维度权重设计为0.85，因为scope3_coverage_score在计算中被移除。
        权重归一化函数会自动处理权重不足1.0的情况。
        """
        total = sum(E_DIMENSION_WEIGHTS.values())
        # E维度权重设计值为0.85（scope3_coverage已移除）
        self.assertGreater(total, 0.8)
        self.assertLess(total, 1.0)

    def test_s_dimension_weights_sum(self):
        """测试S维度权重总和"""
        total = sum(S_DIMENSION_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)


class TestSafeScore(unittest.TestCase):
    """安全评分测试"""

    def test_safe_score_basic(self):
        """测试safe_score基本功能"""
        metrics = ESGMetrics(company_name="测试公司", year="2024")
        score = metrics._safe_score(50.0, 100.0)
        self.assertEqual(score, 50.0)

    def test_safe_score_with_multiplier(self):
        """测试safe_score带乘数"""
        metrics = ESGMetrics(company_name="测试公司", year="2024")
        score = metrics._safe_score(50.0, 100.0, multiplier=2.0)
        self.assertEqual(score, 100.0)

    def test_safe_score_exceeds_max(self):
        """测试safe_score超过最大值"""
        metrics = ESGMetrics(company_name="测试公司", year="2024")
        score = metrics._safe_score(150.0, 100.0)
        self.assertEqual(score, 100.0)

    def test_safe_score_none(self):
        """测试safe_score - None输入"""
        metrics = ESGMetrics(company_name="测试公司", year="2024")
        score = metrics._safe_score(None, 100.0)
        self.assertIsNone(score)


class TestEmissionsCalculation(unittest.TestCase):
    """排放计算测试"""

    def test_get_total_emissions(self):
        """测试获取总排放"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            scope1_emissions=100.0,
            scope2_emissions_market=50.0,
            scope3_emissions=200.0,
        )
        total = metrics.get_total_emissions()
        self.assertEqual(total, 350.0)

    def test_get_scope1_2_emissions(self):
        """测试获取范围1+2排放"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            scope1_emissions=100.0,
            scope2_emissions_market=50.0,
        )
        total = metrics.get_scope1_2_emissions()
        self.assertEqual(total, 150.0)

    def test_get_emissions_breakdown(self):
        """测试排放分解"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            scope1_emissions=100.0,
            scope2_emissions_market=50.0,
            scope3_emissions=200.0,
        )
        breakdown = metrics.get_emissions_breakdown()
        self.assertEqual(breakdown["scope1"], 100.0)
        self.assertEqual(breakdown["scope2_market"], 50.0)
        self.assertEqual(breakdown["scope3_summary"], 200.0)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestESGMetricsScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestCarbonIntensityScore))
    suite.addTests(loader.loadTestsFromTestCase(TestWaterIntensityScore))
    suite.addTests(loader.loadTestsFromTestCase(TestCurtailmentScore))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculateWeightedScore))
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionWeights))
    suite.addTests(loader.loadTestsFromTestCase(TestSafeScore))
    suite.addTests(loader.loadTestsFromTestCase(TestEmissionsCalculation))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)