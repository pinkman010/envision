"""端到端(E2E)测试

覆盖完整用户工作流的端到端测试。
由于Streamlit UI测试需要特殊工具，这里主要测试核心业务流程。
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.completion.report_generator import ReportGenerator
from src.esg.core.compliance_checker import ComplianceChecker
from src.esg.core.models import AnalysisResult, ESGMetrics
from src.esg.utils.validators import validate_esg_metrics


class TestEndToEndWorkflow(unittest.TestCase):
    """端到端工作流测试"""

    def setUp(self):
        """测试前置"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后置"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_analysis_workflow(self):
        """测试完整分析工作流"""
        # 1. 创建ESG指标数据
        metrics = ESGMetrics(
            company_name="远景能源测试公司",
            year="2024",
            carbon_emissions=50000,
            renewable_energy_ratio=45.0,
            energy_efficiency=80.0,
            waste_recycling_rate=60.0,
            employee_count=3000,
            female_ratio=35.0,
            training_hours=30.0,
            safety_incidents=2,
            community_investment=5000000,
            board_independence_ratio=40.0,
            ethics_training_coverage=70.0,
            esg_report_quality=75.0,
            carbon_intensity=0.8,
            water_intensity=20.0,
        )

        # 2. 验证数据
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertTrue(is_valid, f"数据验证失败: {errors}")

        # 3. 合规检查
        checker = ComplianceChecker()
        compliance_results = checker.check_compliance(metrics)
        self.assertIsInstance(compliance_results, dict)
        self.assertGreater(len(compliance_results), 0)

        # 4. 差距分析
        analyzer = GapAnalyzer()
        gap_results = analyzer.analyze_dimension_gap(metrics, "行业平均")
        self.assertIn("E", gap_results)
        self.assertIn("S", gap_results)
        self.assertIn("G", gap_results)

        # 5. 计算维度得分
        e_score = metrics.get_dimension_score("E")
        s_score = metrics.get_dimension_score("S")
        g_score = metrics.get_dimension_score("G")

        self.assertGreater(e_score, 0)
        self.assertGreater(s_score, 0)
        self.assertGreater(g_score, 0)

        # 6. 创建分析结果
        weights = {"E": 0.4, "S": 0.3, "G": 0.3}
        overall_score = e_score * weights["E"] + s_score * weights["S"] + g_score * weights["G"]

        result = AnalysisResult(
            metrics=metrics,
            weights=weights,
            gap_analysis={"dimensions": gap_results},
            overall_score=round(overall_score, 1),
            confidence_level=metrics.calculate_overall_confidence(),
        )

        # 7. 生成报告
        generator = ReportGenerator()
        report = generator.generate(result)

        self.assertIn("远景能源测试公司", report)
        self.assertIn("2024", report)
        self.assertIn("ESG", report)

    def test_data_import_to_report_workflow(self):
        """测试数据导入到报告生成工作流"""
        # 模拟从PDF提取的数据
        extracted_data = {
            "company_name": "测试企业",
            "year": "2024",
            "carbon_emissions": 100000,
            "renewable_energy_ratio": 30.0,
            "employee_count": 5000,
            "board_independence_ratio": 45.0,
        }

        # 创建ESG指标
        metrics = ESGMetrics(
            company_name=extracted_data["company_name"],
            year=extracted_data["year"],
            carbon_emissions=extracted_data["carbon_emissions"],
            renewable_energy_ratio=extracted_data["renewable_energy_ratio"],
            employee_count=extracted_data["employee_count"],
            board_independence_ratio=extracted_data["board_independence_ratio"],
        )

        # 验证数据
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertTrue(is_valid)

        # 生成报告
        result = AnalysisResult(
            metrics=metrics,
            overall_score=65.0,
        )

        generator = ReportGenerator()
        report = generator.generate(result)

        self.assertIn("测试企业", report)


class TestIntegrationScenarios(unittest.TestCase):
    """集成场景测试"""

    def test_multiple_companies_comparison(self):
        """测试多公司对比场景"""
        companies = [
            ESGMetrics(
                company_name=f"公司{i}",
                year="2024",
                renewable_energy_ratio=30.0 + i * 10,
                energy_efficiency=70.0 + i * 5,
                employee_count=1000 * (i + 1),
            )
            for i in range(3)
        ]

        analyzer = GapAnalyzer()

        for company in companies:
            gaps = analyzer.analyze_dimension_gap(company, "行业平均")
            self.assertIsNotNone(gaps)

    def test_yearly_comparison(self):
        """测试年度对比场景"""
        years = ["2022", "2023", "2024"]

        results = []
        for year in years:
            metrics = ESGMetrics(
                company_name="远景能源",
                year=year,
                renewable_energy_ratio=30.0 + int(year) - 2022,
                carbon_emissions=100000 - (int(year) - 2022) * 5000,
            )
            results.append(metrics)

        # 验证年度改进趋势
        for i in range(1, len(results)):
            prev_renewable = results[i - 1].renewable_energy_ratio
            curr_renewable = results[i].renewable_energy_ratio
            self.assertGreater(curr_renewable, prev_renewable)


class TestErrorRecoveryWorkflow(unittest.TestCase):
    """错误恢复工作流测试"""

    def test_partial_data_recovery(self):
        """测试部分数据恢复"""
        # 只有部分数据可用
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=50.0,  # 只有部分数据
        )

        # 应该能继续处理
        e_score = metrics.get_dimension_score("E")
        self.assertIsInstance(e_score, float)

        # 生成报告（可能包含警告）
        result = AnalysisResult(
            metrics=metrics,
            overall_score=e_score,
            data_quality_warnings=["数据不完整"],
        )

        self.assertTrue(result.has_data_quality_issues())

    def test_validation_error_handling(self):
        """测试验证错误处理"""
        # 创建包含错误的数据
        metrics = ESGMetrics(
            company_name="",  # 空名称
            year="invalid",  # 无效年份
            renewable_energy_ratio=150.0,  # 超出范围
        )

        # 验证应该失败
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestPerformanceScenarios(unittest.TestCase):
    """性能场景测试"""

    def test_large_dataset_handling(self):
        """测试大数据集处理"""
        # 创建大量指标数据
        metrics_list = []
        for i in range(100):
            metrics = ESGMetrics(
                company_name=f"公司{i}",
                year="2024",
                renewable_energy_ratio=float(i),
                employee_count=i * 100,
            )
            metrics_list.append(metrics)

        # 应该能快速处理
        for metrics in metrics_list[:10]:  # 只测试前10个
            score = metrics.get_dimension_score("E")
            self.assertIsInstance(score, float)


class TestBoundaryWorkflows(unittest.TestCase):
    """边界工作流测试"""

    def test_minimum_viable_data(self):
        """测试最小可用数据"""
        metrics = ESGMetrics(
            company_name="测试",
            year="2024",
        )

        # 应该能正常工作
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertTrue(is_valid)

        e_score = metrics.get_dimension_score("E")
        self.assertIsInstance(e_score, float)

    def test_maximum_data(self):
        """测试最大数据量"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            # 所有字段都填充
            carbon_emissions=999999999,
            renewable_energy_ratio=100.0,
            energy_efficiency=100.0,
            waste_recycling_rate=100.0,
            female_ratio=100.0,
            board_independence_ratio=100.0,
            ethics_training_coverage=100.0,
            esg_report_quality=100.0,
            employee_count=999999,
            training_hours=8760,  # 一年总小时数
            safety_incidents=0,
            community_investment=999999999,
        )

        is_valid, errors = validate_esg_metrics(metrics)
        self.assertTrue(is_valid)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestEndToEndWorkflow,
        TestIntegrationScenarios,
        TestErrorRecoveryWorkflow,
        TestPerformanceScenarios,
        TestBoundaryWorkflows,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
