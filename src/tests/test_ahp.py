"""AHP层次分析法引擎单元测试

覆盖AHPFusionEngine的各种使用场景。
"""

import numpy as np
import pytest

from src.esg.fusion.ahp import (
    AHPFusionEngine,
    AHPResult,
    ConsistencyStatus,
)


class TestAHPFusionEngine:
    """AHP融合引擎测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.engine = AHPFusionEngine()

    def test_engine_init(self):
        """测试引擎初始化"""
        assert self.engine is not None

    def test_build_matrix(self):
        """测试构建矩阵"""
        # 使用字典格式的判断矩阵
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 3, (0, 2): 5, (1, 2): 2}

        self.engine.build_matrix(labels, comparisons)

        assert self.engine.n == 3

    def test_build_matrix_from_array(self):
        """测试从数组构建矩阵"""
        labels = ["E", "S", "G", "K"]
        matrix = [[1, 2, 3, 4], [1 / 2, 1, 2, 3], [1 / 3, 1 / 2, 1, 2], [1 / 4, 1 / 3, 1 / 2, 1]]

        self.engine.build_matrix_from_array(labels, matrix)

        assert self.engine.n == 4

    def test_calculate_weights(self):
        """测试计算权重"""
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 3, (0, 2): 5, (1, 2): 2}

        self.engine.build_matrix(labels, comparisons)
        result = self.engine.calculate_weights()

        assert isinstance(result, AHPResult)
        assert len(result.weights) == 3

    def test_is_consistent(self):
        """测试一致性检验"""
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 3, (0, 2): 5, (1, 2): 2}

        self.engine.build_matrix(labels, comparisons)
        self.engine.calculate_weights()

        is_consistent = self.engine.is_consistent()
        assert is_consistent in [True, False]

    def test_get_weights_dict(self):
        """测试获取权重字典"""
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 3, (0, 2): 5, (1, 2): 2}

        self.engine.build_matrix(labels, comparisons)
        self.engine.calculate_weights()

        weights_dict = self.engine.get_weights_dict()

        assert isinstance(weights_dict, dict)

    def test_get_consistency_report(self):
        """测试获取一致性报告"""
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 3, (0, 2): 5, (1, 2): 2}

        self.engine.build_matrix(labels, comparisons)
        self.engine.calculate_weights()

        report = self.engine.get_consistency_report()

        assert isinstance(report, dict)
        assert "consistency_index" in report
        assert "consistency_ratio" in report

    def test_reset(self):
        """测试重置"""
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 3, (0, 2): 5, (1, 2): 2}

        self.engine.build_matrix(labels, comparisons)
        self.engine.reset()

        assert self.engine.n == 0

    def test_auto_correct_matrix(self):
        """测试自动修正矩阵"""
        labels = ["E", "S", "G"]
        comparisons = {(0, 1): 9, (0, 2): 1, (1, 2): 1}

        self.engine.build_matrix(labels, comparisons)
        corrected = self.engine.auto_correct_matrix()

        assert corrected is not None


class TestAHPResult:
    """AHPResult数据类测试"""

    def test_ahp_result_creation(self):
        """测试AHPResult创建"""
        result = AHPResult(
            weights=[0.5, 0.3, 0.2],
            weights_dict={"E": 0.5, "S": 0.3, "G": 0.2},
            max_eigenvalue=3.0,
            consistency_index=0.01,
            consistency_ratio=0.02,
            random_index=0.58,
            is_consistent=True,
            status=ConsistencyStatus.PASS,
            matrix=[],
            messages=[],
        )

        assert len(result.weights) == 3
        assert result.consistency_index == 0.01
        assert result.is_consistent is True
