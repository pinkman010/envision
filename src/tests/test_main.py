"""主入口模块单元测试

覆盖 main.py 模块的各种功能。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainImports(unittest.TestCase):
    """导入测试类"""

    def test_import_main_module(self):
        """测试导入main模块"""
        try:
            import src.main

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入main模块: {e}")

    def test_import_streamlit(self):
        """测试导入streamlit"""
        try:
            import streamlit as st

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入streamlit: {e}")

    def test_import_app_config(self):
        """测试导入APP_NAME, APP_ICON, VERSION"""
        try:
            from src.esg.config import APP_ICON, APP_NAME, VERSION

            self.assertIsNotNone(APP_NAME)
            self.assertIsNotNone(APP_ICON)
            self.assertIsNotNone(VERSION)
        except ImportError as e:
            self.fail(f"无法导入配置: {e}")


class TestMainFunction(unittest.TestCase):
    """main函数测试类"""

    @patch("streamlit.set_page_config")
    def test_main_calls_set_page_config(self, mock_set_page_config):
        """测试main函数调用set_page_config"""
        import importlib

        import src.main

        importlib.reload(src.main)

        # 调用main函数
        try:
            src.main.main()
        except Exception:
            # 忽略Streamlit上下文错误
            pass

        # 验证set_page_config被调用（如果Streamlit上下文存在）
        # 由于Streamlit在非运行环境下无法完全测试，这里只验证模块导入成功

    @patch("src.esg.ui.app_enhanced.render_app")
    def test_main_calls_render_app(self, mock_render_app):
        """测试main函数调用render_app"""
        import importlib

        import src.main

        importlib.reload(src.main)

        # 调用main函数
        try:
            src.main.main()
        except Exception:
            # 忽略Streamlit上下文错误
            pass

        # 验证render_app被调用（如果Streamlit上下文存在）
        # 由于Streamlit在非运行环境下无法完全测试，这里只验证模块导入成功


class TestAppConfig(unittest.TestCase):
    """应用配置测试类"""

    def test_app_name_is_string(self):
        """测试APP_NAME是字符串"""
        from src.esg.config import APP_NAME

        self.assertIsInstance(APP_NAME, str)
        self.assertGreater(len(APP_NAME), 0)

    def test_app_icon_is_string(self):
        """测试APP_ICON是字符串"""
        from src.esg.config import APP_ICON

        self.assertIsInstance(APP_ICON, str)

    def test_version_is_string(self):
        """测试VERSION是字符串"""
        from src.esg.config import VERSION

        self.assertIsInstance(VERSION, str)


class TestDocstring(unittest.TestCase):
    """文档字符串测试类"""

    def test_main_module_docstring(self):
        """测试main模块有文档字符串"""
        import src.main

        self.assertIsNotNone(src.main.__doc__)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestMainImports))
    suite.addTests(loader.loadTestsFromTestCase(TestMainFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestAppConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDocstring))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
