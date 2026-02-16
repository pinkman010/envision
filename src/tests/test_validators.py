"""数据验证器单元测试

覆盖validators模块的各种验证函数。
"""

import sys
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

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


class TestValidateYear(unittest.TestCase):
    """年份验证测试"""

    def test_validate_year_valid(self):
        """测试有效年份"""
        is_valid, message = validate_year("2024")
        self.assertTrue(is_valid)

    def test_validate_year_invalid_format(self):
        """测试无效年份格式"""
        is_valid, message = validate_year("abcd")
        self.assertFalse(is_valid)

    def test_validate_year_out_of_range(self):
        """测试超出范围年份"""
        is_valid, message = validate_year("1900")
        self.assertFalse(is_valid)


class TestValidateCompanyName(unittest.TestCase):
    """公司名称验证测试"""

    def test_validate_company_name_valid(self):
        """测试有效公司名称"""
        is_valid, message = validate_company_name("测试公司")
        self.assertTrue(is_valid)

    def test_validate_company_name_empty(self):
        """测试空公司名称"""
        is_valid, message = validate_company_name("")
        self.assertFalse(is_valid)


class TestValidateCompanyCode(unittest.TestCase):
    """公司代码验证测试"""

    def test_validate_company_code_valid(self):
        """测试有效公司代码"""
        is_valid, message = validate_company_code("12345678")
        self.assertTrue(is_valid)

    def test_validate_company_code_invalid(self):
        """测试无效公司代码"""
        is_valid, message = validate_company_code("123")
        self.assertFalse(is_valid)


class TestValidatePercentage(unittest.TestCase):
    """百分比验证测试"""

    def test_validate_percentage_valid(self):
        """测试有效百分比"""
        is_valid, message = validate_percentage(50.0)
        self.assertTrue(is_valid)

    def test_validate_percentage_negative(self):
        """测试负数百分比"""
        is_valid, message = validate_percentage(-10.0)
        self.assertFalse(is_valid)

    def test_validate_percentage_over_100(self):
        """测试超过100的百分比"""
        is_valid, message = validate_percentage(150.0)
        self.assertFalse(is_valid)


class TestValidateScore(unittest.TestCase):
    """分数验证测试"""

    def test_validate_score_valid(self):
        """测试有效分数"""
        is_valid, message = validate_score(85.0)
        self.assertTrue(is_valid)

    def test_validate_score_negative(self):
        """测试负数分数"""
        is_valid, message = validate_score(-5.0)
        self.assertFalse(is_valid)


class TestValidateRatio(unittest.TestCase):
    """比率验证测试"""

    def test_validate_ratio_valid(self):
        """测试有效比率"""
        is_valid, message = validate_ratio(0.5)
        self.assertTrue(is_valid)

    def test_validate_ratio_invalid(self):
        """测试无效比率"""
        is_valid, message = validate_ratio(1.5)
        self.assertFalse(is_valid)


class TestValidateNonNegativeNumber(unittest.TestCase):
    """非负数验证测试"""

    def test_validate_non_negative_valid(self):
        """测试有效非负数"""
        is_valid, message = validate_non_negative_number(100)
        self.assertTrue(is_valid)

    def test_validate_non_negative_negative(self):
        """测试负数"""
        is_valid, message = validate_non_negative_number(-10)
        self.assertFalse(is_valid)


class TestValidatePositiveInt(unittest.TestCase):
    """正整数验证测试"""

    def test_validate_positive_int_valid(self):
        """测试有效正整数"""
        is_valid, message = validate_positive_int(10)
        self.assertTrue(is_valid)

    def test_validate_positive_int_zero(self):
        """测试零"""
        is_valid, message = validate_positive_int(0)
        self.assertFalse(is_valid)

    def test_validate_positive_int_negative(self):
        """测试负数"""
        is_valid, message = validate_positive_int(-5)
        self.assertFalse(is_valid)


class TestValidateEmissionsValue(unittest.TestCase):
    """排放值验证测试"""

    def test_validate_emissions_value_valid(self):
        """测试有效排放值"""
        is_valid, message = validate_emissions_value(50000.0)
        self.assertTrue(is_valid)

    def test_validate_emissions_value_negative(self):
        """测试负排放值"""
        is_valid, message = validate_emissions_value(-1000.0)
        self.assertFalse(is_valid)


class TestValidateCarbonIntensity(unittest.TestCase):
    """碳强度验证测试"""

    def test_validate_carbon_intensity_valid(self):
        """测试有效碳强度"""
        is_valid, message = validate_carbon_intensity(50.0)
        self.assertTrue(is_valid)

    def test_validate_carbon_intensity_invalid(self):
        """测试无效碳强度"""
        is_valid, message = validate_carbon_intensity(-10.0)
        self.assertFalse(is_valid)


class TestValidateWaterIntensity(unittest.TestCase):
    """水强度验证测试"""

    def test_validate_water_intensity_valid(self):
        """测试有效水强度"""
        is_valid, message = validate_water_intensity(100.0)
        self.assertTrue(is_valid)

    def test_validate_water_intensity_invalid(self):
        """测试无效水强度"""
        is_valid, message = validate_water_intensity(-5.0)
        self.assertFalse(is_valid)


class TestValidateTrainingHours(unittest.TestCase):
    """培训时长验证测试"""

    def test_validate_training_hours_valid(self):
        """测试有效培训时长"""
        is_valid, message = validate_training_hours(40.0)
        self.assertTrue(is_valid)

    def test_validate_training_hours_invalid(self):
        """测试无效培训时长"""
        is_valid, message = validate_training_hours(-10.0)
        self.assertFalse(is_valid)


class TestValidatePDF(unittest.TestCase):
    """PDF文件验证测试"""

    def test_validate_pdf_nonexistent(self):
        """测试不存在的PDF文件"""
        is_valid, message = validate_pdf("/nonexistent/file.pdf")
        self.assertFalse(is_valid)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestValidateYear))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateCompanyName))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateCompanyCode))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatePercentage))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateScore))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateRatio))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateNonNegativeNumber))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatePositiveInt))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateEmissionsValue))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateCarbonIntensity))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateWaterIntensity))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateTrainingHours))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatePDF))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
