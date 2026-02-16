"""UI状态管理单元测试

覆盖AppState和StateManager的各种使用场景。
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAppState(unittest.TestCase):
    """应用状态测试类"""

    def test_import_app_state(self):
        """测试导入AppState"""
        try:
            from src.esg.ui.state import AppState

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入AppState")

    def test_app_state_creation(self):
        """测试创建AppState"""
        from src.esg.ui.state import AppState

        state = AppState()
        self.assertIsNotNone(state)


class TestStateManager(unittest.TestCase):
    """状态管理器测试类"""

    def test_import_state_manager(self):
        """测试导入StateManager"""
        try:
            from src.esg.ui.state import StateManager

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入StateManager")

    def test_state_manager_creation(self):
        """测试创建StateManager"""
        from src.esg.ui.state import StateManager

        manager = StateManager()
        self.assertIsNotNone(manager)


class TestAnalysisResult(unittest.TestCase):
    """分析结果数据类测试"""

    def test_import_analysis_result(self):
        """测试导入AnalysisResult"""
        try:
            from src.esg.ui.state import AnalysisResult

            self.assertTrue(True)
        except ImportError:
            self.fail("无法导入AnalysisResult")


class TestStateKeys(unittest.TestCase):
    """状态键测试"""

    def test_import_state_keys(self):
        """测试导入STATE_KEYS"""
        try:
            from src.esg.ui.state import STATE_KEYS

            self.assertIsInstance(STATE_KEYS, dict)
        except ImportError:
            self.fail("无法导入STATE_KEYS")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAppState))
    suite.addTests(loader.loadTestsFromTestCase(TestStateManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisResult))
    suite.addTests(loader.loadTestsFromTestCase(TestStateKeys))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
