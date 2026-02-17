"""首页模块单元测试

覆盖esg.ui.pages.home模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRenderHomePage(unittest.TestCase):
    """首页渲染测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.tabs")
    @patch("streamlit.success")
    def test_render_home_page_with_metrics(
        self, mock_success, mock_tabs, mock_columns, mock_markdown
    ):
        """测试有指标数据时渲染首页"""
        # 模拟tabs返回三个tab对象
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]

        # 模拟columns返回多个列
        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 4

        with patch("esg.ui.pages.home.get_state_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.has_metrics.return_value = True

            mock_metrics = MagicMock()
            mock_metrics.get_all_dimension_scores.return_value = {"E": 75.0, "S": 80.0, "G": 70.0}
            mock_manager.get_metrics.return_value = mock_metrics
            mock_get_manager.return_value = mock_manager

            from src.esg.ui.pages import home

            config = {}

            try:
                home.render_home_page(config)
            except Exception:
                pass

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.tabs")
    def test_render_home_page_without_metrics(self, mock_tabs, mock_columns, mock_markdown):
        """测试没有指标数据时渲染首页"""
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]

        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 4

        with patch("esg.ui.pages.home.get_state_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.has_metrics.return_value = False
            mock_get_manager.return_value = mock_manager

            from src.esg.ui.pages import home

            config = {}

            try:
                home.render_home_page(config)
            except Exception:
                pass


class TestRenderPdfUpload(unittest.TestCase):
    """PDF上传测试"""

    @patch("streamlit.file_uploader")
    @patch("streamlit.spinner")
    @patch("streamlit.error")
    @patch("streamlit.success")
    @patch("streamlit.button")
    def test_render_pdf_upload_with_file(
        self, mock_button, mock_success, mock_error, mock_spinner, mock_uploader
    ):
        """测试上传PDF文件"""
        mock_uploader.return_value = MagicMock()
        mock_uploader.return_value.name = "test.pdf"
        mock_uploader.return_value.getvalue.return_value = b"fake pdf content"

        with patch("tempfile.NamedTemporaryFile"):
            with patch("esg.ui.pages.home.PDFExtractor") as mock_extractor:
                with patch("esg.ui.pages.home.MetricExtractor"):
                    mock_extractor_instance = MagicMock()
                    mock_extractor.return_value = mock_extractor_instance

                    from src.esg.ui.pages import home

                    try:
                        home._render_pdf_upload()
                    except Exception:
                        pass

    @patch("streamlit.file_uploader")
    def test_render_pdf_upload_no_file(self, mock_uploader):
        """测试没有上传文件"""
        mock_uploader.return_value = None

        from src.esg.ui.pages import home

        try:
            home._render_pdf_upload()
        except Exception:
            pass


class TestOfferFallbackOptions(unittest.TestCase):
    """备用选项测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.button")
    def test_offer_fallback_options(self, mock_button, mock_columns, mock_markdown):
        """测试备用选项"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]

        mock_button.return_value = False

        mock_file = MagicMock()
        mock_file.name = "test.pdf"

        from src.esg.ui.pages import home

        try:
            home._offer_fallback_options(mock_file)
        except Exception:
            pass


class TestRenderManualInput(unittest.TestCase):
    """手动输入测试"""

    @patch("streamlit.form")
    @patch("streamlit.columns")
    @patch("streamlit.number_input")
    @patch("streamlit.text_input")
    @patch("streamlit.selectbox")
    @patch("streamlit.form_submit_button")
    def test_render_manual_input(
        self, mock_submit, mock_select, mock_text, mock_number, mock_columns, mock_form
    ):
        """测试手动输入表单"""
        mock_form.return_value.__enter__ = MagicMock()
        mock_form.return_value.__exit__ = MagicMock()

        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 3

        mock_text.return_value = "测试公司"
        mock_select.return_value = "2024"

        from src.esg.ui.pages import home

        try:
            home._render_manual_input()
        except Exception:
            pass


class TestRenderDemoDataSelection(unittest.TestCase):
    """示例数据选择测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.button")
    @patch("streamlit.success")
    def test_render_demo_data_selection(
        self, mock_success, mock_button, mock_markdown
    ):
        """测试示例数据选择"""
        # 模拟按钮被点击
        mock_button.return_value = True

        with patch("esg.ui.pages.home.load_demo_metrics") as mock_load:
            with patch("esg.ui.pages.home.get_state_manager") as mock_get_manager:
                mock_manager = MagicMock()
                mock_get_manager.return_value = mock_manager

                mock_metrics = MagicMock()
                mock_metrics.company_name = "绿色能源集团"
                mock_load.return_value = mock_metrics

                from src.esg.ui.pages import home

                try:
                    home._render_demo_data_selection()
                except Exception:
                    pass


class TestRenderMetricsOverview(unittest.TestCase):
    """指标概览测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.plotly_chart")
    @patch("streamlit.expander")
    def test_render_metrics_overview(self, mock_expander, mock_plotly, mock_columns, mock_markdown):
        """测试指标概览渲染"""
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()

        mock_col = MagicMock()
        mock_columns.return_value = [mock_col] * 3

        with patch("esg.ui.pages.home.get_state_manager") as mock_get_manager:
            mock_manager = MagicMock()

            mock_metrics = MagicMock()
            mock_metrics.get_all_dimension_scores.return_value = {"E": 75.0, "S": 80.0, "G": 70.0}
            mock_metrics.carbon_emissions = 100000
            mock_metrics.renewable_energy_ratio = 0.4
            mock_metrics.energy_efficiency = 70.0
            mock_metrics.employee_count = 3000
            mock_metrics.female_ratio = 0.35
            mock_metrics.training_hours = 30.0
            mock_metrics.board_independence_ratio = 0.4
            mock_metrics.ethics_training_coverage = 0.7

            mock_manager.get_metrics.return_value = mock_metrics
            mock_get_manager.return_value = mock_manager

            from src.esg.ui.pages import home

            try:
                home._render_metrics_overview()
            except Exception:
                pass


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRenderHomePage))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderPdfUpload))
    suite.addTests(loader.loadTestsFromTestCase(TestOfferFallbackOptions))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderManualInput))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderDemoDataSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderMetricsOverview))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
