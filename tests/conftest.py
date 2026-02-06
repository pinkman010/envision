"""Pytest配置和共享fixture"""

import pytest
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def sample_metrics_data():
    """示例ESG指标数据"""
    return {
        "company_name": "测试公司",
        "year": "2024",
        "carbon_emissions": 50000.0,
        "renewable_energy_ratio": 45.0,
        "energy_efficiency": 85.0,
        "employee_count": 5000,
        "female_ratio": 0.35,
        "training_hours": 25.0,
        "board_independence_ratio": 60.0
    }


@pytest.fixture
def mock_gap_analysis():
    """模拟差距分析结果"""
    return {
        "company_score": 75.5,
        "benchmark_score": 88.2,
        "gap": 12.7,
        "status": "落后",
        "dimension_gaps": {
            "E": {"company": 78.0, "benchmark": 90.5, "gap": 12.5},
            "S": {"company": 74.0, "benchmark": 86.8, "gap": 12.8},
            "G": {"company": 74.5, "benchmark": 87.3, "gap": 12.8}
        },
        "indicator_gaps": [
            {"id": "scope3_data", "name": "Scope 3数据披露", "company_score": 60, "benchmark_score": 82, "gap": 22, "severity": "高", "disclosure_level": "基础"},
            {"id": "supply_chain", "name": "供应链透明度", "company_score": 70, "benchmark_score": 88, "gap": 18, "severity": "高", "disclosure_level": "中等"}
        ]
    }
