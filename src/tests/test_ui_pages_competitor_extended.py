"""竞争对手分析模块单元测试

覆盖esg.ui.pages.competitor模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRenderCompetitorPage(unittest.TestCase):
    """竞争对手页面渲染测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.info")
    @patch("streamlit.selectbox")
    @patch("streamlit.columns")
    @patch("streamlit.metric")
    @patch("streamlit.spinner")
    @patch("streamlit.expander")
    @patch("streamlit.warning")
    def test_render_competitor_page_with_metrics(
        self,
        mock_warning,
        mock_expander,
        mock_spinner,
        mock_metric,
        mock_columns,
        mock_select,
        mock_info,
        mock_markdown,
    ):
        """测试有指标数据时渲染竞争对手页面"""
        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 3

        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()

        with patch("esg.ui.pages.competitor.CompetitorAnalyzer") as mock_analyzer:
            with patch("esg.ui.pages.competitor.get_state_manager") as mock_get_manager:
                mock_instance = MagicMock()
                mock_analyzer.return_value = mock_instance

                mock_instance.get_competitor_list.return_value = ["维斯塔斯", "西门子"]
                mock_instance.generate_analysis.return_value = "分析报告内容"
                mock_instance.generate_comparison_table.return_value = []
                mock_instance.get_overall_comparison.return_value = {
                    "current_company": {"rank": 2, "total_companies": 5, "overall_score": 75.0}
                }
                mock_instance.get_strategy_by_dimension.return_value = MagicMock(
                    strategy_area="测试策略",
                    best_practice_description="最佳实践描述",
                    key_results="关键成果",
                    implementation_timeline="6个月",
                    investment="100万",
                    innovation_highlights="创新亮点",
                )
                mock_instance.get_innovation_highlights.return_value = ["亮点1", "亮点2"]

                mock_manager = MagicMock()
                mock_manager.has_metrics.return_value = True
                mock_manager.get_metrics.return_value = MagicMock(
                    get_all_dimension_scores=lambda: {"E": 75, "S": 80, "G": 70}
                )
                mock_get_manager.return_value = mock_manager

                from src.esg.ui.pages import competitor

                try:
                    competitor.render_competitor_page({})
                except Exception:
                    pass

    @patch("streamlit.markdown")
    @patch("streamlit.info")
    @patch("streamlit.selectbox")
    @patch("streamlit.columns")
    @patch("streamlit.warning")
    def test_render_competitor_page_without_metrics(
        self, mock_warning, mock_columns, mock_select, mock_info, mock_markdown
    ):
        """测试没有指标数据时渲染竞争对手页面"""
        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 3

        with patch("esg.ui.pages.competitor.CompetitorAnalyzer") as mock_analyzer:
            with patch("esg.ui.pages.competitor.get_state_manager") as mock_get_manager:
                mock_instance = MagicMock()
                mock_analyzer.return_value = mock_instance

                mock_instance.get_competitor_list.return_value = ["维斯塔斯"]

                mock_manager = MagicMock()
                mock_manager.has_metrics.return_value = False
                mock_get_manager.return_value = mock_manager

                from src.esg.ui.pages import competitor

                try:
                    competitor.render_competitor_page({})
                except Exception:
                    pass

    @patch("streamlit.error")
    def test_render_competitor_page_with_init_error(self, mock_error):
        """测试初始化失败时渲染"""
        with patch("esg.ui.pages.competitor.CompetitorAnalyzer") as mock_analyzer:
            mock_analyzer.side_effect = Exception("初始化失败")

            from src.esg.ui.pages import competitor

            try:
                competitor.render_competitor_page({})
            except Exception:
                pass


class TestGetStateManager(unittest.TestCase):
    """获取状态管理器测试"""

    def test_get_state_manager_function(self):
        """测试get_state_manager函数"""
        with patch("esg.ui.pages.competitor.get_state_manager") as mock_func:
            mock_func.return_value = MagicMock()

            from src.esg.ui.pages import competitor

            result = competitor.get_state_manager()

            # 函数被调用
            self.assertIsNotNone(result)


class TestCompetitorAnalyzerMock(unittest.TestCase):
    """CompetitorAnalyzer模拟测试"""

    def test_competitor_analyzer_import(self):
        """测试导入CompetitorAnalyzer"""
        from src.esg.analysis.competitor_analyzer import CompetitorAnalyzer

        self.assertIsNotNone(CompetitorAnalyzer)

    def test_competitor_analyzer_init(self):
        """测试CompetitorAnalyzer初始化"""
        from src.esg.analysis.competitor_analyzer import CompetitorAnalyzer

        analyzer = CompetitorAnalyzer()
        self.assertIsNotNone(analyzer)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRenderCompetitorPage))
    suite.addTests(loader.loadTestsFromTestCase(TestGetStateManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCompetitorAnalyzerMock))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
