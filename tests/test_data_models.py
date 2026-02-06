"""测试数据模型"""

import pytest
from core.data_models import ESGMetrics, AnalysisResult, BenchmarkData


class TestESGMetrics:
    """测试ESG指标模型"""
    
    def test_create_metrics(self):
        """测试创建指标对象"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=50000.0,
            renewable_energy_ratio=45.0
        )
        
        assert metrics.company_name == "测试公司"
        assert metrics.year == "2024"
        assert metrics.carbon_emissions == 50000.0
        assert metrics.renewable_energy_ratio == 45.0
        assert metrics.employee_count is None  # 未设置的字段应为None
    
    def test_dimension_score_with_data(self):
        """测试有数据时的维度得分计算"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=50.0,
            energy_efficiency=80.0,
            waste_recycling_rate=70.0
        )
        
        score = metrics.get_dimension_score('E')
        # (50 + 80 + 70) / 3 = 66.67
        assert 66 < score < 67
    
    def test_dimension_score_with_none(self):
        """测试数据为None时的维度得分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024"
        )
        
        # 没有数据时应返回默认值50.0
        score = metrics.get_dimension_score('E')
        assert score == 50.0
    
    def test_dimension_score_mixed(self):
        """测试部分数据为None时的维度得分"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=60.0,
            energy_efficiency=None,
            waste_recycling_rate=80.0
        )
        
        score = metrics.get_dimension_score('E')
        # (60 + 80) / 2 = 70
        assert score == 70.0
    
    def test_overall_confidence(self):
        """测试整体置信度计算"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            confidence={"carbon_emissions": 0.8, "renewable_energy_ratio": 0.9}
        )
        
        # (0.8 + 0.9) / 2 = 0.85 -> "高"
        assert metrics.calculate_overall_confidence() == "高"
    
    def test_overall_confidence_empty(self):
        """测试无置信度数据时"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024"
        )
        
        assert metrics.calculate_overall_confidence() == "极低"
    
    def test_has_dimension_data(self):
        """测试维度数据存在性检查"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=50.0
        )
        
        assert metrics.has_dimension_data('E') is True
        assert metrics.has_dimension_data('S') is False
        assert metrics.has_dimension_data('G') is False
    
    def test_get_missing_indicators(self):
        """测试获取缺失指标"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=50.0
        )
        
        missing_e = metrics.get_missing_indicators('E')
        assert 'E.carbon_emissions' in missing_e
        assert 'E.renewable_energy_ratio' not in missing_e
        
        all_missing = metrics.get_missing_indicators()
        assert len(all_missing) > 0


class TestAnalysisResult:
    """测试分析结果模型"""
    
    def test_create_result(self):
        """测试创建分析结果"""
        metrics = ESGMetrics(company_name="测试", year="2024")
        
        result = AnalysisResult(
            metrics=metrics,
            weights={"E": 0.4, "S": 0.3, "G": 0.3},
            gap_analysis={},
            strategies=[],
            overall_score=75.5
        )
        
        assert result.overall_score == 75.5
        assert result.confidence_level == "中"


class TestBenchmarkData:
    """测试基准数据模型"""
    
    def test_benchmark_score(self):
        """测试基准得分计算"""
        benchmark = BenchmarkData(
            industry="新能源",
            year="2024",
            avg_renewable_energy_ratio=70.0,
            avg_energy_efficiency=80.0
        )
        
        score = benchmark.get_benchmark_score('E')
        # (70 + 80) / 2 = 75
        assert score == 75.0
    
    def test_benchmark_score_no_data(self):
        """测试无数据时的基准得分"""
        benchmark = BenchmarkData(
            industry="新能源",
            year="2024"
        )
        
        # 无数据时应返回默认值
        score = benchmark.get_benchmark_score('E')
        assert score == 50.0
