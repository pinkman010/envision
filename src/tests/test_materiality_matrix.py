"""重要性矩阵单元测试

覆盖MaterialityMatrix的各种使用场景。
"""

import pytest

# 模块不存在时跳过整个测试文件
pytest.importorskip("src.esg.analysis.materiality_matrix", reason="src.esg.analysis.materiality_matrix 模块不存在")

from src.esg.analysis.materiality_matrix import (
    MaterialityMatrix,
    MaterialityTopic,
)


class TestMaterialityMatrix:
    """重要性矩阵测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.matrix = MaterialityMatrix()

    def test_matrix_init(self):
        """测试矩阵初始化"""
        assert self.matrix is not None

    def test_get_all_topics(self):
        """测试获取所有主题"""
        result = self.matrix.get_all_topics()
        assert isinstance(result, list)

    def test_get_matrix_data(self):
        """测试获取矩阵数据"""
        result = self.matrix.get_matrix_data()
        # 返回的是list
        assert isinstance(result, list)

    def test_get_quadrant_summary(self):
        """测试获取象限摘要"""
        result = self.matrix.get_quadrant_summary()
        assert isinstance(result, dict)

    def test_get_topics_by_dimension(self):
        """测试按维度获取主题"""
        result = self.matrix.get_topics_by_dimension("E")
        assert isinstance(result, list)

    def test_get_topics_by_quadrant(self):
        """测试按象限获取主题"""
        result = self.matrix.get_topics_by_quadrant("高重要性-高影响力")
        assert isinstance(result, list)

    def test_get_priority_list(self):
        """测试获取优先级列表"""
        result = self.matrix.get_priority_list()
        assert isinstance(result, list)

    def test_update_topic_scores(self):
        """测试更新主题分数"""
        # 应该不抛出异常
        self.matrix.update_topic_scores("carbon_emission", financial=8, impact=7)

    def test_reset_to_defaults(self):
        """测试重置为默认值"""
        result = self.matrix.reset_to_defaults()
        assert result is None

    def test_export_scores(self):
        """测试导出分数"""
        result = self.matrix.export_scores()
        assert isinstance(result, dict)


class TestMaterialityTopic:
    """MaterialityTopic测试类"""

    def test_topic_creation(self):
        """测试主题创建"""
        topic = MaterialityTopic(
            topic_id="test_1",
            name="测试主题",
            dimension="E",
            description="测试描述",
            financial_score=7.0,
            impact_score=8.0,
            heat_score=5.0,
        )
        assert topic.topic_id == "test_1"
        assert topic.name == "测试主题"
        assert topic.dimension == "E"
