"""边界情况和异常场景测试

测试极端数值、空输入、边界条件等特殊情况。
"""

import math
import sys
import unittest
from decimal import Decimal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.analysis.gap_analyzer import GapAnalyzer, GapResult
from src.esg.core.compliance_checker import ComplianceChecker
from src.esg.core.models import DEFAULT_SCORE, ESGMetrics
from src.esg.extraction.pdf_extractor import PDFExtractor, PDFNotFoundError
from src.esg.fusion.ahp import AHPFusionEngine
from src.esg.utils.html_sanitizer import sanitize_for_markdown, sanitize_html


class TestExtremeValues(unittest.TestCase):
    """极端数值测试"""

    def test_extreme_large_values(self):
        """测试极大数值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=1e15,  # 极大碳排放
            renewable_energy_ratio=1e6,  # 超出合理范围
            energy_efficiency=1e9,
            female_ratio=1e5,
            training_hours=1e10,
            community_investment=1e20,
            board_independence_ratio=1e3,
            ethics_training_coverage=1e4,
            esg_report_quality=1e8,
        )

        # 维度得分应该被限制在合理范围内
        e_score = metrics.get_dimension_score("E")
        self.assertLessEqual(e_score, 100.0)
        self.assertGreaterEqual(e_score, 0.0)

    def test_extreme_small_values(self):
        """测试极小数值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=1e-10,  # 极小碳排放
            renewable_energy_ratio=1e-9,  # 接近0
            energy_efficiency=1e-8,
            female_ratio=1e-7,
            training_hours=1e-6,
            community_investment=1e-5,
            board_independence_ratio=1e-4,
            ethics_training_coverage=1e-3,
            esg_report_quality=1e-2,
        )

        # 维度得分应该能处理极小值
        e_score = metrics.get_dimension_score("E")
        self.assertGreaterEqual(e_score, 0.0)
        self.assertLessEqual(e_score, 100.0)

    def test_zero_values(self):
        """测试零值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=0,
            renewable_energy_ratio=0,
            energy_efficiency=0,
            female_ratio=0,
            training_hours=0,
            community_investment=0,
            board_independence_ratio=0,
            ethics_training_coverage=0,
            esg_report_quality=0,
        )

        # 得分为0或默认值
        e_score = metrics.get_dimension_score("E")
        self.assertGreaterEqual(e_score, 0.0)

    def test_negative_values(self):
        """测试负值处理"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=-1000,  # 负碳排放（理论上可能表示碳抵消）
            renewable_energy_ratio=-0.5,
            energy_efficiency=-80.0,
            female_ratio=-0.4,
            training_hours=-30.0,
            community_investment=-1000000,
            board_independence_ratio=-0.5,
            ethics_training_coverage=-0.8,
            esg_report_quality=-85.0,
        )

        # 系统应该能处理负值（可能返回负分或按0处理）
        e_score = metrics.get_dimension_score("E")
        # 不验证具体值，只确保不抛出异常
        self.assertIsInstance(e_score, float)

    def test_infinity_values(self):
        """测试无穷大值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=float("inf"),
            energy_efficiency=float("inf"),
        )

        # 应该能处理无穷大而不崩溃
        e_score = metrics.get_dimension_score("E")
        self.assertIsInstance(e_score, float)

    def test_nan_values(self):
        """测试NaN值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=float("nan"),
            energy_efficiency=float("nan"),
        )

        # 应该能处理NaN而不崩溃
        e_score = metrics.get_dimension_score("E")
        self.assertIsInstance(e_score, float)


class TestEmptyAndNoneInputs(unittest.TestCase):
    """空输入和None值测试"""

    def test_empty_string_inputs(self):
        """测试空字符串输入"""
        metrics = ESGMetrics(
            company_name="",  # 空公司名称
            year="",  # 空年份
        )

        self.assertEqual(metrics.company_name, "")
        self.assertEqual(metrics.year, "")

    def test_whitespace_only_strings(self):
        """测试仅包含空白字符的字符串"""
        metrics = ESGMetrics(
            company_name="   ",
            year="  \t\n  ",
        )

        self.assertEqual(metrics.company_name, "   ")
        self.assertEqual(metrics.year, "  \t\n  ")

    def test_none_values_in_metrics(self):
        """测试所有指标为None"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            # 所有可选字段保持None
        )

        # 所有维度得分应该返回默认值
        e_score = metrics.get_dimension_score("E")
        s_score = metrics.get_dimension_score("S")
        g_score = metrics.get_dimension_score("G")

        self.assertEqual(e_score, DEFAULT_SCORE)
        self.assertEqual(s_score, DEFAULT_SCORE)
        self.assertEqual(g_score, DEFAULT_SCORE)

    def test_partial_none_values(self):
        """测试部分指标为None"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=0.5,  # 只有E维度部分数据
            female_ratio=0.4,  # 只有S维度部分数据
            board_independence_ratio=0.6,  # 只有G维度部分数据
        )

        # 应该基于可用数据计算得分
        e_score = metrics.get_dimension_score("E")
        s_score = metrics.get_dimension_score("S")
        g_score = metrics.get_dimension_score("G")

        self.assertNotEqual(e_score, DEFAULT_SCORE)
        self.assertNotEqual(s_score, DEFAULT_SCORE)
        self.assertNotEqual(g_score, DEFAULT_SCORE)

    def test_empty_confidence_dict(self):
        """测试空置信度字典"""
        metrics = ESGMetrics(company_name="测试公司", year="2024", confidence={})

        confidence_level = metrics.calculate_overall_confidence()
        self.assertEqual(confidence_level, "极低")

    def test_empty_html_sanitization(self):
        """测试空HTML净化"""
        result = sanitize_html("")
        self.assertEqual(result, "")

        result = sanitize_html(None)  # type: ignore
        self.assertEqual(result, "")

    def test_empty_markdown_sanitization(self):
        """测试空Markdown净化"""
        result = sanitize_for_markdown("")
        self.assertEqual(result, "")

        result = sanitize_for_markdown(None)  # type: ignore
        self.assertEqual(result, "")


class TestBoundaryConditions(unittest.TestCase):
    """边界条件测试"""

    def test_boundary_scores_zero(self):
        """测试边界得分0"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=0,
            energy_efficiency=0,
            waste_recycling_rate=0,
        )

        e_score = metrics.get_dimension_score("E")
        self.assertEqual(e_score, 0.0)

    def test_boundary_scores_maximum(self):
        """测试边界得分最大值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=100.0,  # 超过100%应该被限制
            energy_efficiency=1000.0,  # 远超100
            waste_recycling_rate=1.0,  # 100%
        )

        e_score = metrics.get_dimension_score("E")
        # 得分应该被限制在100以内
        self.assertLessEqual(e_score, 100.0)

    def test_boundary_ratio_values(self):
        """测试边界比例值"""
        test_cases = [
            (0.0, 0.0),  # 最小值
            (0.5, 50.0),  # 中间值
            (1.0, 100.0),  # 最大值（100%）
        ]

        for input_ratio, expected_score in test_cases:
            metrics = ESGMetrics(
                company_name="测试公司",
                year="2024",
                renewable_energy_ratio=input_ratio,
            )
            # 验证单个指标计算
            score = metrics._safe_score(input_ratio, 100.0, 100.0)
            self.assertAlmostEqual(score, expected_score, places=1)

    def test_confidence_boundary_values(self):
        """测试置信度边界值"""
        test_cases = [
            ({"field": 0.0}, "低"),
            ({"field": 0.29}, "低"),
            ({"field": 0.3}, "中"),
            ({"field": 0.59}, "中"),
            ({"field": 0.6}, "较高"),
            ({"field": 0.79}, "较高"),
            ({"field": 0.8}, "高"),
            ({"field": 1.0}, "高"),
        ]

        for confidence_dict, expected_level in test_cases:
            metrics = ESGMetrics(company_name="测试公司", year="2024", confidence=confidence_dict)
            level = metrics.calculate_overall_confidence()
            self.assertEqual(
                level, expected_level, f"置信度{confidence_dict}应该为{expected_level}"
            )


class TestGapAnalyzerEdgeCases(unittest.TestCase):
    """差距分析器边界情况测试"""

    def setUp(self):
        self.analyzer = GapAnalyzer()
        self.test_metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=0.5,
            energy_efficiency=80.0,
            female_ratio=0.4,
            training_hours=30.0,
            board_independence_ratio=0.5,
            ethics_training_coverage=0.8,
            esg_report_quality=85.0,
        )

    def test_gap_with_invalid_benchmark(self):
        """测试无效标杆企业"""
        with self.assertRaises(ValueError) as context:
            self.analyzer.analyze_dimension_gap(self.test_metrics, "不存在的标杆")
        self.assertIn("未找到标杆企业", str(context.exception))

    def test_gap_with_same_values(self):
        """测试与标杆值相同的情况"""
        # 使用行业平均作为标杆
        gaps = self.analyzer.analyze_dimension_gap(self.test_metrics, "行业平均")

        for dim, gap_result in gaps.items():
            # gap应该为0或接近0
            self.assertIsInstance(gap_result.gap, float)


class TestAHPBoundaryConditions(unittest.TestCase):
    """AHP引擎边界条件测试"""

    def setUp(self):
        self.engine = AHPFusionEngine()

    def test_single_criterion(self):
        """测试单标准情况"""
        self.engine.build_matrix(["E"], {})
        result = self.engine.calculate_weights()

        self.assertEqual(len(result.weights), 1)
        self.assertEqual(result.weights[0], 1.0)

    def test_two_criteria(self):
        """测试双标准情况"""
        comparisons = {(0, 1): 2.0}  # E 比 S 重要2倍
        self.engine.build_matrix(["E", "S"], comparisons)
        result = self.engine.calculate_weights()

        self.assertEqual(len(result.weights), 2)
        self.assertAlmostEqual(sum(result.weights), 1.0, places=5)
        # E的权重应该大于S
        self.assertGreater(result.weights[0], result.weights[1])

    def test_extreme_comparison_values(self):
        """测试极端比较值"""
        comparisons = {
            (0, 1): 9.0,  # 最大标准值
            (0, 2): 1 / 9,  # 最小标准值
            (1, 2): 1.0,  # 相等
        }
        self.engine.build_matrix(["E", "S", "G"], comparisons)
        result = self.engine.calculate_weights()

        self.assertEqual(len(result.weights), 3)
        self.assertAlmostEqual(sum(result.weights), 1.0, places=5)


class TestHTMLSanitizerEdgeCases(unittest.TestCase):
    """HTML净化器边界情况测试"""

    def test_nested_tags(self):
        """测试嵌套标签"""
        html = "<p>外层<b>内层<i>最内层</i></b></p>"
        result = sanitize_html(html)
        self.assertIn("<p>", result)
        self.assertIn("<b>", result)
        self.assertIn("<i>", result)

    def test_malformed_html(self):
        """测试畸形HTML"""
        test_cases = [
            "<p>未闭合标签",  # 未闭合
            "<p><b>错误嵌套</p></b>",  # 错误嵌套
            "<p class=无引号>内容</p>",  # 无引号属性
            "<p  >多余空格</p>",  # 多余空格
        ]

        for html in test_cases:
            result = sanitize_html(html)
            # 不应该抛出异常
            self.assertIsInstance(result, str)

    def test_dangerous_attributes(self):
        """测试危险属性"""
        test_cases = [
            ('<p onload="alert(1)">内容</p>', "onload"),
            ('<p ONCLICK="alert(1)">内容</p>', "onclick"),
            ('<p style="background-image:url(javascript:alert(1))">内容</p>', "javascript"),
        ]

        for html, forbidden in test_cases:
            result = sanitize_html(html)
            self.assertNotIn(forbidden.lower(), result.lower())

    def test_unicode_in_html(self):
        """测试HTML中的Unicode"""
        html = "<p>🌍 环境 <script>alert('xss')</script> 保护 ♻️</p>"
        result = sanitize_html(html)

        self.assertIn("🌍", result)
        self.assertIn("♻️", result)
        self.assertNotIn("<script>", result)

    def test_very_long_html(self):
        """测试超长HTML"""
        long_content = "A" * 100000
        html = f"<p>{long_content}</p>"
        result = sanitize_html(html)

        self.assertIn(long_content, result)

    def test_html_entities(self):
        """测试HTML实体"""
        html = "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>"
        result = sanitize_html(html)

        # 实体应该被保留
        self.assertIn("&lt;", result)


class TestStringEncodingEdgeCases(unittest.TestCase):
    """字符串编码边界情况测试"""

    def test_unicode_company_names(self):
        """测试Unicode公司名称"""
        companies = [
            "🌱绿色能源",
            "公司™",
            "公司®",
            "Москва",  # 俄语
            "東京株式会社",  # 日语
            "📊数据公司",
        ]

        for company in companies:
            metrics = ESGMetrics(company_name=company, year="2024")
            self.assertEqual(metrics.company_name, company)

    def test_special_year_formats(self):
        """测试特殊年份格式"""
        year_formats = [
            "2024",
            "2024/2025",
            "FY2024",
            "2023-2024",
            "二〇二四年",  # 中文数字
        ]

        for year in year_formats:
            metrics = ESGMetrics(company_name="测试公司", year=year)
            self.assertEqual(metrics.year, year)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestExtremeValues))
    suite.addTests(loader.loadTestsFromTestCase(TestEmptyAndNoneInputs))
    suite.addTests(loader.loadTestsFromTestCase(TestBoundaryConditions))
    suite.addTests(loader.loadTestsFromTestCase(TestGapAnalyzerEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestAHPBoundaryConditions))
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLSanitizerEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestStringEncodingEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
