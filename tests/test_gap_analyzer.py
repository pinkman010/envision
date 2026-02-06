"""测试差距分析器"""

import pytest
from analysis.gap_analyzer import GapAnalyzer
from core.constants import GAP_THRESHOLD_HIGH, GAP_THRESHOLD_MEDIUM


class TestGapAnalyzer:
    """测试差距分析器"""
    
    def test_analyze_gap(self):
        """测试差距分析"""
        analyzer = GapAnalyzer()
        result = analyzer.analyze_gap("维斯塔斯", company_score=78.5)
        
        assert 'company_score' in result
        assert 'benchmark_score' in result
        assert 'gap' in result
        assert 'dimension_gaps' in result
        assert 'indicator_gaps' in result
    
    def test_calculate_severity(self):
        """测试严重程度计算"""
        analyzer = GapAnalyzer()
        
        # 高差距
        assert analyzer._calculate_severity(GAP_THRESHOLD_HIGH + 1) == "高"
        # 中差距
        assert analyzer._calculate_severity(GAP_THRESHOLD_MEDIUM + 1) == "中"
        assert analyzer._calculate_severity(GAP_THRESHOLD_HIGH - 1) == "中"
        # 低差距
        assert analyzer._calculate_severity(GAP_THRESHOLD_MEDIUM - 1) == "低"
        assert analyzer._calculate_severity(0) == "低"
    
    def test_gap_calculation(self):
        """测试差距计算逻辑"""
        analyzer = GapAnalyzer()
        result = analyzer.analyze_gap("维斯塔斯", company_score=70.0)
        
        # 差距 = 标杆分数 - 公司分数
        expected_gap = result['benchmark_score'] - 70.0
        assert abs(result['gap'] - expected_gap) < 0.1
    
    def test_indicator_gaps_sorted(self):
        """测试指标差距按大小排序"""
        analyzer = GapAnalyzer()
        result = analyzer.analyze_gap("维斯塔斯")
        
        gaps = result['indicator_gaps']
        if len(gaps) > 1:
            # 检查是否按差距降序排列
            for i in range(len(gaps) - 1):
                assert gaps[i]['gap'] >= gaps[i + 1]['gap']
