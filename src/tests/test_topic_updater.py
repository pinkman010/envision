"""议题更新器单元测试

覆盖TopicUpdater的各种使用场景、异常处理和边界条件。
"""

import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.analysis.topic_updater import (
    TopicChangeLog,
    TopicUpdater,
    UpdateRecord,
)


class TestTopicChangeLog(unittest.TestCase):
    """议题变更日志测试"""

    def test_create_changelog(self):
        """测试创建变更日志"""
        log = TopicChangeLog(
            topic_id="carbon_emission",
            topic_name="碳排放",
            old_value=50.0,
            new_value=55.0,
            change=5.0,
            change_percent=10.0,
            is_hot_rising=True,
        )

        self.assertEqual(log.topic_id, "carbon_emission")
        self.assertEqual(log.topic_name, "碳排放")
        self.assertEqual(log.change, 5.0)
        self.assertTrue(log.is_hot_rising)

    def test_to_dict(self):
        """测试转换为字典"""
        log = TopicChangeLog(
            topic_id="carbon_emission",
            topic_name="碳排放",
            old_value=50.0,
            new_value=55.5,
            change=5.5,
            change_percent=11.0,
            is_hot_rising=False,
        )

        result = log.to_dict()

        self.assertEqual(result["topic"], "碳排放")
        self.assertEqual(result["old"], 50.0)
        self.assertEqual(result["new"], 55.5)
        self.assertEqual(result["change"], "+5.5")
        self.assertEqual(result["change_percent"], "+11.0%")
        self.assertEqual(result["is_hot"], "")


class TestUpdateRecord(unittest.TestCase):
    """更新记录测试"""

    def test_create_record(self):
        """测试创建更新记录"""
        record = UpdateRecord(
            timestamp="2024-01-15T10:00:00",
            source="测试数据源",
            version="v240115_1000",
            changed_topics=5,
            summary="5个议题发生变化",
        )

        self.assertEqual(record.timestamp, "2024-01-15T10:00:00")
        self.assertEqual(record.changed_topics, 5)
        self.assertEqual(record.change_logs, [])

    def test_post_init_with_logs(self):
        """测试__post_init__带日志"""
        logs = [{"topic": "碳排放", "change": "+5.0"}]
        record = UpdateRecord(
            timestamp="2024-01-15T10:00:00",
            source="测试",
            version="v1",
            changed_topics=1,
            summary="测试摘要",
            change_logs=logs,
        )

        self.assertEqual(record.change_logs, logs)


class TestTopicUpdaterInit(unittest.TestCase):
    """议题更新器初始化测试"""

    def setUp(self):
        """测试前置"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = Path(self.temp_dir) / "mock_topic_updates.json"

    def tearDown(self):
        """测试后置"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_existing_file(self):
        """测试存在数据文件时初始化"""
        # 创建测试数据文件
        test_data = {"version_1": {"topics": {"carbon_emission": {"name": "碳排放", "heat": 80}}}}
        self.data_file.write_text(json.dumps(test_data), encoding="utf-8")

        # 创建实例并手动设置数据文件路径
        updater = TopicUpdater()
        updater.data_file = self.data_file
        updater._load_data()

        current_data = updater.get_current_data()
        self.assertIn("carbon_emission", current_data)

    @patch.object(TopicUpdater, "DATA_FILE", property(lambda self: Path("/nonexistent/path.json")))
    def test_init_with_missing_file(self):
        """测试数据文件不存在时初始化"""
        updater = TopicUpdater()
        updater._data_file = Path("/nonexistent/path.json")
        updater._load_data()

        # 应该创建默认数据结构
        self.assertIn("version_1", updater._data)

    @patch.object(TopicUpdater, "DATA_FILE", property(lambda self: Path("/nonexistent/path.json")))
    def test_init_with_invalid_json(self):
        """测试无效JSON文件"""
        # 创建一个临时文件包含无效JSON
        invalid_file = Path(self.temp_dir) / "invalid.json"
        invalid_file.write_text("not valid json", encoding="utf-8")

        updater = TopicUpdater()
        updater._data_file = invalid_file
        updater._load_data()

        # 应该创建默认数据结构
        self.assertIn("version_1", updater._data)


class TestTopicUpdaterSimulateUpdate(unittest.TestCase):
    """议题更新模拟测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()
            self.updater._data = {
                "version_1": {
                    "topics": {
                        "carbon_emission": {"name": "碳排放", "heat": 50.0, "trend": "stable"},
                        "renewable_energy": {"name": "可再生能源", "heat": 60.0, "trend": "stable"},
                    }
                }
            }

    def test_simulate_update_changes_values(self):
        """测试模拟更新改变数值"""
        current_data = self.updater.get_current_data()
        updated_data, change_logs = self.updater.simulate_update(current_data)

        # 数值应该发生变化
        self.assertNotEqual(
            updated_data["carbon_emission"]["heat"], current_data["carbon_emission"]["heat"]
        )

    def test_simulate_update_generates_change_logs(self):
        """测试模拟更新生成变更日志"""
        current_data = self.updater.get_current_data()
        updated_data, change_logs = self.updater.simulate_update(current_data)

        # 应该有变更日志
        self.assertIsInstance(change_logs, list)
        # 由于随机波动，可能会有变更日志

    def test_simulate_update_limits_range(self):
        """测试模拟更新限制范围"""
        # 设置极端值
        extreme_data = {
            "topic1": {"name": "测试", "heat": 5.0},
            "topic2": {"name": "测试", "heat": 95.0},
        }

        updated_data, _ = self.updater.simulate_update(extreme_data)

        # 数值应该在10-100范围内
        for topic_data in updated_data.values():
            self.assertGreaterEqual(topic_data["heat"], 10)
            self.assertLessEqual(topic_data["heat"], 100)

    def test_simulate_update_updates_trend(self):
        """测试模拟更新更新趋势"""
        # 设置固定值确保变化
        fixed_data = {"topic1": {"name": "测试", "heat": 50.0, "trend": "stable"}}

        # 多次运行以获取变化
        for _ in range(10):
            updated_data, _ = self.updater.simulate_update(fixed_data)
            if updated_data["topic1"]["heat"] > 52:
                self.assertEqual(updated_data["topic1"]["trend"], "up")
                break
            elif updated_data["topic1"]["heat"] < 48:
                self.assertEqual(updated_data["topic1"]["trend"], "down")
                break


class TestTopicUpdaterCreateUpdateRecord(unittest.TestCase):
    """创建更新记录测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()

    def test_create_record_with_changes(self):
        """测试有变更时创建记录"""
        change_logs = [
            TopicChangeLog("t1", "议题1", 50, 55, 5, 10.0),
            TopicChangeLog("t2", "议题2", 60, 65, 5, 8.3),
        ]

        record = self.updater.create_update_record(change_logs)

        self.assertEqual(record.changed_topics, 2)
        self.assertIn("2个议题", record.summary)

    def test_create_record_with_hot_rising(self):
        """测试有新晋热点时创建记录"""
        change_logs = [
            TopicChangeLog("t1", "议题1", 50, 60, 10, 20.0, is_hot_rising=True),
        ]

        record = self.updater.create_update_record(change_logs)

        self.assertIn("1个新晋热点", record.summary)

    def test_create_record_empty_changes(self):
        """测试无变更时创建记录"""
        record = self.updater.create_update_record([])

        self.assertEqual(record.changed_topics, 0)
        self.assertEqual(record.summary, "无显著变化")


class TestTopicUpdaterGenerateSummary(unittest.TestCase):
    """生成摘要测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()

    def test_generate_summary_rising(self):
        """测试上升趋势摘要"""
        logs = [
            TopicChangeLog("t1", "议题1", 50, 55, 5, 10.0),
            TopicChangeLog("t2", "议题2", 60, 65, 5, 8.3),
        ]

        summary = self.updater._generate_summary(logs)

        self.assertIn("2个议题热度上升", summary)

    def test_generate_summary_falling(self):
        """测试下降趋势摘要"""
        logs = [
            TopicChangeLog("t1", "议题1", 55, 50, -5, -9.1),
            TopicChangeLog("t2", "议题2", 65, 60, -5, -7.7),
        ]

        summary = self.updater._generate_summary(logs)

        self.assertIn("2个议题热度下降", summary)

    def test_generate_summary_mixed(self):
        """测试混合趋势摘要"""
        logs = [
            TopicChangeLog("t1", "议题1", 50, 55, 5, 10.0),
            TopicChangeLog("t2", "议题2", 65, 60, -5, -7.7),
            TopicChangeLog("t3", "议题3", 70, 85, 15, 21.4, is_hot_rising=True),
        ]

        summary = self.updater._generate_summary(logs)

        self.assertIn("上升", summary)
        self.assertIn("下降", summary)
        self.assertIn("新晋热点", summary)


class TestTopicUpdaterGetUpdateHistory(unittest.TestCase):
    """获取更新历史测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()

    def test_get_empty_history(self):
        """测试获取空历史"""
        history = self.updater.get_update_history()

        self.assertIsInstance(history, list)

    def test_get_history_with_limit(self):
        """测试带限制获取历史"""
        # 添加一些历史记录
        for i in range(5):
            record = UpdateRecord(
                timestamp=f"2024-01-{i+1}T10:00:00",
                source="测试",
                version=f"v{i}",
                changed_topics=i,
                summary=f"摘要{i}",
            )
            self.updater._update_history.append(record)

        history = self.updater.get_update_history(limit=3)

        self.assertEqual(len(history), 3)


class TestTopicUpdaterGetHotRisingTopics(unittest.TestCase):
    """获取新晋热点测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()
            self.updater._data = {
                "version_1": {
                    "topics": {
                        "t1": {"name": "议题1", "heat": 80, "change": "+15.0"},
                        "t2": {"name": "议题2", "heat": 70, "change": "+5.0"},
                        "t3": {"name": "议题3", "heat": 60, "change": "-3.0"},
                    }
                }
            }

    def test_get_hot_rising_topics(self):
        """测试获取新晋热点"""
        hot_topics = self.updater.get_hot_rising_topics(min_change_percent=10.0)

        self.assertEqual(len(hot_topics), 1)
        self.assertEqual(hot_topics[0]["name"], "议题1")

    def test_get_hot_rising_empty(self):
        """测试无新晋热点"""
        hot_topics = self.updater.get_hot_rising_topics(min_change_percent=20.0)

        self.assertEqual(len(hot_topics), 0)

    def test_get_hot_rising_invalid_change(self):
        """测试无效变化值"""
        self.updater._data["version_1"]["topics"]["t1"]["change"] = "invalid"

        hot_topics = self.updater.get_hot_rising_topics()

        # 应该跳过无效值
        self.assertEqual(len(hot_topics), 0)


class TestTopicUpdaterGetTopicRankChange(unittest.TestCase):
    """获取议题排名变化测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()
            self.updater._data = {
                "version_1": {
                    "topics": {
                        "t1": {"name": "议题1", "heat": 90},
                        "t2": {"name": "议题2", "heat": 80},
                        "t3": {"name": "议题3", "heat": 70},
                    }
                }
            }

    def test_get_rank_change(self):
        """测试获取排名变化"""
        result = self.updater.get_topic_rank_change("t1")

        self.assertEqual(result["name"], "议题1")
        self.assertEqual(result["current_rank"], 1)
        self.assertIn("rank_change", result)

    def test_get_rank_change_new_hot(self):
        """测试新晋热点判断"""
        result = self.updater.get_topic_rank_change("t3")

        # t3排名为3，如果之前排名较低可能会被视为新晋热点
        self.assertIn("is_new_hot", result)


class TestTopicUpdaterFormatTimestamp(unittest.TestCase):
    """格式化时间戳测试"""

    def setUp(self):
        """测试前置"""
        with patch.object(TopicUpdater, "_load_data"):
            self.updater = TopicUpdater()

    def test_format_valid_timestamp(self):
        """测试格式化有效时间戳"""
        timestamp = "2024-01-15T10:30:00"
        result = self.updater.format_timestamp(timestamp)

        self.assertEqual(result, "2024-01-15 10:30")

    def test_format_timestamp_with_timezone(self):
        """测试带时区的时间戳"""
        timestamp = "2024-01-15T10:30:00Z"
        result = self.updater.format_timestamp(timestamp)

        self.assertEqual(result, "2024-01-15 10:30")

    def test_format_invalid_timestamp(self):
        """测试格式化无效时间戳"""
        invalid_timestamp = "not-a-timestamp"
        result = self.updater.format_timestamp(invalid_timestamp)

        # 应该返回原始字符串
        self.assertEqual(result, invalid_timestamp)

    def test_format_empty_timestamp(self):
        """测试空时间戳"""
        result = self.updater.format_timestamp("")

        self.assertEqual(result, "")


class TestTopicUpdaterEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_empty_topics_data(self):
        """测试空议题数据"""
        with patch.object(TopicUpdater, "_load_data"):
            updater = TopicUpdater()
            updater._data = {"version_1": {"topics": {}}}

            current_data = updater.get_current_data()
            self.assertEqual(current_data, {})

    def test_very_large_heat_values(self):
        """测试极大热度值"""
        with patch.object(TopicUpdater, "_load_data"):
            updater = TopicUpdater()
            updater._data = {
                "version_1": {
                    "topics": {
                        "t1": {"name": "议题1", "heat": 999999.0},
                    }
                }
            }

            current_data = updater.get_current_data()
            updated_data, _ = updater.simulate_update(current_data)

            # 应该被限制在100以内
            self.assertLessEqual(updated_data["t1"]["heat"], 100)

    def test_very_small_heat_values(self):
        """测试极小热度值"""
        with patch.object(TopicUpdater, "_load_data"):
            updater = TopicUpdater()
            updater._data = {
                "version_1": {
                    "topics": {
                        "t1": {"name": "议题1", "heat": 0.1},
                    }
                }
            }

            current_data = updater.get_current_data()
            updated_data, _ = updater.simulate_update(current_data)

            # 应该被限制在10以上
            self.assertGreaterEqual(updated_data["t1"]["heat"], 10)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestTopicChangeLog,
        TestUpdateRecord,
        TestTopicUpdaterInit,
        TestTopicUpdaterSimulateUpdate,
        TestTopicUpdaterCreateUpdateRecord,
        TestTopicUpdaterGenerateSummary,
        TestTopicUpdaterGetUpdateHistory,
        TestTopicUpdaterGetHotRisingTopics,
        TestTopicUpdaterGetTopicRankChange,
        TestTopicUpdaterFormatTimestamp,
        TestTopicUpdaterEdgeCases,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
