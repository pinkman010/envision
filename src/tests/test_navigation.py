"""导航模块单元测试

覆盖 navigation 模块的各种功能。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNavigationImports(unittest.TestCase):
    """导入测试类"""

    def test_import_navigation_module(self):
        """测试导入navigation模块"""
        try:
            from src.esg.ui import navigation

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入navigation模块: {e}")

    def test_import_dependencies(self):
        """测试导入依赖模块"""
        try:
            import streamlit as st

            from src.esg.config import ANALYSIS_YEARS, BENCHMARK_COMPANIES

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入依赖: {e}")


class TestRenderSidebar(unittest.TestCase):
    """render_sidebar函数测试类"""

    @patch("src.esg.ui.navigation.st.sidebar")
    @patch("src.esg.ui.navigation.st.markdown")
    @patch("src.esg.ui.navigation.st.button")
    @patch("src.esg.ui.navigation.st.selectbox")
    @patch("src.esg.ui.navigation.get_state_manager")
    def test_render_sidebar_returns_dict(
        self, mock_manager, mock_selectbox, mock_button, mock_markdown, mock_sidebar
    ):
        """测试render_sidebar返回字典"""
        from src.esg.ui import navigation

        # Mock返回值
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_current_page.return_value = "home"
        mock_manager.return_value = mock_manager_instance

        mock_selectbox.return_value = "新能源"
        mock_button.return_value = False

        # 调用render_sidebar
        result = navigation.render_sidebar()

        # 验证返回的是字典
        self.assertIsInstance(result, dict)
        self.assertIn("industry", result)
        self.assertIn("year", result)
        self.assertIn("benchmark", result)

    @patch("src.esg.ui.navigation.st.sidebar")
    @patch("src.esg.ui.navigation.st.markdown")
    @patch("src.esg.ui.navigation.st.button")
    @patch("src.esg.ui.navigation.st.selectbox")
    @patch("src.esg.ui.navigation.get_state_manager")
    def test_render_sidebar_returns_industry(
        self, mock_manager, mock_selectbox, mock_button, mock_markdown, mock_sidebar
    ):
        """测试render_sidebar返回行业"""
        from src.esg.ui import navigation

        # Mock返回值
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_current_page.return_value = "home"
        mock_manager.return_value = mock_manager_instance

        mock_selectbox.return_value = "制造业"
        mock_button.return_value = False

        # 调用render_sidebar
        result = navigation.render_sidebar()

        # 验证返回的行业
        self.assertEqual(result["industry"], "制造业")

    @patch("src.esg.ui.navigation.st.sidebar")
    @patch("src.esg.ui.navigation.st.markdown")
    @patch("src.esg.ui.navigation.st.button")
    @patch("src.esg.ui.navigation.st.selectbox")
    @patch("src.esg.ui.navigation.get_state_manager")
    def test_render_sidebar_returns_year(
        self, mock_manager, mock_selectbox, mock_button, mock_markdown, mock_sidebar
    ):
        """测试render_sidebar返回年份"""
        from src.esg.ui import navigation

        # Mock返回值
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_current_page.return_value = "home"
        mock_manager.return_value = mock_manager_instance

        mock_selectbox.return_value = "2024"
        mock_button.return_value = False

        # 调用render_sidebar
        result = navigation.render_sidebar()

        # 验证返回的年份
        self.assertEqual(result["year"], "2024")

    @patch("src.esg.ui.navigation.st.sidebar")
    @patch("src.esg.ui.navigation.st.markdown")
    @patch("src.esg.ui.navigation.st.button")
    @patch("src.esg.ui.navigation.st.selectbox")
    @patch("src.esg.ui.navigation.get_state_manager")
    def test_render_sidebar_returns_benchmark(
        self, mock_manager, mock_selectbox, mock_button, mock_markdown, mock_sidebar
    ):
        """测试render_sidebar返回对标企业"""
        from src.esg.ui import navigation

        # Mock返回值
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_current_page.return_value = "home"
        mock_manager.return_value = mock_manager_instance

        mock_selectbox.return_value = "Company A"
        mock_button.return_value = False

        # 调用render_sidebar
        result = navigation.render_sidebar()

        # 验证返回的对标企业
        self.assertEqual(result["benchmark"], "Company A")


class TestNavigationConfig(unittest.TestCase):
    """导航配置测试类"""

    def test_analysis_years(self):
        """测试ANALYSIS_YEARS配置"""
        from src.esg.config import ANALYSIS_YEARS

        self.assertIsInstance(ANALYSIS_YEARS, (list, tuple))
        self.assertGreater(len(ANALYSIS_YEARS), 0)

    def test_benchmark_companies(self):
        """测试BENCHMARK_COMPANIES配置"""
        from src.esg.config import BENCHMARK_COMPANIES

        self.assertIsInstance(BENCHMARK_COMPANIES, (list, tuple))
        self.assertGreater(len(BENCHMARK_COMPANIES), 0)


class TestDocstring(unittest.TestCase):
    """文档字符串测试类"""

    def test_navigation_module_docstring(self):
        """测试navigation模块有文档字符串"""
        from src.esg.ui import navigation

        self.assertIsNotNone(navigation.__doc__)

    def test_render_sidebar_docstring(self):
        """测试render_sidebar函数有文档字符串"""
        from src.esg.ui.navigation import render_sidebar

        self.assertIsNotNone(render_sidebar.__doc__)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestNavigationImports))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderSidebar))
    suite.addTests(loader.loadTestsFromTestCase(TestNavigationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDocstring))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
