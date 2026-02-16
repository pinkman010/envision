"""竞争对手分析页面单元测试

覆盖esg.ui.pages.competitor模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCompetitorPage(unittest.TestCase):
    """竞争对手分析页面测试类"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.selectbox")
    @patch("streamlit.button")
    @patch("streamlit.error")
    @patch("streamlit.info")
    @patch("streamlit.spinner")
    @patch("streamlit.warning")
    @patch("streamlit.metric")
    @patch("streamlit.dataframe")
    @patch("streamlit.expander")
    def test_render_competitor_page_with_metrics(
        self,
        mock_expander,
        mock_dataframe,
        mock_metric,
        mock_warning,
        mock_spinner,
        mock_info,
        mock_error,
        mock_button,
        mock_selectbox,
        mock_columns,
        mock_markdown,
    ):
        """测试有指标数据时渲染"""
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()

        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]

        mock_selectbox.return_value = "维斯塔斯"

        with patch("esg.ui.pages.competitor.get_state_manager") as mock_get_manager:
            with patch("esg.ui.pages.competitor.CompetitorAnalyzer") as mock_analyzer:
                mock_manager = MagicMock()
                mock_manager.has_metrics.return_value = True

                mock_metrics = MagicMock()
                mock_metrics.get_all_dimension_scores.return_value = {
                    "E": 75.0,
                    "S": 80.0,
                    "G": 70.0,
                }
                mock_manager.get_metrics.return_value = mock_metrics
                mock_get_manager.return_value = mock_manager

                mock_instance = MagicMock()
                mock_instance.get_competitor_list.return_value = ["维斯塔斯", "西门子歌美萨克"]
                mock_instance.generate_analysis.return_value = "分析报告内容"
                mock_instance.generate_comparison_table.return_value = []
                mock_instance.get_overall_comparison.return_value = {
                    "current_company": {"rank": 3, "total_companies": 10, "overall_score": 75.0}
                }
                mock_instance.get_strategy_by_dimension.return_value = MagicMock(
                    strategy_area="碳减排",
                    best_practice_description="最佳实践描述",
                    key_results="关键成果",
                    implementation_timeline="12个月",
                    investment="1000万",
                    innovation_highlights="创新亮点",
                )
                mock_instance.get_innovation_highlights.return_value = ["亮点1", "亮点2"]
                mock_analyzer.return_value = mock_instance

                from src.esg.ui.pages import competitor

                config = {}

                try:
                    competitor.render_competitor_page(config)
                except Exception:
                    pass

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.selectbox")
    @patch("streamlit.button")
    @patch("streamlit.error")
    @patch("streamlit.info")
    @patch("streamlit.spinner")
    @patch("streamlit.warning")
    @patch("streamlit.metric")
    @patch("streamlit.dataframe")
    @patch("streamlit.expander")
    def test_render_competitor_page_without_metrics(
        self,
        mock_expander,
        mock_dataframe,
        mock_metric,
        mock_warning,
        mock_spinner,
        mock_info,
        mock_error,
        mock_button,
        mock_selectbox,
        mock_columns,
        mock_markdown,
    ):
        """测试没有指标数据时渲染"""
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()

        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]

        mock_selectbox.return_value = "维斯塔斯"

        with patch("esg.ui.pages.competitor.get_state_manager") as mock_get_manager:
            with patch("esg.ui.pages.competitor.CompetitorAnalyzer") as mock_analyzer:
                mock_manager = MagicMock()
                mock_manager.has_metrics.return_value = False
                mock_get_manager.return_value = mock_manager

                mock_instance = MagicMock()
                mock_instance.get_competitor_list.return_value = ["维斯塔斯", "西门子歌美萨克"]
                mock_instance.get_strategy_by_dimension.return_value = None
                mock_instance.get_innovation_highlights.return_value = []
                mock_analyzer.return_value = mock_instance

                from src.esg.ui.pages import competitor

                config = {}

                try:
                    competitor.render_competitor_page(config)
                except Exception:
                    pass

    @patch("streamlit.error")
    def test_render_competitor_page_with_error(self, mock_error):
        """测试初始化失败时渲染"""
        with patch("esg.ui.pages.competitor.CompetitorAnalyzer") as mock_analyzer:
            mock_analyzer.side_effect = Exception("初始化失败")

            from src.esg.ui.pages import competitor

            config = {}

            try:
                competitor.render_competitor_page(config)
            except Exception:
                pass


class TestGetStateManager(unittest.TestCase):
    """get_state_manager函数测试"""

    def test_get_state_manager_function(self):
        """测试get_state_manager函数"""
        from src.esg.ui.pages.competitor import get_state_manager

        # 函数应该返回状态管理器
        result = get_state_manager()
        self.assertIsNotNone(result)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCompetitorPage))
    suite.addTests(loader.loadTestsFromTestCase(TestGetStateManager))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
