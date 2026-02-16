"""日志配置模块单元测试

覆盖 logging_config 模块的各种功能。
"""

import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLoggingConfigConstants(unittest.TestCase):
    """日志配置常量测试类"""

    def test_import_constants(self):
        """测试导入日志配置常量"""
        try:
            from src.esg.config.logging_config import (
                BACKUP_COUNT,
                DATE_FORMAT,
                DEFAULT_LOG_LEVEL,
                LOG_DIR,
                LOG_FORMAT,
                MAX_LOG_SIZE,
            )

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"无法导入日志配置常量: {e}")

    def test_log_dir_is_path(self):
        """测试LOG_DIR是Path对象"""
        from src.esg.config.logging_config import LOG_DIR

        self.assertIsInstance(LOG_DIR, Path)

    def test_default_log_level_default(self):
        """测试默认日志级别为INFO"""
        from src.esg.config.logging_config import DEFAULT_LOG_LEVEL

        self.assertEqual(DEFAULT_LOG_LEVEL, "INFO")

    def test_log_format(self):
        """测试日志格式包含必要元素"""
        from src.esg.config.logging_config import LOG_FORMAT

        self.assertIn("%(asctime)s", LOG_FORMAT)
        self.assertIn("%(levelname)s", LOG_FORMAT)
        self.assertIn("%(message)s", LOG_FORMAT)

    def test_max_log_size(self):
        """测试日志文件大小限制"""
        from src.esg.config.logging_config import MAX_LOG_SIZE

        self.assertEqual(MAX_LOG_SIZE, 10 * 1024 * 1024)

    def test_backup_count(self):
        """测试日志备份数量"""
        from src.esg.config.logging_config import BACKUP_COUNT

        self.assertEqual(BACKUP_COUNT, 5)


class TestSetupLogging(unittest.TestCase):
    """setup_logging函数测试类"""

    def test_setup_logging_returns_logger(self):
        """测试setup_logging返回Logger对象"""
        from src.esg.config.logging_config import setup_logging

        logger = setup_logging(name="test_logger", level="DEBUG", log_to_file=False)
        self.assertIsInstance(logger, logging.Logger)
        # 清理
        logger.handlers = []

    def test_setup_logging_with_custom_level(self):
        """测试使用自定义日志级别"""
        from src.esg.config.logging_config import setup_logging

        logger = setup_logging(name="test_level", level="WARNING", log_to_file=False)
        self.assertEqual(logger.level, logging.WARNING)
        # 清理
        logger.handlers = []

    def test_setup_logging_no_duplicate_handlers(self):
        """测试不会重复添加handler"""
        from src.esg.config.logging_config import setup_logging

        # 第一次调用
        logger1 = setup_logging(name="test_dup", level="INFO", log_to_file=False)
        handler_count = len(logger1.handlers)

        # 第二次调用应该返回同一个logger且不添加新handler
        logger2 = setup_logging(name="test_dup", level="INFO", log_to_file=False)
        self.assertEqual(len(logger2.handlers), handler_count)

        # 清理
        logger1.handlers = []


class TestGetLogger(unittest.TestCase):
    """get_logger函数测试类"""

    def test_get_logger_returns_logger(self):
        """测试get_logger返回Logger对象"""
        from src.esg.config.logging_config import get_logger

        logger = get_logger("test_get_logger")
        self.assertIsInstance(logger, logging.Logger)

    def test_get_logger_with_different_names(self):
        """测试获取不同名称的logger"""
        from src.esg.config.logging_config import get_logger

        logger1 = get_logger("name1")
        logger2 = get_logger("name2")
        self.assertNotEqual(logger1.name, logger2.name)


class TestLogLevelConstants(unittest.TestCase):
    """日志级别常量测试类"""

    def test_log_level_constants(self):
        """测试日志级别常量导出"""
        from src.esg.config.logging_config import (
            CRITICAL,
            DEBUG,
            ERROR,
            INFO,
            WARNING,
        )

        self.assertEqual(CRITICAL, logging.CRITICAL)
        self.assertEqual(ERROR, logging.ERROR)
        self.assertEqual(WARNING, logging.WARNING)
        self.assertEqual(INFO, logging.INFO)
        self.assertEqual(DEBUG, logging.DEBUG)


class TestInitRootLogger(unittest.TestCase):
    """init_root_logger函数测试类"""

    def test_init_root_logger(self):
        """测试初始化根日志记录器"""
        from src.esg.config.logging_config import init_root_logger

        # 应该能够正常调用，不抛出异常
        try:
            init_root_logger()
        except Exception as e:
            self.fail(f"init_root_logger 抛出异常: {e}")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLoggingConfigConstants))
    suite.addTests(loader.loadTestsFromTestCase(TestSetupLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestGetLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestLogLevelConstants))
    suite.addTests(loader.loadTestsFromTestCase(TestInitRootLogger))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
