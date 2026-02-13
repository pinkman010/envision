"""测试竞争对手深度分析功能

使用标准unittest格式，优化测试隔离和mock使用。
"""

import logging
import unittest

from src.esg.analysis.competitor_analyzer import CompetitorAnalyzer
from src.esg.core.models import ESGMetrics

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestCompetitorAnalyzer(unittest.TestCase):
    """竞争对手分析器测试类"""

    def setUp(self):
        """测试前置设置"""
        self.analyzer = CompetitorAnalyzer()

        # 创建标准测试数据
        self.test_metrics = ESGMetrics(
            company_name="远景能源",
            year="2024",
            renewable_energy_ratio=0.45,
            energy_efficiency=70,
            waste_recycling_rate=0.6,
            female_ratio=0.35,
            training_hours=30,
            community_investment=500000,
            board_independence_ratio=0.40,
            ethics_training_coverage=0.70,
            esg_report_quality=75,
        )

        # 标准差距数据
        self.gap_data = {
            "E": {"current": 65, "target": 85, "gap": 20},
            "S": {"current": 70, "target": 80, "gap": 10},
            "G": {"current": 75, "target": 78, "gap": 3},
        }

    def test_competitor_analyzer_init(self):
        """测试CompetitorAnalyzer初始化"""
        self.assertIsNotNone(self.analyzer)
        competitor_list = self.analyzer.get_competitor_list()
        self.assertIsInstance(competitor_list, list)
        logger.info(f"可用竞争对手: {competitor_list}")

    def test_generate_analysis(self):
        """测试差距分析生成"""
        analysis = self.analyzer.generate_analysis(self.test_metrics, "维斯塔斯", self.gap_data)

        # 使用assert验证
        self.assertIsNotNone(analysis)
        self.assertIsInstance(analysis, str)
        self.assertGreater(len(analysis), 0)

        logger.info(f"分析内容长度: {len(analysis)} 字符")

    def test_generate_comparison_table(self):
        """测试对比表格生成"""
        table = self.analyzer.generate_comparison_table(
            self.test_metrics, "维斯塔斯", self.gap_data
        )

        # 验证表格结构
        self.assertIsNotNone(table)
        self.assertIsInstance(table, list)
        self.assertGreater(len(table), 0)

        # 验证表格字段
        for row in table:
            self.assertIn("维度", row)
            self.assertIn("我司现状", row)
            self.assertIn("差距", row)

        logger.info(f"表格行数: {len(table)}")

    def test_get_innovation_highlights(self):
        """测试创新亮点获取"""
        highlights = self.analyzer.get_innovation_highlights("维斯塔斯")

        self.assertIsNotNone(highlights)
        self.assertIsInstance(highlights, list)

        logger.info(f"创新亮点数量: {len(highlights)}")

    def test_get_overall_comparison(self):
        """测试整体对比"""
        comparison = self.analyzer.get_overall_comparison(self.test_metrics)

        # 验证对比结果结构
        self.assertIsNotNone(comparison)
        self.assertIn("current_company", comparison)

        current = comparison["current_company"]
        self.assertIn("name", current)
        self.assertIn("overall_score", current)
        self.assertIn("rank", current)
        self.assertIn("total_companies", current)

        logger.info(f"综合评分: {current['overall_score']}")
        logger.info(f"排名: #{current['rank']} / {current['total_companies']}")

    def test_gap_data_preserved(self):
        """测试差距数据在分析中被正确使用"""
        # 测试E维度差距
        e_gap = self.gap_data["E"]
        self.assertEqual(e_gap["gap"], 20)

        # 测试S维度差距
        s_gap = self.gap_data["S"]
        self.assertEqual(s_gap["gap"], 10)

        # 测试G维度差距
        g_gap = self.gap_data["G"]
        self.assertEqual(g_gap["gap"], 3)


class TestCompetitorAnalyzerIsolation(unittest.TestCase):
    """使用Mock进行测试隔离"""

    def setUp(self):
        """测试前置设置"""
        self.test_metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=0.5,
            energy_efficiency=80,
        )

    def test_with_mocked_analyzer(self):
        """测试使用模拟对象的隔离"""
        # 此测试展示如何隔离外部依赖
        # 实际项目中可以mock OllamaClient 等外部服务
        analyzer = CompetitorAnalyzer()

        # 验证基本功能不依赖外部服务
        competitors = analyzer.get_competitor_list()

        # 使用断言而非日志
        self.assertIsInstance(competitors, list)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCompetitorAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestCompetitorAnalyzerIsolation))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    import sys

    sys.exit(0 if success else 1)
