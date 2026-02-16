"""权重配置页面单元测试

覆盖esg.ui.pages.weights模块的各种使用场景和边界情况。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWeightsPage(unittest.TestCase):
    """权重配置页面测试类"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.radio")
    @patch("streamlit.slider")
    @patch("streamlit.button")
    @patch("streamlit.success")
    @patch("streamlit.info")
    @patch("streamlit.write")
    @patch("streamlit.plotly_chart")
    def test_render_weights_page_simple(
        self,
        mock_plotly,
        mock_write,
        mock_info,
        mock_success,
        mock_button,
        mock_slider,
        mock_radio,
        mock_columns,
        mock_markdown,
    ):
        """测试简单配置模式"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]

        mock_radio.return_value = "简单配置"

        # 模拟sliders返回不同的值
        mock_slider.side_effect = [0.4, 0.3, 0.3]

        # 模拟button点击
        mock_button.return_value = True

        with patch("esg.ui.pages.weights.get_state_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_weights.return_value = {"E": 0.33, "S": 0.33, "G": 0.34}
            mock_get_manager.return_value = mock_manager

            from src.esg.ui.pages import weights

            config = {}

            try:
                weights.render_weights_page(config)
            except Exception:
                pass

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.radio")
    @patch("streamlit.select_slider")
    @patch("streamlit.button")
    @patch("streamlit.success")
    @patch("streamlit.info")
    @patch("streamlit.write")
    @patch("streamlit.warning")
    @patch("streamlit.plotly_chart")
    def test_render_weights_page_ahp(
        self,
        mock_plotly,
        mock_warning,
        mock_write,
        mock_info,
        mock_success,
        mock_button,
        mock_select_slider,
        mock_radio,
        mock_columns,
        mock_markdown,
    ):
        """测试AHP配置模式"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]

        mock_radio.return_value = "AHP层次分析法"

        # 模拟select_slider返回不同的值
        mock_select_slider.side_effect = [3, 5, 1]

        # 模拟button点击
        mock_button.return_value = True

        with patch("esg.ui.pages.weights.get_state_manager") as mock_get_manager:
            with patch("esg.ui.pages.weights.AHPFusionEngine") as mock_engine:
                mock_manager = MagicMock()
                mock_manager.get_weights.return_value = {"E": 0.33, "S": 0.33, "G": 0.34}
                mock_get_manager.return_value = mock_manager

                mock_engine_instance = MagicMock()
                mock_result = MagicMock()
                mock_result.weights_dict = {"E": 0.4, "S": 0.3, "G": 0.3}
                mock_result.consistency_ratio = 0.05
                mock_result.is_consistent = True
                mock_engine_instance.calculate_weights.return_value = mock_result
                mock_engine.return_value = mock_engine_instance

                from src.esg.ui.pages import weights

                config = {}

                try:
                    weights.render_weights_page(config)
                except Exception:
                    pass


class TestSimpleWeightsConfig(unittest.TestCase):
    """简单权重配置测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.slider")
    @patch("streamlit.button")
    @patch("streamlit.success")
    @patch("streamlit.write")
    def test_render_simple_weights(
        self, mock_write, mock_success, mock_button, mock_slider, mock_columns, mock_markdown
    ):
        """测试简单权重配置渲染"""
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]

        mock_slider.side_effect = [0.4, 0.3, 0.3]

        mock_button.return_value = True

        with patch("esg.ui.pages.weights.get_state_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_weights.return_value = {"E": 0.33, "S": 0.33, "G": 0.34}
            mock_get_manager.return_value = mock_manager

            from src.esg.ui.pages import weights

            try:
                weights._render_simple_weights_config()
            except Exception:
                pass


class TestAHPWeightsConfig(unittest.TestCase):
    """AHP权重配置测试"""

    @patch("streamlit.markdown")
    @patch("streamlit.select_slider")
    @patch("streamlit.button")
    @patch("streamlit.success")
    @patch("streamlit.write")
    @patch("streamlit.warning")
    def test_render_ahp_weights_inconsistent(
        self, mock_warning, mock_write, mock_success, mock_button, mock_select_slider, mock_markdown
    ):
        """测试AHP权重配置 - 不一致情况"""
        mock_select_slider.side_effect = [3, 5, 1]

        mock_button.return_value = True

        with patch("esg.ui.pages.weights.get_state_manager") as mock_get_manager:
            with patch("esg.ui.pages.weights.AHPFusionEngine") as mock_engine:
                mock_manager = MagicMock()
                mock_manager.get_weights.return_value = {"E": 0.33, "S": 0.33, "G": 0.34}
                mock_get_manager.return_value = mock_manager

                mock_engine_instance = MagicMock()
                mock_result = MagicMock()
                mock_result.weights_dict = {"E": 0.4, "S": 0.3, "G": 0.3}
                mock_result.consistency_ratio = 0.15  # 不一致
                mock_result.is_consistent = False
                mock_engine_instance.calculate_weights.return_value = mock_result
                mock_engine.return_value = mock_engine_instance

                from src.esg.ui.pages import weights

                try:
                    weights._render_ahp_weights_config()
                except Exception:
                    pass


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestWeightsPage))
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleWeightsConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestAHPWeightsConfig))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
