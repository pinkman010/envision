"""Windows启动脚本单元测试

覆盖 start_windows 模块的各种功能。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSetupEnvironment(unittest.TestCase):
    """setup_environment函数测试类"""

    @patch("src.start_windows.Path")
    @patch("src.start_windows.sys.path", [])
    def test_setup_environment_adds_paths(self, mock_path):
        """测试setup_environment添加项目路径"""
        import importlib

        # 重新加载模块以获取最新状态
        import src.start_windows as sw

        importlib.reload(sw)

        # 记录原始sys.path长度
        original_path_len = len(sys.path)

        # 调用setup_environment
        sw.setup_environment()

        # 验证路径已添加
        self.assertGreater(len(sys.path), original_path_len)

    def test_setup_environment_sets_pythonpath(self):
        """测试setup_environment设置PYTHONPATH环境变量"""
        import importlib

        import src.start_windows as sw

        importlib.reload(sw)

        # 保存原始值
        original_pythonpath = os.environ.get("PYTHONPATH")

        try:
            sw.setup_environment()
            # 验证PYTHONPATH已设置
            self.assertIn("PYTHONPATH", os.environ)
        finally:
            # 恢复原始值
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)


class TestRunStreamlit(unittest.TestCase):
    """run_streamlit函数测试类"""

    def test_run_streamlit_is_callable(self):
        """测试run_streamlit可调用"""
        import src.start_windows as sw

        self.assertTrue(callable(sw.run_streamlit))

    def test_run_streamlit_accepts_mode_parameter(self):
        """测试run_streamlit接受mode参数"""
        import inspect

        import src.start_windows as sw

        sig = inspect.signature(sw.run_streamlit)
        self.assertIn("mode", sig.parameters)


class TestImports(unittest.TestCase):
    """导入测试类"""

    def test_import_start_windows(self):
        """测试导入start_windows模块"""
        try:
            import src.start_windows

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入start_windows模块: {e}")

    def test_import_dependencies(self):
        """测试导入依赖模块"""
        try:
            import logging
            import os
            import sys
            from pathlib import Path

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入依赖模块: {e}")


class TestModuleFunctions(unittest.TestCase):
    """模块函数测试类"""

    def test_setup_environment_is_callable(self):
        """测试setup_environment是可调用函数"""
        import src.start_windows

        self.assertTrue(callable(src.start_windows.setup_environment))

    def test_run_streamlit_is_callable(self):
        """测试run_streamlit是可调用函数"""
        import src.start_windows

        self.assertTrue(callable(src.start_windows.run_streamlit))


import os


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSetupEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestRunStreamlit))
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleFunctions))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
