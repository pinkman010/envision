"""UI组件单元测试

覆盖components模块的各种使用场景。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestESGColors(unittest.TestCase):
    """ESG颜色常量测试"""

    def test_import_esg_colors(self):
        """测试导入ESG_COLORS"""
        try:
            from src.esg.ui.components import ESG_COLORS

            self.assertIsInstance(ESG_COLORS, dict)
        except ImportError:
            self.fail("无法导入ESG_COLORS")


class TestESGDimensionNames(unittest.TestCase):
    """ESG维度名称测试"""

    def test_import_esg_dimension_names(self):
        """测试导入ESG_DIMENSION_NAMES"""
        try:
            from src.esg.ui.components import ESG_DIMENSION_NAMES

            self.assertIsInstance(ESG_DIMENSION_NAMES, dict)
        except ImportError:
            self.fail("无法导入ESG_DIMENSION_NAMES")


class TestGapCardData(unittest.TestCase):
    """差距卡片数据测试"""

    def test_import_gap_card_data(self):
        """测试导入GapCardData"""
        try:
            from src.esg.ui.components import GapCardData

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入GapCardData")

    def test_gap_card_data_creation(self):
        """测试创建GapCardData"""
        from src.esg.ui.components import GapCardData

        data = GapCardData(dimension="E", current=60.0, benchmark=80.0, gap=20.0, priority="高")
        self.assertEqual(data.dimension, "E")
        self.assertEqual(data.current, 60.0)


class TestScoreCardData(unittest.TestCase):
    """分数卡片数据测试"""

    def test_import_score_card_data(self):
        """测试导入ScoreCardData"""
        try:
            from src.esg.ui.components import ScoreCardData

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入ScoreCardData")

    def test_score_card_data_creation(self):
        """测试创建ScoreCardData"""
        from src.esg.ui.components import ScoreCardData

        data = ScoreCardData(
            title="ESG总分",
            score=85.0,
            max_score=100.0,
            description="环境、社会、治理综合得分",
            color="green",
        )
        self.assertEqual(data.title, "ESG总分")
        self.assertEqual(data.score, 85.0)


class TestStrategyCardData(unittest.TestCase):
    """策略卡片数据测试"""

    def test_import_strategy_card_data(self):
        """测试导入StrategyCardData"""
        try:
            from src.esg.ui.components import StrategyCardData

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入StrategyCardData")

    def test_strategy_card_data_creation(self):
        """测试创建StrategyCardData"""
        from src.esg.ui.components import StrategyCardData

        data = StrategyCardData(
            id="strategy_1",
            title="减排策略",
            description="减少碳排放",
            dimension="E",
            priority="高",
            confidence=0.85,
            actions=[],
            timeframe="短期",
            target_audiences=[],
            communication_style="专业",
            recommended_channels=[],
        )
        self.assertEqual(data.title, "减排策略")


class TestGetScoreColor(unittest.TestCase):
    """获取分数颜色测试"""

    def test_get_score_color_function(self):
        """测试get_score_color函数"""
        try:
            from src.esg.ui.components import get_score_color

            # 测试不同分数范围
            self.assertIsInstance(get_score_color(85.0), str)
            self.assertIsInstance(get_score_color(60.0), str)
            self.assertIsInstance(get_score_color(30.0), str)
        except ImportError:
            self.fail("无法导入get_score_color")


class TestGetConfidenceColor(unittest.TestCase):
    """获取置信度颜色测试"""

    def test_get_confidence_color_function(self):
        """测试get_confidence_color函数"""
        try:
            from src.esg.ui.components import get_confidence_color

            # 测试不同置信度
            self.assertIsInstance(get_confidence_color(0.9), str)
            self.assertIsInstance(get_confidence_color(0.5), str)
        except ImportError:
            self.fail("无法导入get_confidence_color")


class TestGetScoreEmoji(unittest.TestCase):
    """获取分数表情测试"""

    def test_get_score_emoji_function(self):
        """测试get_score_emoji函数"""
        try:
            from src.esg.ui.components import get_score_emoji

            # 测试不同分数
            self.assertIsInstance(get_score_emoji(85.0), str)
            self.assertIsInstance(get_score_emoji(60.0), str)
        except ImportError:
            self.fail("无法导入get_score_emoji")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestESGColors))
    suite.addTests(loader.loadTestsFromTestCase(TestESGDimensionNames))
    suite.addTests(loader.loadTestsFromTestCase(TestGapCardData))
    suite.addTests(loader.loadTestsFromTestCase(TestScoreCardData))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyCardData))
    suite.addTests(loader.loadTestsFromTestCase(TestGetScoreColor))
    suite.addTests(loader.loadTestsFromTestCase(TestGetConfidenceColor))
    suite.addTests(loader.loadTestsFromTestCase(TestGetScoreEmoji))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
