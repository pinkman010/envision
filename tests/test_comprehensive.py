"""综合测试套件

覆盖核心模块的单元测试，确保端到端流程正常运行。
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import ESGMetrics, AnalysisResult
from src.core.compliance_checker import ComplianceChecker
from src.analysis.gap_analyzer import GapAnalyzer
from src.analysis.business_mapper import BusinessAlignmentMapper
from src.fusion.ahp import AHPFusionEngine
from src.utils.html_sanitizer import HTMLSanitizer, sanitize_html


class TestESGMetrics(unittest.TestCase):
    """ESG指标模型测试"""
    
    def test_dimension_score_calculation(self):
        """测试维度得分计算"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=0.5,
            energy_efficiency=80.0,
            waste_recycling_rate=0.7,
            female_ratio=0.4,
            training_hours=30.0,
            community_investment=1000000,
            board_independence_ratio=0.5,
            ethics_training_coverage=0.8,
            esg_report_quality=85.0
        )
        
        # 测试E维度得分
        e_score = metrics.get_dimension_score('E')
        self.assertGreater(e_score, 0)
        self.assertLessEqual(e_score, 100)
        
        # 测试S维度得分
        s_score = metrics.get_dimension_score('S')
        self.assertGreater(s_score, 0)
        
        # 测试G维度得分
        g_score = metrics.get_dimension_score('G')
        self.assertGreater(g_score, 0)
    
    def test_confidence_calculation(self):
        """测试置信度计算"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            confidence={"carbon_emissions": 0.8, "renewable_energy_ratio": 0.9}
        )
        
        confidence = metrics.calculate_overall_confidence()
        self.assertIn(confidence, ["极低", "低", "中", "较高", "高"])


class TestComplianceChecker(unittest.TestCase):
    """合规检查器测试"""
    
    def setUp(self):
        """测试前置"""
        self.checker = ComplianceChecker()
        self.test_metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=10000,
            renewable_energy_ratio=35.5,
            energy_efficiency=82.0,
            water_consumption=50000,
            waste_recycling_rate=78.0,
            employee_count=5000,
            female_ratio=0.42,
            training_hours=25.0,
            safety_incidents=2,
            community_investment=500000,
            board_independence_ratio=0.67,
            ethics_training_coverage=95.0,
            esg_report_quality=85.0
        )
    
    def test_compliance_check(self):
        """测试合规检查"""
        results = self.checker.check_compliance(self.test_metrics)
        
        # 验证返回结果
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
        
        # 验证结果格式
        for std_id, result in results.items():
            self.assertIn("status", result)
            self.assertIn("score", result)
            self.assertIn("missing_items", result)
            self.assertIn(result["status"], ["已合规", "未合规", "部分合规"])
    
    def test_compliance_rate(self):
        """测试合规率计算"""
        rate = self.checker.get_compliance_rate(self.test_metrics)
        
        self.assertIsInstance(rate, float)
        self.assertGreaterEqual(rate, 0.0)
        self.assertLessEqual(rate, 1.0)
    
    def test_compliance_summary(self):
        """测试合规汇总"""
        summary = self.checker.get_compliance_summary(self.test_metrics)
        
        self.assertIn("overall_rate", summary)
        self.assertIn("total_clauses", summary)
        self.assertIn("compliant_count", summary)
        self.assertIn("non_compliant_count", summary)


class TestGapAnalyzer(unittest.TestCase):
    """差距分析器测试"""
    
    def setUp(self):
        """测试前置"""
        self.analyzer = GapAnalyzer()
        self.test_metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=0.4,
            energy_efficiency=75.0,
            waste_recycling_rate=0.6,
            female_ratio=0.35,
            training_hours=20.0,
            board_independence_ratio=0.4,
            ethics_training_coverage=0.7,
            esg_report_quality=75.0
        )
    
    def test_dimension_gap_analysis(self):
        """测试维度差距分析"""
        gaps = self.analyzer.analyze_dimension_gap(self.test_metrics, "行业平均")
        
        self.assertIsInstance(gaps, dict)
        self.assertIn("E", gaps)
        self.assertIn("S", gaps)
        self.assertIn("G", gaps)
        
        # 验证差距结果格式 (GapResult是dataclass，使用属性访问)
        for dim, gap in gaps.items():
            self.assertIn(dim, ["E", "S", "G"])
            self.assertIsInstance(gap.current, (int, float))
            self.assertIsInstance(gap.benchmark, (int, float))
            self.assertIsInstance(gap.gap, (int, float))
            self.assertIn(gap.priority, ["高", "中", "低"])


class TestBusinessMapper(unittest.TestCase):
    """业务映射器测试"""
    
    def setUp(self):
        """测试前置"""
        self.mapper = BusinessAlignmentMapper()
    
    def test_get_related_units(self):
        """测试获取关联业务单元"""
        units = self.mapper.get_related_units("carbon_emission")
        
        self.assertIsInstance(units, list)
        if units:  # 如果有映射
            self.assertIn("name", units[0])
            self.assertIn("impact", units[0])
    
    def test_get_topic_summary(self):
        """测试获取议题汇总"""
        summary = self.mapper.get_topic_summary_by_unit()
        
        self.assertIsInstance(summary, dict)
        for unit_name, counts in summary.items():
            self.assertIn("高", counts)
            self.assertIn("中", counts)
            self.assertIn("低", counts)
            self.assertIn("总计", counts)
    
    def test_get_risk_matrix(self):
        """测试获取风险矩阵"""
        matrix = self.mapper.get_risk_matrix_data()
        
        self.assertIsInstance(matrix, list)
        if matrix:
            self.assertIn("business_unit", matrix[0])
            self.assertIn("topics", matrix[0])


class TestAHPFusionEngine(unittest.TestCase):
    """AHP融合引擎测试"""
    
    def setUp(self):
        """测试前置"""
        self.engine = AHPFusionEngine()
    
    def test_matrix_building(self):
        """测试矩阵构建"""
        comparisons = {
            (0, 1): 3.0,  # E vs S
            (0, 2): 5.0,  # E vs G
            (1, 2): 2.0,  # S vs G
        }
        
        self.engine.build_matrix(["E", "S", "G"], comparisons)
        
        self.assertIsNotNone(self.engine.matrix)
        self.assertEqual(self.engine.n, 3)
    
    def test_weight_calculation(self):
        """测试权重计算"""
        comparisons = {
            (0, 1): 2.0,
            (0, 2): 3.0,
            (1, 2): 2.0,
        }
        
        self.engine.build_matrix(["E", "S", "G"], comparisons)
        result = self.engine.calculate_weights()
        
        self.assertIsNotNone(result.weights)
        self.assertEqual(len(result.weights), 3)
        self.assertAlmostEqual(sum(result.weights), 1.0, places=5)
        self.assertIn("is_consistent", result.__dict__)


class TestHTMLSanitizer(unittest.TestCase):
    """HTML净化器测试"""
    
    def test_sanitize_safe_html(self):
        """测试安全HTML"""
        html = "<p>这是一个<b>测试</b>段落</p>"
        result = sanitize_html(html)
        
        self.assertIn("<p>", result)
        self.assertIn("</p>", result)
    
    def test_sanitize_dangerous_html(self):
        """测试危险HTML"""
        html = '<p onclick="alert(\'xss\')">测试</p>'
        result = sanitize_html(html)
        
        # onclick属性应该被移除
        self.assertNotIn("onclick", result)
    
    def test_sanitize_javascript_protocol(self):
        """测试JavaScript协议"""
        html = '<a href="javascript:alert(\'xss\')">链接</a>'
        result = sanitize_html(html)
        
        # javascript: 协议应该被移除
        self.assertNotIn("javascript:", result.lower())
    
    def test_sanitize_script_tag(self):
        """测试script标签"""
        html = "<script>alert('xss')</script><p>安全内容</p>"
        result = sanitize_html(html)
        
        # script标签应该被转义或移除
        self.assertNotIn("<script>", result.lower())
        self.assertNotIn("</script>", result.lower())
        # 确保安全内容被保留
        self.assertIn("安全内容", result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_end_to_end_analysis(self):
        """测试端到端分析流程"""
        # 1. 创建测试指标
        metrics = ESGMetrics(
            company_name="集成测试公司",
            year="2024",
            carbon_emissions=5000,
            renewable_energy_ratio=0.6,
            energy_efficiency=85.0,
            employee_count=1000,
            female_ratio=0.4,
            training_hours=35.0,
            board_independence_ratio=0.5,
            ethics_training_coverage=0.9,
            esg_report_quality=80.0
        )
        
        # 2. 合规检查
        checker = ComplianceChecker()
        compliance_results = checker.check_compliance(metrics)
        self.assertIsNotNone(compliance_results)
        
        # 3. 差距分析
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze_dimension_gap(metrics, "行业平均")
        self.assertIsNotNone(gaps)
        
        # 4. AHP权重计算
        engine = AHPFusionEngine()
        comparisons = {(0, 1): 2.0, (0, 2): 3.0, (1, 2): 1.5}
        engine.build_matrix(["E", "S", "G"], comparisons)
        weights = engine.calculate_weights()
        self.assertIsNotNone(weights)
        
        # 5. 创建分析结果
        result = AnalysisResult(
            metrics=metrics,
            weights=weights.weights_dict,
            gap_analysis={"dimensions": gaps},
            overall_score=75.0
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.metrics.company_name, "集成测试公司")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestESGMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestComplianceChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestGapAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestBusinessMapper))
    suite.addTests(loader.loadTestsFromTestCase(TestAHPFusionEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLSanitizer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
