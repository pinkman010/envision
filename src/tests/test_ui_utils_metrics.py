"""指标处理工具单元测试

覆盖esg.ui.utils.metrics模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCreateMetricsFromExtraction(unittest.TestCase):
    """从提取结果创建ESGMetrics对象的测试"""

    def test_create_metrics_from_extraction_basic(self):
        """测试基本功能"""
        from src.esg.core.models import ESGMetrics
        from src.esg.ui.utils.metrics import create_metrics_from_extraction

        # 创建模拟的提取结果
        mock_result = MagicMock()
        mock_result.company_name = "测试公司"
        mock_result.year = 2024

        # 创建模拟的metrics字典
        mock_metric = MagicMock()
        mock_metric.value = 100.0
        mock_metric.confidence = 0.9

        mock_result.metrics = {
            "carbon_emissions": mock_metric,
            "renewable_energy_ratio": mock_metric,
            "energy_efficiency": mock_metric,
            "water_consumption": mock_metric,
            "waste_recycling_rate": mock_metric,
            "employee_count": mock_metric,
            "female_ratio": mock_metric,
            "training_hours": mock_metric,
            "safety_incidents": mock_metric,
            "community_investment": mock_metric,
            "board_independence_ratio": mock_metric,
            "ethics_training_coverage": mock_metric,
            "esg_report_quality": mock_metric,
        }

        result = create_metrics_from_extraction(mock_result)

        self.assertIsInstance(result, ESGMetrics)
        self.assertEqual(result.company_name, "测试公司")
        self.assertEqual(result.year, 2024)

    def test_create_metrics_with_none_values(self):
        """测试包含None值的情况"""
        from src.esg.core.models import ESGMetrics
        from src.esg.ui.utils.metrics import create_metrics_from_extraction

        mock_result = MagicMock()
        mock_result.company_name = "测试公司"
        mock_result.year = 2024

        # 所有metrics都是None
        mock_result.metrics = {
            "carbon_emissions": None,
            "renewable_energy_ratio": None,
        }

        result = create_metrics_from_extraction(mock_result)

        self.assertIsInstance(result, ESGMetrics)
        self.assertIsNone(result.carbon_emissions)
        self.assertIsNone(result.renewable_energy_ratio)

    def test_create_metrics_with_missing_keys(self):
        """测试缺失键的情况"""
        from src.esg.core.models import ESGMetrics
        from src.esg.ui.utils.metrics import create_metrics_from_extraction

        mock_result = MagicMock()
        mock_result.company_name = "测试公司"
        mock_result.year = 2024

        # 只有部分metrics
        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_metric.confidence = 0.8

        mock_result.metrics = {
            "carbon_emissions": mock_metric,
        }

        result = create_metrics_from_extraction(mock_result)

        self.assertIsInstance(result, ESGMetrics)
        self.assertEqual(result.carbon_emissions, 50.0)
        self.assertIsNone(result.renewable_energy_ratio)

    def test_create_metrics_with_metric_without_value(self):
        """测试metric没有value属性的情况"""
        from src.esg.core.models import ESGMetrics
        from src.esg.ui.utils.metrics import create_metrics_from_extraction

        mock_result = MagicMock()
        mock_result.company_name = "测试公司"
        mock_result.year = 2024

        # metric没有value属性
        mock_metric = MagicMock()
        del mock_metric.value
        mock_metric.confidence = 0.8

        mock_result.metrics = {
            "carbon_emissions": mock_metric,
        }

        result = create_metrics_from_extraction(mock_result)

        self.assertIsInstance(result, ESGMetrics)
        self.assertIsNone(result.carbon_emissions)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_empty_metrics_dict(self):
        """测试空字典"""
        from src.esg.core.models import ESGMetrics
        from src.esg.ui.utils.metrics import create_metrics_from_extraction

        mock_result = MagicMock()
        mock_result.company_name = "测试公司"
        mock_result.year = 2024
        mock_result.metrics = {}

        result = create_metrics_from_extraction(mock_result)

        self.assertIsInstance(result, ESGMetrics)
        self.assertEqual(result.company_name, "测试公司")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCreateMetricsFromExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
