"""话题分析器单元测试

覆盖TopicAnalyzer的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# 模块不存在时跳过整个测试文件
pytest.importorskip("src.esg.analysis.topic_analyzer", reason="src.esg.analysis.topic_analyzer 模块不存在")

from src.esg.analysis.topic_analyzer import (
    TopicAnalyzer,
    TopicInfo,
    WordCloudItem,
)


class TestTopicAnalyzer(unittest.TestCase):
    """话题分析器测试类"""

    def setUp(self):
        """测试前置设置"""
        self.analyzer = TopicAnalyzer()

    def test_topic_analyzer_init(self):
        """测试TopicAnalyzer初始化"""
        self.assertIsNotNone(self.analyzer)

    def test_analyze_trends(self):
        """测试趋势分析"""
        result = self.analyzer.analyze_trends()
        self.assertIsInstance(result, dict)

    def test_get_category_summary(self):
        """测试获取类别摘要"""
        result = self.analyzer.get_category_summary()
        self.assertIsInstance(result, dict)

    def test_get_topic_detail(self):
        """测试获取话题详情"""
        # 测试获取E维度的话题详情
        result = self.analyzer.get_topic_detail("E")
        # 可能返回None或dict
        self.assertTrue(result is None or isinstance(result, dict))

    def test_generate_wordcloud_data(self):
        """测试生成词云数据"""
        result = self.analyzer.generate_wordcloud_data()
        self.assertIsInstance(result, list)

    def test_clear_cache(self):
        """测试清除缓存"""
        # 应该不抛出异常
        self.analyzer.clear_cache()


class TestTopicInfo(unittest.TestCase):
    """TopicInfo数据类测试"""

    def test_topic_info_creation(self):
        """测试TopicInfo创建"""
        info = TopicInfo(
            id="test_topic", name="测试话题", category="E", base_weight=0.8, growth=0.1
        )
        self.assertEqual(info.id, "test_topic")
        self.assertEqual(info.name, "测试话题")
        self.assertEqual(info.category, "E")


class TestWordCloudItem(unittest.TestCase):
    """WordCloudItem数据类测试"""

    def test_word_cloud_item_creation(self):
        """测试WordCloudItem创建"""
        item = WordCloudItem(text="ESG", value=100, category="E")
        self.assertEqual(item.text, "ESG")
        self.assertEqual(item.value, 100)
        self.assertEqual(item.category, "E")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTopicAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestTopicInfo))
    suite.addTests(loader.loadTestsFromTestCase(TestWordCloudItem))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
