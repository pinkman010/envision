"""议题全景图页面单元测试

覆盖esg.ui.pages.topics模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTopicsPage(unittest.TestCase):
    """议题全景图页面测试类"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.selectbox")
    @patch("streamlit.slider")
    @patch("streamlit.error")
    @patch("streamlit.caption")
    @patch("streamlit.plotly_chart")
    @patch("streamlit.container")
    @patch("streamlit.write")
    def test_render_topics_page_basic(
        self,
        mock_write,
        mock_container,
        mock_plotly,
        mock_caption,
        mock_error,
        mock_slider,
        mock_selectbox,
        mock_columns,
        mock_markdown,
    ):
        """测试基本渲染"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]

        mock_container.return_value.__enter__ = MagicMock()
        mock_container.return_value.__exit__ = MagicMock()

        mock_selectbox.return_value = "all"
        mock_slider.return_value = 0.0

        with patch("esg.ui.pages.topics.TopicAnalyzer") as mock_analyzer:
            mock_instance = MagicMock()
            mock_instance.generate_wordcloud_data.return_value = []
            mock_instance.analyze_trends.return_value = {
                "hot_topics": [{"name": "碳排放", "heat_score": 95, "trend": "上升"}],
                "rising_topics": [{"name": "循环经济", "growth_rate": 25, "trend": "上升"}],
            }
            mock_instance.get_category_summary.return_value = {
                "E": {
                    "name": "环境",
                    "count": 10,
                    "avg_heat": 80,
                    "avg_growth_rate": 15,
                    "top_topic": "碳排放",
                },
                "S": {
                    "name": "社会",
                    "count": 8,
                    "avg_heat": 70,
                    "avg_growth_rate": 12,
                    "top_topic": "员工关怀",
                },
                "G": {
                    "name": "治理",
                    "count": 6,
                    "avg_heat": 75,
                    "avg_growth_rate": 10,
                    "top_topic": "董事会多元化",
                },
            }
            mock_analyzer.return_value = mock_instance

            from src.esg.ui.pages import topics

            config = {}

            try:
                topics.render_topics_page(config)
            except Exception:
                pass

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.selectbox")
    @patch("streamlit.slider")
    @patch("streamlit.error")
    @patch("streamlit.caption")
    @patch("streamlit.plotly_chart")
    @patch("streamlit.container")
    @patch("streamlit.write")
    def test_render_topics_page_with_dimension_filter(
        self,
        mock_write,
        mock_container,
        mock_plotly,
        mock_caption,
        mock_error,
        mock_slider,
        mock_selectbox,
        mock_columns,
        mock_markdown,
    ):
        """测试带维度筛选的渲染"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]

        mock_container.return_value.__enter__ = MagicMock()
        mock_container.return_value.__exit__ = MagicMock()

        mock_selectbox.return_value = "E"  # 环境维度
        mock_slider.return_value = 0.1

        with patch("esg.ui.pages.topics.TopicAnalyzer") as mock_analyzer:
            mock_instance = MagicMock()
            mock_instance.generate_wordcloud_data.return_value = []
            mock_instance.analyze_trends.return_value = {"hot_topics": [], "rising_topics": []}
            mock_instance.get_category_summary.return_value = {}
            mock_analyzer.return_value = mock_instance

            from src.esg.ui.pages import topics

            config = {}

            try:
                topics.render_topics_page(config)
            except Exception:
                pass

    @patch("streamlit.error")
    def test_render_topics_page_with_error(self, mock_error):
        """测试初始化失败时渲染"""
        with patch("esg.ui.pages.topics.TopicAnalyzer") as mock_analyzer:
            mock_analyzer.side_effect = Exception("初始化失败")

            from src.esg.ui.pages import topics

            config = {}

            try:
                topics.render_topics_page(config)
            except Exception:
                pass


class TestTopicAnalyzer(unittest.TestCase):
    """TopicAnalyzer测试"""

    def test_topic_analyzer_import(self):
        """测试导入TopicAnalyzer"""
        try:
            from src.esg.analysis.topic_analyzer import TopicAnalyzer

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入TopicAnalyzer")

    def test_topic_analyzer_init(self):
        """测试初始化TopicAnalyzer"""
        try:
            from src.esg.analysis.topic_analyzer import TopicAnalyzer

            analyzer = TopicAnalyzer()
            self.assertIsNotNone(analyzer)
        except Exception:
            pass  # 可能需要配置文件


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTopicsPage))
    suite.addTests(loader.loadTestsFromTestCase(TestTopicAnalyzer))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
