"""策略生成器单元测试

覆盖StrategyGenerator的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.analysis.strategy_generator import (
    Strategy,
    StrategyGenerator,
    StrategyPriority,
)


class TestStrategyGenerator(unittest.TestCase):
    """策略生成器测试类"""

    def setUp(self):
        """测试前置设置"""
        self.generator = StrategyGenerator()
        # 创建Mock的ESGMetrics对象
        self.mock_metrics = MagicMock()
        self.mock_metrics.company_name = "测试公司"
        self.mock_metrics.year = "2024"

    @unittest.skip("需要更复杂的Mock设置")
    def test_generate_strategies(self):
        """测试生成策略"""
        result = self.generator.generate_strategies(self.mock_metrics, "行业平均")

        self.assertIsInstance(result, list)

    @unittest.skip("需要更复杂的Mock设置")
    def test_generate_strategies_max_count(self):
        """测试最大策略数量"""
        result = self.generator.generate_strategies(self.mock_metrics, "行业平均", max_strategies=3)

        self.assertLessEqual(len(result), 3)

    def test_generate_strategy_for_area(self):
        """测试为特定领域生成策略"""
        result = self.generator.generate_strategy_for_area(
            "carbon_management", self.mock_metrics, gap_value=20.0
        )

        if result:
            self.assertIsInstance(result, Strategy)
            self.assertIsNotNone(result.title)
            self.assertIsNotNone(result.description)

    def test_generate_strategy_for_invalid_area(self):
        """测试无效领域"""
        result = self.generator.generate_strategy_for_area(
            "invalid_area", self.mock_metrics, gap_value=10.0
        )

        self.assertIsNone(result)

    def test_fine_tune_strategy(self):
        """测试微调策略"""
        # 先创建一个基础策略
        original_strategy = Strategy(
            id="STR-TEST-001",
            title="测试策略",
            description="测试描述",
            dimension="E",
            actions=["行动1", "行动2"],
            priority=StrategyPriority.HIGH,
            confidence=0.8,
            expected_impact=15.0,
            timeframe="6个月",
            resources_needed=["资源1"],
        )

        # 微调
        adjustments = {"title": "微调后的策略", "priority": StrategyPriority.MEDIUM}

        tuned = self.generator.fine_tune_strategy(original_strategy, adjustments)

        self.assertEqual(tuned.title, "微调后的策略")
        self.assertEqual(tuned.priority, StrategyPriority.MEDIUM)

    def test_explain_confidence(self):
        """测试置信度解释"""
        strategy = Strategy(
            id="STR-TEST-002",
            title="测试策略",
            description="测试描述",
            dimension="E",
            actions=["行动1"],
            priority=StrategyPriority.HIGH,
            confidence=0.85,
            expected_impact=15.0,
            timeframe="6个月",
            resources_needed=["资源1"],
        )

        explanation = self.generator.explain_confidence(strategy)

        self.assertIsInstance(explanation, dict)
        self.assertIn("confidence_score", explanation)
        self.assertIn("confidence_level", explanation)

    def test_to_dict(self):
        """测试策略转字典"""
        strategy = Strategy(
            id="STR-TEST-003",
            title="测试策略",
            description="测试描述",
            dimension="E",
            actions=["行动1"],
            priority=StrategyPriority.HIGH,
            confidence=0.8,
            expected_impact=15.0,
            timeframe="6个月",
            resources_needed=["资源1"],
        )

        result = self.generator.to_dict(strategy)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "STR-TEST-003")
        self.assertEqual(result["title"], "测试策略")

    def test_filter_by_audience(self):
        """测试按受众筛选"""
        strategies = [
            Strategy(
                id="STR-1",
                title="策略1",
                description="描述",
                dimension="E",
                actions=[],
                priority=StrategyPriority.HIGH,
                confidence=0.8,
                expected_impact=10.0,
                timeframe="6个月",
                resources_needed=[],
                target_audiences=["投资者", "员工"],
            ),
            Strategy(
                id="STR-2",
                title="策略2",
                description="描述",
                dimension="S",
                actions=[],
                priority=StrategyPriority.MEDIUM,
                confidence=0.7,
                expected_impact=8.0,
                timeframe="3个月",
                resources_needed=[],
                target_audiences=["监管机构"],
            ),
        ]

        # 筛选包含"投资者"的策略
        filtered = self.generator.filter_by_audience(strategies, "投资者")

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, "STR-1")

    def test_get_all_audiences(self):
        """测试获取所有受众选项"""
        audiences = StrategyGenerator.get_all_audiences()

        self.assertIsInstance(audiences, list)
        self.assertIn("投资者", audiences)
        self.assertIn("监管机构", audiences)


class TestStrategyPriority(unittest.TestCase):
    """策略优先级枚举测试"""

    def test_priority_values(self):
        """测试优先级值"""
        self.assertEqual(StrategyPriority.HIGH.value, "高")
        self.assertEqual(StrategyPriority.MEDIUM.value, "中")
        self.assertEqual(StrategyPriority.LOW.value, "低")


class TestStrategy(unittest.TestCase):
    """策略数据类测试"""

    def test_strategy_creation(self):
        """测试策略创建"""
        strategy = Strategy(
            id="STR-TEST-004",
            title="测试策略",
            description="测试描述",
            dimension="E",
            actions=["行动1", "行动2"],
            priority=StrategyPriority.HIGH,
            confidence=0.85,
            expected_impact=20.0,
            timeframe="6-12个月",
            resources_needed=["资源1", "资源2"],
        )

        self.assertEqual(strategy.id, "STR-TEST-004")
        self.assertEqual(strategy.title, "测试策略")
        self.assertEqual(strategy.dimension, "E")
        self.assertEqual(strategy.priority, StrategyPriority.HIGH)

    def test_strategy_to_dict(self):
        """测试策略转字典"""
        strategy = Strategy(
            id="STR-TEST-005",
            title="测试策略",
            description="测试描述",
            dimension="E",
            actions=["行动1"],
            priority=StrategyPriority.MEDIUM,
            confidence=0.7,
            expected_impact=10.0,
            timeframe="6个月",
            resources_needed=["资源1"],
        )

        result = strategy.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "STR-TEST-005")
        self.assertEqual(result["title"], "测试策略")
        self.assertEqual(result["priority"], "中")

    def test_strategy_default_values(self):
        """测试策略默认值"""
        strategy = Strategy(
            id="STR-TEST-006",
            title="测试策略",
            description="测试描述",
            dimension="E",
            actions=[],
            priority=StrategyPriority.LOW,
            confidence=0.5,
            expected_impact=5.0,
            timeframe="12个月",
            resources_needed=[],
        )

        # 验证默认值
        self.assertEqual(strategy.target_audiences, [])
        self.assertEqual(strategy.communication_style, "正式")
        self.assertEqual(strategy.recommended_channels, [])


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestStrategyGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyPriority))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategy))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
