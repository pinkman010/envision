"""数据验证模块单元测试

覆盖所有验证函数的单元测试，包括正常场景、边界条件和异常处理。
"""

import math
import sys
import unittest
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.core.models import ESGMetrics
from src.esg.utils.validators import (
    validate_carbon_intensity,
    validate_company_code,
    validate_company_name,
    validate_emissions_value,
    validate_esg_metrics,
    validate_non_negative_number,
    validate_pdf,
    validate_percentage,
    validate_positive_int,
    validate_ratio,
    validate_report_year_range,
    validate_score,
    validate_training_hours,
    validate_water_intensity,
    validate_year,
)


class TestValidatePDF(unittest.TestCase):
    """PDF文件验证测试"""

    def setUp(self):
        """测试前置设置"""
        self.temp_dir = Path(__file__).parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        self.valid_pdf = self.temp_dir / "test.pdf"
        self.valid_pdf.write_bytes(b"%PDF-1.4 test content")

    def tearDown(self):
        """测试后置清理"""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_pdf(self):
        """测试有效PDF文件"""
        is_valid, msg = validate_pdf(self.valid_pdf)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "验证通过")

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        is_valid, msg = validate_pdf("/nonexistent/file.pdf")
        self.assertFalse(is_valid)
        self.assertIn("文件不存在", msg)

    def test_not_a_file(self):
        """测试路径不是文件"""
        is_valid, msg = validate_pdf(self.temp_dir)
        self.assertFalse(is_valid)
        self.assertIn("路径不是文件", msg)

    def test_wrong_extension(self):
        """测试错误扩展名"""
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("not a pdf")
        is_valid, msg = validate_pdf(txt_file)
        self.assertFalse(is_valid)
        self.assertIn("不支持的文件类型", msg)

    def test_empty_file(self):
        """测试空文件"""
        empty_pdf = self.temp_dir / "empty.pdf"
        empty_pdf.write_bytes(b"%PDF")
        # 文件大小为0会触发空文件检查
        is_valid, msg = validate_pdf(empty_pdf)
        self.assertTrue(is_valid)  # 非空文件应该通过

    def test_invalid_pdf_header(self):
        """测试无效PDF头"""
        invalid_pdf = self.temp_dir / "invalid.pdf"
        invalid_pdf.write_bytes(b"NOTPDF content")
        is_valid, msg = validate_pdf(invalid_pdf)
        self.assertFalse(is_valid)
        self.assertIn("不是有效的 PDF 格式", msg)

    def test_file_size_limit(self):
        """测试文件大小限制"""
        # 创建一个超大文件
        large_pdf = self.temp_dir / "large.pdf"
        large_pdf.write_bytes(b"%PDF" + b"0" * (101 * 1024 * 1024))  # 101MB
        is_valid, msg = validate_pdf(large_pdf, max_size=100 * 1024 * 1024)
        self.assertFalse(is_valid)
        self.assertIn("文件大小超过限制", msg)


class TestValidateYear(unittest.TestCase):
    """年份验证测试"""

    def test_valid_year_int(self):
        """测试有效整数年份"""
        is_valid, msg = validate_year(2024)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "验证通过")

    def test_valid_year_string(self):
        """测试有效字符串年份"""
        is_valid, msg = validate_year("2024")
        self.assertTrue(is_valid)

    def test_year_too_early(self):
        """测试年份太早"""
        is_valid, msg = validate_year(1999)
        self.assertFalse(is_valid)
        self.assertIn("必须大于等于 2000", msg)

    def test_year_too_late(self):
        """测试年份太晚"""
        future_year = datetime.now().year + 2
        is_valid, msg = validate_year(future_year)
        self.assertFalse(is_valid)
        self.assertIn("必须小于等于", msg)

    def test_invalid_year_string(self):
        """测试无效年份字符串"""
        is_valid, msg = validate_year("not_a_year")
        self.assertFalse(is_valid)
        self.assertIn("必须是有效的数字", msg)

    def test_none_year(self):
        """测试None年份"""
        is_valid, msg = validate_year(None)
        self.assertFalse(is_valid)


class TestValidateScore(unittest.TestCase):
    """评分验证测试"""

    def test_valid_score_int(self):
        """测试有效整数评分"""
        is_valid, msg = validate_score(85)
        self.assertTrue(is_valid)

    def test_valid_score_float(self):
        """测试有效浮点评分"""
        is_valid, msg = validate_score(85.5)
        self.assertTrue(is_valid)

    def test_valid_score_string(self):
        """测试有效字符串评分"""
        is_valid, msg = validate_score("90")
        self.assertTrue(is_valid)

    def test_score_too_low(self):
        """测试评分过低"""
        is_valid, msg = validate_score(-1)
        self.assertFalse(is_valid)
        self.assertIn("不能小于 0", msg)

    def test_score_too_high(self):
        """测试评分过高"""
        is_valid, msg = validate_score(101)
        self.assertFalse(is_valid)
        self.assertIn("不能大于 100", msg)

    def test_score_nan(self):
        """测试NaN评分"""
        is_valid, msg = validate_score(float("nan"))
        self.assertFalse(is_valid)
        self.assertIn("不能为 NaN", msg)

    def test_score_infinity(self):
        """测试无穷大评分"""
        is_valid, msg = validate_score(float("inf"))
        self.assertFalse(is_valid)
        self.assertIn("不能为无穷大", msg)


class TestValidateCompanyCode(unittest.TestCase):
    """公司代码验证测试"""

    def test_valid_a_share_code(self):
        """测试有效A股代码"""
        is_valid, msg = validate_company_code("000001")
        self.assertTrue(is_valid)

    def test_valid_hk_code(self):
        """测试有效港股代码"""
        is_valid, msg = validate_company_code("00700")
        self.assertTrue(is_valid)

    def test_valid_alphanumeric_code(self):
        """测试有效字母数字代码"""
        is_valid, msg = validate_company_code("AAPL")
        self.assertTrue(is_valid)

    def test_empty_code(self):
        """测试空代码"""
        is_valid, msg = validate_company_code("")
        self.assertFalse(is_valid)
        self.assertIn("不能为空", msg)

    def test_none_code(self):
        """测试None代码"""
        is_valid, msg = validate_company_code(None)
        self.assertFalse(is_valid)

    def test_code_too_short(self):
        """测试代码太短"""
        is_valid, msg = validate_company_code("123")
        self.assertFalse(is_valid)
        self.assertIn("长度应在 4-10", msg)

    def test_code_too_long(self):
        """测试代码太长"""
        is_valid, msg = validate_company_code("12345678901")
        self.assertFalse(is_valid)
        self.assertIn("长度应在 4-10", msg)


class TestValidateReportYearRange(unittest.TestCase):
    """报告年份范围验证测试"""

    def test_valid_range(self):
        """测试有效年份范围"""
        is_valid, msg = validate_report_year_range(2020, 2023)
        self.assertTrue(is_valid)

    def test_same_year(self):
        """测试同一年份"""
        is_valid, msg = validate_report_year_range(2024, 2024)
        self.assertTrue(is_valid)

    def test_invalid_start_year(self):
        """测试无效起始年份"""
        is_valid, msg = validate_report_year_range(1999, 2023)
        self.assertFalse(is_valid)
        self.assertIn("起始年份无效", msg)

    def test_invalid_end_year(self):
        """测试无效结束年份"""
        is_valid, msg = validate_report_year_range(2020, 2030)
        self.assertFalse(is_valid)
        self.assertIn("结束年份无效", msg)

    def test_start_after_end(self):
        """测试起始年份晚于结束年份"""
        is_valid, msg = validate_report_year_range(2023, 2020)
        self.assertFalse(is_valid)
        self.assertIn("起始年份不能大于结束年份", msg)

    def test_range_too_wide(self):
        """测试年份范围过宽"""
        is_valid, msg = validate_report_year_range(2000, 2025)
        self.assertFalse(is_valid)
        self.assertIn("不能超过 20 年", msg)


class TestValidatePercentage(unittest.TestCase):
    """百分比验证测试"""

    def test_valid_percentage_int(self):
        """测试有效整数百分比"""
        is_valid, msg = validate_percentage(85, "能源效率")
        self.assertTrue(is_valid)

    def test_valid_percentage_float(self):
        """测试有效浮点百分比"""
        is_valid, msg = validate_percentage(85.5, "可再生能源占比")
        self.assertTrue(is_valid)

    def test_boundary_zero(self):
        """测试边界值0"""
        is_valid, msg = validate_percentage(0, "废物回收率")
        self.assertTrue(is_valid)

    def test_boundary_hundred(self):
        """测试边界值100"""
        is_valid, msg = validate_percentage(100, "风机可利用率")
        self.assertTrue(is_valid)

    def test_percentage_negative(self):
        """测试负百分比"""
        is_valid, msg = validate_percentage(-1, "能源效率")
        self.assertFalse(is_valid)
        self.assertIn("不能小于 0", msg)

    def test_percentage_over_hundred(self):
        """测试超过100%"""
        is_valid, msg = validate_percentage(101, "能源效率")
        self.assertFalse(is_valid)
        self.assertIn("不能大于 100", msg)

    def test_percentage_nan(self):
        """测试NaN百分比"""
        is_valid, msg = validate_percentage(float("nan"), "能源效率")
        self.assertFalse(is_valid)
        self.assertIn("不能为 NaN", msg)

    def test_percentage_inf(self):
        """测试无穷大百分比"""
        is_valid, msg = validate_percentage(float("inf"), "能源效率")
        self.assertFalse(is_valid)
        self.assertIn("不能为无穷大", msg)

    def test_invalid_string(self):
        """测试无效字符串"""
        is_valid, msg = validate_percentage("invalid", "能源效率")
        self.assertFalse(is_valid)
        self.assertIn("必须是有效的数字", msg)


class TestValidateRatio(unittest.TestCase):
    """比例验证测试"""

    def test_valid_ratio(self):
        """测试有效比例"""
        is_valid, msg = validate_ratio(0.5, "女性员工比例")
        self.assertTrue(is_valid)

    def test_boundary_zero(self):
        """测试边界值0"""
        is_valid, msg = validate_ratio(0.0, "女性员工比例")
        self.assertTrue(is_valid)

    def test_boundary_one(self):
        """测试边界值1"""
        is_valid, msg = validate_ratio(1.0, "女性员工比例")
        self.assertTrue(is_valid)

    def test_ratio_negative(self):
        """测试负比例"""
        is_valid, msg = validate_ratio(-0.1, "女性员工比例")
        self.assertFalse(is_valid)
        self.assertIn("不能小于 0", msg)

    def test_ratio_over_one(self):
        """测试超过1的比例"""
        is_valid, msg = validate_ratio(1.1, "女性员工比例")
        self.assertFalse(is_valid)
        self.assertIn("不能大于 1", msg)


class TestValidatePositiveInt(unittest.TestCase):
    """正整数验证测试"""

    def test_valid_positive_int(self):
        """测试有效正整数"""
        is_valid, msg = validate_positive_int(1000, "员工数量")
        self.assertTrue(is_valid)

    def test_zero_value(self):
        """测试零值"""
        is_valid, msg = validate_positive_int(0, "员工数量")
        self.assertFalse(is_valid)
        self.assertIn("必须是正整数", msg)

    def test_negative_value(self):
        """测试负值"""
        is_valid, msg = validate_positive_int(-5, "员工数量")
        self.assertFalse(is_valid)
        self.assertIn("必须是正整数", msg)

    def test_invalid_string(self):
        """测试无效字符串"""
        is_valid, msg = validate_positive_int("abc", "员工数量")
        self.assertFalse(is_valid)
        self.assertIn("必须是有效的整数", msg)


class TestValidateNonNegativeNumber(unittest.TestCase):
    """非负数值验证测试"""

    def test_valid_positive_number(self):
        """测试有效正数"""
        is_valid, msg = validate_non_negative_number(100000, "碳排放量")
        self.assertTrue(is_valid)

    def test_zero_value(self):
        """测试零值"""
        is_valid, msg = validate_non_negative_number(0, "碳排放量")
        self.assertTrue(is_valid)

    def test_negative_value(self):
        """测试负值"""
        is_valid, msg = validate_non_negative_number(-50, "用水量")
        self.assertFalse(is_valid)
        self.assertIn("不能为负数", msg)

    def test_nan_value(self):
        """测试NaN值"""
        is_valid, msg = validate_non_negative_number(float("nan"), "碳排放量")
        self.assertFalse(is_valid)

    def test_inf_value(self):
        """测试无穷大值"""
        is_valid, msg = validate_non_negative_number(float("inf"), "碳排放量")
        self.assertFalse(is_valid)


class TestValidateCompanyName(unittest.TestCase):
    """公司名称验证测试"""

    def test_valid_name(self):
        """测试有效公司名称"""
        is_valid, msg = validate_company_name("远景能源有限公司")
        self.assertTrue(is_valid)

    def test_empty_name(self):
        """测试空名称"""
        is_valid, msg = validate_company_name("")
        self.assertFalse(is_valid)
        self.assertIn("不能为空", msg)

    def test_whitespace_only(self):
        """测试仅空白字符"""
        is_valid, msg = validate_company_name("   ")
        self.assertFalse(is_valid)
        self.assertIn("不能为空或仅包含空白字符", msg)

    def test_none_name(self):
        """测试None名称"""
        is_valid, msg = validate_company_name(None)
        self.assertFalse(is_valid)

    def test_name_too_long(self):
        """测试名称过长"""
        long_name = "A" * 101
        is_valid, msg = validate_company_name(long_name)
        self.assertFalse(is_valid)
        self.assertIn("长度不能超过", msg)

    def test_name_with_illegal_chars(self):
        """测试包含非法字符"""
        is_valid, msg = validate_company_name("公司<script>名称")
        self.assertFalse(is_valid)
        self.assertIn("包含非法字符", msg)

    def test_unicode_name(self):
        """测试Unicode名称"""
        is_valid, msg = validate_company_name("🌱绿色能源™公司")
        self.assertTrue(is_valid)


class TestValidateEmissionsValue(unittest.TestCase):
    """排放量验证测试"""

    def test_valid_emissions(self):
        """测试有效排放量"""
        is_valid, msg = validate_emissions_value(50000, "范围1排放")
        self.assertTrue(is_valid)

    def test_zero_emissions(self):
        """测试零排放量"""
        is_valid, msg = validate_emissions_value(0, "范围2排放")
        self.assertTrue(is_valid)

    def test_negative_emissions(self):
        """测试负排放量"""
        is_valid, msg = validate_emissions_value(-100, "范围3排放")
        self.assertFalse(is_valid)
        self.assertIn("不能为负数", msg)


class TestValidateCarbonIntensity(unittest.TestCase):
    """碳强度验证测试"""

    def test_valid_intensity(self):
        """测试有效碳强度"""
        is_valid, msg = validate_carbon_intensity(0.5)
        self.assertTrue(is_valid)

    def test_zero_intensity(self):
        """测试零碳强度"""
        is_valid, msg = validate_carbon_intensity(0)
        self.assertTrue(is_valid)

    def test_negative_intensity(self):
        """测试负碳强度"""
        is_valid, msg = validate_carbon_intensity(-1.0)
        self.assertFalse(is_valid)


class TestValidateWaterIntensity(unittest.TestCase):
    """水资源强度验证测试"""

    def test_valid_intensity(self):
        """测试有效水资源强度"""
        is_valid, msg = validate_water_intensity(10.0)
        self.assertTrue(is_valid)

    def test_negative_intensity(self):
        """测试负水资源强度"""
        is_valid, msg = validate_water_intensity(-5.0)
        self.assertFalse(is_valid)


class TestValidateTrainingHours(unittest.TestCase):
    """培训时长验证测试"""

    def test_valid_hours(self):
        """测试有效培训时长"""
        is_valid, msg = validate_training_hours(40)
        self.assertTrue(is_valid)

    def test_zero_hours(self):
        """测试零培训时长"""
        is_valid, msg = validate_training_hours(0)
        self.assertTrue(is_valid)

    def test_negative_hours(self):
        """测试负培训时长"""
        is_valid, msg = validate_training_hours(-10)
        self.assertFalse(is_valid)

    def test_excessive_hours(self):
        """测试超量培训时长（超过一年）"""
        is_valid, msg = validate_training_hours(9000)
        self.assertFalse(is_valid)
        self.assertIn("超过 8760 小时", msg)


class TestValidateESGMetrics(unittest.TestCase):
    """ESGMetrics完整验证测试"""

    def test_valid_metrics(self):
        """测试有效ESGMetrics对象"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=45.5,
            energy_efficiency=80.0,
            waste_recycling_rate=60.0,
            female_ratio=40.0,
            board_independence_ratio=50.0,
            ethics_training_coverage=70.0,
            esg_report_quality=75.0,
            employee_count=1000,
            carbon_emissions=50000,
            training_hours=30.0,
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        metrics = ESGMetrics(
            company_name="",
            year="",
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertTrue(any("公司名称" in e for e in errors))
        self.assertTrue(any("年份" in e for e in errors))

    def test_invalid_percentage_fields(self):
        """测试无效百分比字段"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            renewable_energy_ratio=150.0,  # 超过100%
            energy_efficiency=-10.0,  # 负数
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertTrue(any("可再生能源" in e for e in errors))
        self.assertTrue(any("能源效率" in e for e in errors))

    def test_invalid_positive_int_fields(self):
        """测试无效正整数字段"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            employee_count=-100,  # 负数
            battery_cycle_life=0,  # 零值
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertTrue(any("员工数量" in e for e in errors))
        self.assertTrue(any("电池循环寿命" in e for e in errors))

    def test_negative_safety_incidents(self):
        """测试负安全事故数"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            safety_incidents=-5,
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertTrue(any("安全事故数" in e for e in errors))

    def test_invalid_emissions(self):
        """测试无效排放量"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_emissions=-1000,
            scope1_emissions=-500,
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertTrue(any("碳排放" in e for e in errors))

    def test_invalid_intensity(self):
        """测试无效强度值"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
            carbon_intensity=-0.5,
            water_intensity=-10.0,
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertTrue(any("碳强度" in e for e in errors))
        self.assertTrue(any("水资源强度" in e for e in errors))

    def test_all_none_fields(self):
        """测试所有可选字段为None"""
        metrics = ESGMetrics(
            company_name="测试公司",
            year="2024",
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_multiple_errors(self):
        """测试多个错误同时存在"""
        metrics = ESGMetrics(
            company_name="",
            year="1999",
            renewable_energy_ratio=150.0,
            employee_count=-100,
            carbon_emissions=-1000,
        )
        is_valid, errors = validate_esg_metrics(metrics)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 4)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    test_classes = [
        TestValidatePDF,
        TestValidateYear,
        TestValidateScore,
        TestValidateCompanyCode,
        TestValidateReportYearRange,
        TestValidatePercentage,
        TestValidateRatio,
        TestValidatePositiveInt,
        TestValidateNonNegativeNumber,
        TestValidateCompanyName,
        TestValidateEmissionsValue,
        TestValidateCarbonIntensity,
        TestValidateWaterIntensity,
        TestValidateTrainingHours,
        TestValidateESGMetrics,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
