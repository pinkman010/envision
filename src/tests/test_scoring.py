"""ESG评分计算器单元测试

覆盖ScoreCalculator的各种评分计算方法和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.core.scoring import (
    E_DIMENSION_WEIGHTS,
    S_DIMENSION_WEIGHTS,
    ScoreCalculator,
    _calculate_weighted_score,
    get_score_calculator,
)


class TestScoreCalculator(unittest.TestCase):
    """评分计算器测试类"""

    def setUp(self):
        """测试前置设置"""
        self.calculator = ScoreCalculator()

    def test_calculate_carbon_intensity_score_excellent(self):
        """测试碳强度得分 - 优秀水平"""
        # 低于优秀阈值(0.25)，得满分 - 使用0.1吨CO2e/百万元
        score = self.calculator.calculate_carbon_intensity_score(0.1)
        self.assertEqual(score, 100.0)

    def test_calculate_carbon_intensity_score_poor(self):
        """测试碳强度得分 - 较差水平"""
        # 高于较差阈值(0.85)，得0分 - 使用1.0吨CO2e/百万元
        score = self.calculator.calculate_carbon_intensity_score(1.0)
        self.assertEqual(score, 0.0)

    def test_calculate_carbon_intensity_score_middle(self):
        """测试碳强度得分 - 中等水平"""
        # 中间值，线性插值 - 0.55吨CO2e/百万元
        score = self.calculator.calculate_carbon_intensity_score(0.55)
        # (0.55 - 0.25) / (0.85 - 0.25) = 0.3/0.6 = 0.5
        # 100 * (1 - 0.5) = 50
        self.assertAlmostEqual(score, 50.0, places=5)

    def test_calculate_carbon_intensity_score_none(self):
        """测试碳强度得分 - None输入"""
        score = self.calculator.calculate_carbon_intensity_score(None)
        self.assertIsNone(score)

    def test_calculate_water_intensity_score_excellent(self):
        """测试水资源强度得分 - 优秀水平"""
        score = self.calculator.calculate_water_intensity_score(10.0)
        self.assertEqual(score, 100.0)

    def test_calculate_water_intensity_score_poor(self):
        """测试水资源强度得分 - 较差水平"""
        score = self.calculator.calculate_water_intensity_score(100.0)
        self.assertEqual(score, 0.0)

    def test_calculate_water_intensity_score_middle(self):
        """测试水资源强度得分 - 中等水平"""
        score = self.calculator.calculate_water_intensity_score(50.0)
        # (50 - 15) / (100 - 15) = 35/85 ≈ 0.412
        # 100 * (1 - 0.412) ≈ 58.8
        self.assertAlmostEqual(score, 58.82, places=1)

    def test_calculate_water_intensity_score_none(self):
        """测试水资源强度得分 - None输入"""
        score = self.calculator.calculate_water_intensity_score(None)
        self.assertIsNone(score)

    def test_calculate_curtailment_score_excellent(self):
        """测试弃电率得分 - 优秀水平"""
        score = self.calculator.calculate_curtailment_score(1.0)
        self.assertEqual(score, 100.0)

    def test_calculate_curtailment_score_poor(self):
        """测试弃电率得分 - 较差水平"""
        score = self.calculator.calculate_curtailment_score(12.0)
        self.assertEqual(score, 0.0)

    def test_calculate_curtailment_score_middle(self):
        """测试弃电率得分 - 中等水平"""
        score = self.calculator.calculate_curtailment_score(6.0)
        # (6 - 2) / 8 = 0.5
        # 100 * (1 - 0.5) = 50
        self.assertEqual(score, 50.0)

    def test_calculate_curtailment_score_none(self):
        """测试弃电率得分 - None输入"""
        score = self.calculator.calculate_curtailment_score(None)
        self.assertIsNone(score)

    def test_calculate_trir_score_excellent(self):
        """测试TRIR得分 - 优秀水平"""
        score = self.calculator.calculate_trir_score(0.5)
        self.assertEqual(score, 100.0)

    def test_calculate_trir_score_poor(self):
        """测试TRIR得分 - 较差水平"""
        score = self.calculator.calculate_trir_score(4.0)
        self.assertEqual(score, 0.0)

    def test_calculate_trir_score_middle(self):
        """测试TRIR得分 - 中等水平"""
        score = self.calculator.calculate_trir_score(2.0)
        # (2 - 1) / (3 - 1) = 0.5
        # 100 * (1 - 0.5) = 50
        self.assertEqual(score, 50.0)

    def test_calculate_trir_score_none(self):
        """测试TRIR得分 - None输入"""
        score = self.calculator.calculate_trir_score(None)
        self.assertIsNone(score)

    def test_calculate_ltifr_score_excellent(self):
        """测试LTIFR得分 - 优秀水平"""
        score = self.calculator.calculate_ltifr_score(0.1)
        self.assertEqual(score, 100.0)

    def test_calculate_ltifr_score_poor(self):
        """测试LTIFR得分 - 较差水平"""
        score = self.calculator.calculate_ltifr_score(1.5)
        self.assertEqual(score, 0.0)

    def test_calculate_ltifr_score_middle(self):
        """测试LTIFR得分 - 中等水平"""
        score = self.calculator.calculate_ltifr_score(0.5)
        # (0.5 - 0.2) / (1.0 - 0.2) = 0.3/0.8 = 0.375
        # 100 * (1 - 0.375) = 62.5
        self.assertEqual(score, 62.5)

    def test_calculate_ltifr_score_none(self):
        """测试LTIFR得分 - None输入"""
        score = self.calculator.calculate_ltifr_score(None)
        self.assertIsNone(score)

    def test_calculate_safety_investment_score(self):
        """测试安全投入占比评分"""
        # 2%得100分
        score = self.calculator.calculate_safety_investment_score(2.0)
        self.assertEqual(score, 100.0)

        # 1%得50分
        score = self.calculator.calculate_safety_investment_score(1.0)
        self.assertEqual(score, 50.0)

        # 超过2%截断为100
        score = self.calculator.calculate_safety_investment_score(5.0)
        self.assertEqual(score, 100.0)

    def test_calculate_safety_investment_score_none(self):
        """测试安全投入占比评分 - None输入"""
        score = self.calculator.calculate_safety_investment_score(None)
        self.assertIsNone(score)

    def test_safe_score_basic(self):
        """测试safe_score基本功能"""
        score = self.calculator.safe_score(50.0)
        self.assertEqual(score, 50.0)

    def test_safe_score_with_multiplier(self):
        """测试safe_score带乘数"""
        score = self.calculator.safe_score(50.0, multiplier=2.0)
        self.assertEqual(score, 100.0)

    def test_safe_score_exceeds_max(self):
        """测试safe_score超过最大值"""
        score = self.calculator.safe_score(150.0, max_val=100.0)
        self.assertEqual(score, 100.0)

    def test_safe_score_none(self):
        """测试safe_score - None输入"""
        score = self.calculator.safe_score(None)
        self.assertIsNone(score)

    def test_calculate_percentage_score(self):
        """测试百分比得分"""
        score = self.calculator.calculate_percentage_score(80.0)
        self.assertEqual(score, 80.0)

        # 超过100截断
        score = self.calculator.calculate_percentage_score(150.0)
        self.assertEqual(score, 100.0)

    def test_calculate_percentage_score_none(self):
        """测试百分比得分 - None输入"""
        score = self.calculator.calculate_percentage_score(None)
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


class TestDimensionScoreCalculation(unittest.TestCase):
    """维度得分计算测试"""

    def setUp(self):
        """测试前置设置"""
        self.calculator = ScoreCalculator()
        # 创建Mock的ESGMetrics对象
        self.mock_metrics = MagicMock()

    def test_calculate_e_dimension_scores(self):
        """测试E维度得分计算"""
        # 设置E维度所需指标 - 使用真实值
        self.mock_metrics.carbon_intensity = 0.5  # 碳强度（吨CO2e/百万元）
        self.mock_metrics.industry_sector = "new_energy_composite"
        self.mock_metrics.renewable_energy_ratio = 50.0  # 可再生能源比例
        self.mock_metrics.energy_efficiency = 75.0  # 能源效率
        self.mock_metrics.waste_recycling_rate = 0.6  # 废弃物回收率
        self.mock_metrics.water_intensity = 30.0  # 水资源强度
        # 新能源特色指标
        self.mock_metrics.turbine_availability = None
        self.mock_metrics.curtailment_rate = None
        self.mock_metrics.battery_cycle_life = None
        self.mock_metrics.battery_recycling_rate = None
        self.mock_metrics.electrolysis_efficiency = None
        self.mock_metrics.energy_storage_safety_score = None
        # 范围3指标
        self.mock_metrics.scope3_coverage_percentage = None
        self.mock_metrics.sbti_target = None
        self.mock_metrics.carbon_emissions = None

        scores = self.calculator.calculate_dimension_scores(self.mock_metrics, "E")

        self.assertIsInstance(scores, list)
        self.assertEqual(len(scores), 11)  # E维度有11个指标

    def test_calculate_s_dimension_scores(self):
        """测试S维度得分计算"""
        # 设置S维度所需指标
        self.mock_metrics.female_ratio = 35.0
        self.mock_metrics.female_executive_ratio = 20.0
        self.mock_metrics.training_hours = 30.0
        self.mock_metrics.local_employment_ratio = 80.0
        self.mock_metrics.community_investment_per_revenue = 0.5
        # 设置其他S维度属性为None
        self.mock_metrics.trir = None
        self.mock_metrics.ltifr = None
        self.mock_metrics.safety_investment_ratio = None

        scores = self.calculator.calculate_dimension_scores(self.mock_metrics, "S")

        self.assertIsInstance(scores, list)

    def test_calculate_g_dimension_scores(self):
        """测试G维度得分计算"""
        # 设置G维度所需指标
        self.mock_metrics.board_independence_ratio = 50.0
        self.mock_metrics.esg_committee_independence = 60.0
        self.mock_metrics.ethics_training_coverage = 90.0
        self.mock_metrics.anti_corruption_training_coverage = 85.0
        self.mock_metrics.esg_report_quality = 80.0
        self.mock_metrics.whistleblower_protection = True

        # Mock气候治理对象
        mock_climate_gov = MagicMock()
        mock_climate_gov.get_score.return_value = 75.0
        self.mock_metrics.climate_governance = mock_climate_gov

        # Mock TCFD披露对象
        mock_tcfd = MagicMock()
        mock_tcfd.get_score.return_value = 80.0
        self.mock_metrics.tcfd_disclosure = mock_tcfd

        scores = self.calculator.calculate_dimension_scores(self.mock_metrics, "G")

        self.assertIsInstance(scores, list)
        self.assertEqual(len(scores), 8)  # G维度有8个指标

    def test_calculate_dimension_score_e(self):
        """测试E维度综合得分"""
        # 使用真实值设置
        self.mock_metrics.carbon_intensity = 0.5
        self.mock_metrics.industry_sector = "new_energy_composite"
        self.mock_metrics.renewable_energy_ratio = 50.0
        self.mock_metrics.energy_efficiency = 75.0
        self.mock_metrics.waste_recycling_rate = 0.6
        self.mock_metrics.water_intensity = 30.0
        # 新能源特色指标设为None
        self.mock_metrics.turbine_availability = None
        self.mock_metrics.curtailment_rate = None
        self.mock_metrics.battery_cycle_life = None
        self.mock_metrics.battery_recycling_rate = None
        self.mock_metrics.electrolysis_efficiency = None
        self.mock_metrics.energy_storage_safety_score = None
        self.mock_metrics.scope3_coverage_percentage = None
        self.mock_metrics.sbti_target = None
        self.mock_metrics.carbon_emissions = None

        score = self.calculator.calculate_dimension_score(self.mock_metrics, "E")

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_calculate_dimension_score_s(self):
        """测试S维度综合得分"""
        self.mock_metrics.female_ratio = 35.0
        self.mock_metrics.female_executive_ratio = 20.0
        self.mock_metrics.training_hours = 30.0
        self.mock_metrics.local_employment_ratio = 80.0
        self.mock_metrics.community_investment_per_revenue = 0.5
        self.mock_metrics.trir = None
        self.mock_metrics.ltifr = None
        self.mock_metrics.safety_investment_ratio = None

        score = self.calculator.calculate_dimension_score(self.mock_metrics, "S")

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_calculate_dimension_score_g(self):
        """测试G维度综合得分"""
        self.mock_metrics.board_independence_ratio = 50.0
        self.mock_metrics.esg_committee_independence = 60.0
        self.mock_metrics.ethics_training_coverage = 90.0
        self.mock_metrics.anti_corruption_training_coverage = 85.0
        self.mock_metrics.esg_report_quality = 80.0
        self.mock_metrics.whistleblower_protection = True
        self.mock_metrics.climate_governance = None
        self.mock_metrics.tcfd_disclosure = None

        score = self.calculator.calculate_dimension_score(self.mock_metrics, "G")

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_calculate_dimension_score_invalid_dimension(self):
        """测试无效维度"""
        self.mock_metrics.carbon_intensity = 0.5

        score = self.calculator.calculate_dimension_score(self.mock_metrics, "X")

        # 无效维度使用简单平均
        self.assertIsInstance(score, float)


class TestGetScoreCalculator(unittest.TestCase):
    """全局评分计算器实例测试"""

    def test_get_score_calculator(self):
        """测试获取全局评分计算器"""
        calc1 = get_score_calculator()
        calc2 = get_score_calculator()

        self.assertIs(calc1, calc2)  # 应该是单例


class TestDimensionWeights(unittest.TestCase):
    """权重配置测试"""

    def test_e_dimension_weights_sum(self):
        """测试E维度权重总和"""
        total = sum(E_DIMENSION_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_s_dimension_weights_sum(self):
        """测试S维度权重总和"""
        total = sum(S_DIMENSION_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestScoreCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculateWeightedScore))
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionScoreCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestGetScoreCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionWeights))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
