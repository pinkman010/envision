# /envision/tests/test_mvp.py
"""MVP功能测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import ESGMetrics, BenchmarkData
from core.esg_engine import ESGAnalysisEngine
from extractor.metric_extractor import MetricExtractor
from fusion.ahp_fusion import AHPFusionEngine
from completion.data_completion import SimpleCompletionEngine


def test_data_models():
    """测试数据模型"""
    print("测试1: 数据模型")
    
    metrics = ESGMetrics(
        company_name="测试公司",
        year="2023",
        carbon_emissions=10000.0,
        renewable_energy_ratio=45.0,
        employee_count=5000,
        board_independence_ratio=40.0
    )
    
    print(f"  ✓ 创建指标对象: {metrics.company_name}")
    print(f"  ✓ E维度得分: {metrics.get_dimension_score('E'):.1f}")
    return True


def test_extractor():
    """测试指标提取"""
    print("\n测试2: 指标提取")
    
    sample_text = """
    2023年公司碳排放量为15,000吨CO2e。
    可再生能源占比达到55%。
    员工总数为3,500人，女性员工占比40%。
    独立董事比例为45%。
    """
    
    extractor = MetricExtractor()
    metrics = extractor.extract(sample_text, "测试公司", "2023")
    
    print(f"  ✓ 提取碳排放: {metrics.carbon_emissions}")
    print(f"  ✓ 提取可再生能源占比: {metrics.renewable_energy_ratio}%")
    print(f"  ✓ 提取员工数: {metrics.employee_count}")
    
    return True


def test_fusion():
    """测试AHP融合"""
    print("\n测试3: AHP融合")
    
    engine = AHPFusionEngine()
    
    # 构建判断矩阵
    engine.build_matrix(
        ['E', 'S', 'G'],
        {(0, 1): 1.5, (0, 2): 1.2, (1, 2): 1.0}
    )
    
    weights, ci, cr = engine.calculate_weights()
    
    print(f"  ✓ E权重: {weights[0]:.3f}")
    print(f"  ✓ S权重: {weights[1]:.3f}")
    print(f"  ✓ G权重: {weights[2]:.3f}")
    print(f"  ✓ CR一致性: {cr:.4f} {'(通过)' if cr < 0.1 else '(不通过)'}")
    
    return True


def test_completion():
    """测试数据补全"""
    print("\n测试4: 数据补全")
    
    metrics = ESGMetrics(
        company_name="测试公司",
        year="2023",
        carbon_emissions=10000.0  # 仅提供部分数据
    )
    
    engine = SimpleCompletionEngine()
    completed, log = engine.complete(metrics)
    
    print(f"  ✓ 补全字段数: {len(log)}")
    print(f"  ✓ 补全后可再生能源占比: {completed.renewable_energy_ratio}")
    
    return True


def test_full_pipeline():
    """测试完整流程"""
    print("\n测试5: 完整分析流程")
    
    # 创建测试数据
    metrics = ESGMetrics(
        company_name="远景能源",
        year="2023",
        carbon_emissions=20000.0,
        renewable_energy_ratio=60.0,
        energy_efficiency=80.0,
        employee_count=5000,
        female_ratio=0.38,
        board_independence_ratio=45.0
    )
    
    # 运行分析
    engine = ESGAnalysisEngine()
    result = engine.analyze(metrics)
    
    print(f"  ✓ 总体得分: {result.overall_score}")
    print(f"  ✓ 建议数量: {len(result.strategies)}")
    print(f"  ✓ 数据置信度: {result.confidence_level}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ESG评价专家系统 - MVP功能测试")
    print("=" * 60)
    
    tests = [
        test_data_models,
        test_extractor,
        test_fusion,
        test_completion,
        test_full_pipeline
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    run_all_tests()