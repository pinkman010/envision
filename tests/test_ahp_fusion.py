"""测试AHP融合引擎"""

import pytest
import numpy as np
from fusion.ahp_fusion import AHPFusionEngine


class TestAHPFusionEngine:
    """测试AHP引擎"""
    
    def test_build_matrix(self):
        """测试构建判断矩阵"""
        ahp = AHPFusionEngine()
        matrix = ahp.build_matrix(
            ['E', 'S', 'G'],
            {(0, 1): 2.0, (0, 2): 3.0, (1, 2): 2.0}
        )
        
        # 检查矩阵形状
        assert matrix.shape == (3, 3)
        # 检查对角线为1
        assert matrix[0, 0] == 1.0
        # 检查互反性
        assert matrix[0, 1] == 2.0
        assert matrix[1, 0] == 0.5
    
    def test_calculate_weights(self):
        """测试权重计算"""
        ahp = AHPFusionEngine()
        ahp.build_matrix(
            ['E', 'S', 'G'],
            {(0, 1): 1.0, (0, 2): 1.0, (1, 2): 1.0}
        )
        
        weights, ci, cr = ahp.calculate_weights()
        
        # 完全相同的比较应产生相等的权重
        assert len(weights) == 3
        assert abs(weights[0] - 0.333) < 0.01
        assert abs(weights[1] - 0.333) < 0.01
        assert abs(weights[2] - 0.333) < 0.01
        # 完全一致的矩阵CR应为0
        assert cr == 0.0
    
    def test_is_consistent(self):
        """测试一致性检验"""
        ahp = AHPFusionEngine()
        # 完全一致的矩阵
        ahp.build_matrix(
            ['E', 'S', 'G'],
            {(0, 1): 1.0, (0, 2): 1.0, (1, 2): 1.0}
        )
        
        assert ahp.is_consistent() is True
    
    def test_get_weights_dict(self):
        """测试获取权重字典"""
        ahp = AHPFusionEngine()
        ahp.build_matrix(
            ['E', 'S', 'G'],
            {(0, 1): 2.0, (0, 2): 3.0, (1, 2): 2.0}
        )
        
        weights_dict = ahp.get_weights_dict()
        
        assert 'E' in weights_dict
        assert 'S' in weights_dict
        assert 'G' in weights_dict
        assert abs(sum(weights_dict.values()) - 1.0) < 0.001
    
    def test_generate_suggestions(self):
        """测试建议生成"""
        ahp = AHPFusionEngine()
        
        suggestion = ahp.generate_suggestions('financial')
        
        assert 'weights' in suggestion
        assert 'reasoning' in suggestion
        assert 'confidence' in suggestion
        # 投资者视角G权重最高
        assert suggestion['weights']['G'] > suggestion['weights']['E']
    
    def test_error_handling(self):
        """测试错误处理"""
        ahp = AHPFusionEngine()
        
        # 未构建矩阵就计算应报错
        with pytest.raises(ValueError, match="请先构建判断矩阵"):
            ahp.calculate_weights()
