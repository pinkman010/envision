"""数据校验工具模块

提供各种数据校验功能，用于验证文件类型、年份、评分等数据的合法性。
主要用于 ESG 报告处理场景。
"""

import math
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

# ============ 常量定义 ============

# 允许的 PDF MIME 类型
ALLOWED_PDF_MIME_TYPES = [
    "application/pdf",
    "application/x-pdf",
]

# 允许的文件扩展名
ALLOWED_PDF_EXTENSIONS = [".pdf"]

# 最大文件大小（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024

# 百分比字段的合理范围
PERCENTAGE_MIN = 0.0
PERCENTAGE_MAX = 100.0

# 比例字段的合理范围（0-1）
RATIO_MIN = 0.0
RATIO_MAX = 1.0

# 最小/最大年份
MIN_YEAR = 2000
MAX_YEAR_OFFSET = 1  # 当前年份 + 1


def validate_pdf(
    file_path: Union[str, Path], check_mime: bool = False, max_size: Optional[int] = None
) -> Tuple[bool, str]:
    """验证 PDF 文件的合法性

    检查文件是否为合法的 PDF 文件，包括文件存在性、扩展名、
    MIME 类型（可选）和文件大小检查。

    Args:
        file_path: 文件路径
        check_mime: 是否检查 MIME 类型，默认为 False
        max_size: 最大允许的文件大小（字节），默认 100MB

    Returns:
        一个元组 (is_valid, message)
        - is_valid: 验证是否通过
        - message: 验证结果信息，如果验证失败则为错误原因

    Example:
        >>> is_valid, msg = validate_pdf("report.pdf")
        >>> if not is_valid:
        ...     print(f"验证失败: {msg}")
    """
    path = Path(file_path)

    # 检查文件是否存在
    if not path.exists():
        return False, f"文件不存在: {file_path}"

    # 检查是否为文件
    if not path.is_file():
        return False, f"路径不是文件: {file_path}"

    # 检查文件扩展名
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_PDF_EXTENSIONS:
        return False, f"不支持的文件类型 '{suffix}'，仅支持 PDF 文件"

    # 检查文件大小
    size_limit = max_size or MAX_FILE_SIZE
    file_size = path.stat().st_size
    if file_size > size_limit:
        size_mb = size_limit / (1024 * 1024)
        return False, f"文件大小超过限制（最大 {size_mb:.1f}MB）"

    if file_size == 0:
        return False, "文件为空"

    # 检查 MIME 类型（如果启用）
    if check_mime:
        try:
            import magic

            mime = magic.from_file(str(path), mime=True)
            if mime not in ALLOWED_PDF_MIME_TYPES:
                return False, f"文件 MIME 类型不正确: {mime}"
        except ImportError:
            # python-magic 未安装，跳过 MIME 检查
            pass
        except Exception as e:
            return False, f"MIME 类型检查失败: {str(e)}"

    # 检查 PDF 文件头（魔术数字）
    try:
        with open(path, "rb") as f:
            header = f.read(4)
            # PDF 文件头应该是 %PDF
            if not header.startswith(b"%PDF"):
                return False, "文件不是有效的 PDF 格式"
    except Exception as e:
        return False, f"无法读取文件: {str(e)}"

    return True, "验证通过"


def validate_year(year: Union[int, str]) -> Tuple[bool, str]:
    """验证年份的合法性

    检查给定的值是否为合法的 ESG 报告年份。
    合法年份范围：2000 年至当前年份 + 1（允许次年度报告）

    Args:
        year: 年份值，可以是整数或字符串

    Returns:
        一个元组 (is_valid, message)
        - is_valid: 验证是否通过
        - message: 验证结果信息

    Example:
        >>> validate_year(2023)
        (True, "验证通过")
        >>> validate_year("2020")
        (True, "验证通过")
        >>> validate_year(1999)
        (False, "年份必须在 2000-2027 之间")
    """
    from datetime import datetime

    # 转换为整数
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        return False, f"年份必须是有效的数字，收到: {year}"

    # 定义合法年份范围
    MIN_YEAR = 2000
    MAX_YEAR = datetime.now().year + 1  # 允许次年度报告

    # 检查范围
    if year_int < MIN_YEAR:
        return False, f"年份必须大于等于 {MIN_YEAR}，收到: {year_int}"

    if year_int > MAX_YEAR:
        return False, f"年份必须小于等于 {MAX_YEAR}，收到: {year_int}"

    return True, "验证通过"


def validate_score(score: Union[int, float, str]) -> Tuple[bool, str]:
    """验证 ESG 评分的合法性

    检查给定的值是否为合法的 ESG 评分。
    合法评分范围：0-100 分

    Args:
        score: 评分值，可以是整数、浮点数或字符串

    Returns:
        一个元组 (is_valid, message)
        - is_valid: 验证是否通过
        - message: 验证结果信息

    Example:
        >>> validate_score(85.5)
        (True, "验证通过")
        >>> validate_score("90")
        (True, "验证通过")
        >>> validate_score(150)
        (False, "评分必须在 0-100 之间")
    """
    # 转换为浮点数
    try:
        score_float = float(score)
    except (ValueError, TypeError):
        return False, f"评分必须是有效的数字，收到: {score}"

    # 检查是否为有效数值（非 NaN, Inf）- 必须先检查，再检查范围
    import math

    if math.isnan(score_float):
        return False, "评分不能为 NaN"

    if math.isinf(score_float):
        return False, "评分不能为无穷大"

    # 检查范围
    MIN_SCORE = 0.0
    MAX_SCORE = 100.0

    if score_float < MIN_SCORE:
        return False, f"评分不能小于 {MIN_SCORE}，收到: {score_float}"

    if score_float > MAX_SCORE:
        return False, f"评分不能大于 {MAX_SCORE}，收到: {score_float}"

    return True, "验证通过"


def validate_company_code(code: str) -> Tuple[bool, str]:
    """验证公司代码的合法性

    检查给定的字符串是否为合法的公司代码（股票代码）。
    支持 A 股（6位数字）、港股（数字/字母组合）等格式。

    Args:
        code: 公司代码字符串

    Returns:
        一个元组 (is_valid, message)
        - is_valid: 验证是否通过
        - message: 验证结果信息

    Example:
        >>> validate_company_code("000001")
        (True, "验证通过")
        >>> validate_company_code("00700")
        (True, "验证通过")
    """
    if not code or not isinstance(code, str):
        return False, "公司代码不能为空"

    # 去除空白字符
    code = code.strip().upper()

    if len(code) < 4 or len(code) > 10:
        return False, "公司代码长度应在 4-10 个字符之间"

    # A 股：6位数字
    if re.match(r"^\d{6}$", code):
        return True, "验证通过"

    # 港股：1-5位数字
    if re.match(r"^\d{1,5}$", code):
        return True, "验证通过"

    # 其他格式：字母数字组合
    if re.match(r"^[A-Z0-9]{4,10}$", code):
        return True, "验证通过"

    return False, "公司代码格式不正确"


def validate_report_year_range(
    start_year: Union[int, str], end_year: Union[int, str]
) -> Tuple[bool, str]:
    """验证报告年份范围的合法性

    检查起始年份和结束年份是否构成合法的年份范围。

    Args:
        start_year: 起始年份
        end_year: 结束年份

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_report_year_range(2020, 2023)
        (True, "验证通过")
        >>> validate_report_year_range(2023, 2020)
        (False, "起始年份不能大于结束年份")
    """
    # 验证起始年份
    valid, msg = validate_year(start_year)
    if not valid:
        return False, f"起始年份无效: {msg}"
    start_int = int(start_year)

    # 验证结束年份
    valid, msg = validate_year(end_year)
    if not valid:
        return False, f"结束年份无效: {msg}"
    end_int = int(end_year)

    # 检查顺序
    if start_int > end_int:
        return False, "起始年份不能大于结束年份"

    # 检查范围跨度（最多 20 年）
    if end_int - start_int > 20:
        return False, "年份范围不能超过 20 年"

    return True, "验证通过"


def validate_percentage(
    value: Union[int, float, str], field_name: str = "百分比"
) -> Tuple[bool, str]:
    """验证百分比值的合法性

    检查给定的值是否在 0-100 的百分比范围内。
    适用于：可再生能源占比、能源效率、废物回收率、女性员工比例、
    独立董事比例、道德培训覆盖率、风机可利用率、电池回收率、电解效率等。

    Args:
        value: 百分比值，可以是整数、浮点数或字符串
        field_name: 字段名称，用于错误信息

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_percentage(85.5, "可再生能源占比")
        (True, "验证通过")
        >>> validate_percentage(150, "能源效率")
        (False, "能源效率必须在 0-100 之间，收到: 150")
    """
    # 转换为浮点数
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的数字，收到: {value}"

    # 检查是否为有效数值
    if math.isnan(value_float):
        return False, f"{field_name}不能为 NaN"

    if math.isinf(value_float):
        return False, f"{field_name}不能为无穷大"

    # 检查范围
    if value_float < PERCENTAGE_MIN:
        return False, f"{field_name}不能小于 {PERCENTAGE_MIN}，收到: {value_float}"

    if value_float > PERCENTAGE_MAX:
        return False, f"{field_name}不能大于 {PERCENTAGE_MAX}，收到: {value_float}"

    return True, "验证通过"


def validate_ratio(value: Union[int, float, str], field_name: str = "比例") -> Tuple[bool, str]:
    """验证比例值的合法性

    检查给定的值是否在 0-1 的比例范围内。
    适用于：各种比率字段（如 renewable_energy_ratio 存储为 0-1 而非 0-100 时）。

    Args:
        value: 比例值，可以是整数、浮点数或字符串
        field_name: 字段名称，用于错误信息

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_ratio(0.85, "可再生能源比例")
        (True, "验证通过")
        >>> validate_ratio(1.5, "女性员工比例")
        (False, "女性员工比例必须在 0-1 之间，收到: 1.5")
    """
    # 转换为浮点数
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的数字，收到: {value}"

    # 检查是否为有效数值
    if math.isnan(value_float):
        return False, f"{field_name}不能为 NaN"

    if math.isinf(value_float):
        return False, f"{field_name}不能为无穷大"

    # 检查范围
    if value_float < RATIO_MIN:
        return False, f"{field_name}不能小于 {RATIO_MIN}，收到: {value_float}"

    if value_float > RATIO_MAX:
        return False, f"{field_name}不能大于 {RATIO_MAX}，收到: {value_float}"

    return True, "验证通过"


def validate_positive_int(value: Union[int, str], field_name: str = "整数值") -> Tuple[bool, str]:
    """验证正整数的合法性

    检查给定的值是否为正整数（大于 0）。
    适用于：员工数量、安全事故数、电池循环寿命等。

    Args:
        value: 整数值，可以是整数或字符串
        field_name: 字段名称，用于错误信息

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_positive_int(1000, "员工数量")
        (True, "验证通过")
        >>> validate_positive_int(-5, "安全事故数")
        (False, "安全事故数必须是正整数，收到: -5")
        >>> validate_positive_int(0, "电池循环寿命")
        (False, "电池循环寿命必须是正整数，收到: 0")
    """
    # 转换为整数
    try:
        value_int = int(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的整数，收到: {value}"

    # 检查是否为正数
    if value_int <= 0:
        return False, f"{field_name}必须是正整数（大于0），收到: {value_int}"

    return True, "验证通过"


def validate_non_negative_number(
    value: Union[int, float, str], field_name: str = "数值"
) -> Tuple[bool, str]:
    """验证非负数值的合法性

    检查给定的值是否为非负数（大于等于 0）。
    适用于：碳排放量、用水量、社区投资金额、碳强度、水资源强度等。

    Args:
        value: 数值，可以是整数、浮点数或字符串
        field_name: 字段名称，用于错误信息

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_non_negative_number(100000, "碳排放量")
        (True, "验证通过")
        >>> validate_non_negative_number(-50, "用水量")
        (False, "用水量不能为负数，收到: -50")
    """
    # 转换为浮点数
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的数字，收到: {value}"

    # 检查是否为有效数值
    if math.isnan(value_float):
        return False, f"{field_name}不能为 NaN"

    if math.isinf(value_float):
        return False, f"{field_name}不能为无穷大"

    # 检查是否为非负数
    if value_float < 0:
        return False, f"{field_name}不能为负数，收到: {value_float}"

    return True, "验证通过"


def validate_company_name(name: str, max_length: int = 100) -> Tuple[bool, str]:
    """验证公司名称的合法性

    检查给定的字符串是否为合法的公司名称。

    Args:
        name: 公司名称字符串
        max_length: 最大允许长度，默认 100 个字符

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_company_name("远景能源有限公司")
        (True, "验证通过")
        >>> validate_company_name("")
        (False, "公司名称不能为空")
        >>> validate_company_name("A" * 101)
        (False, "公司名称长度不能超过 100 个字符")
    """
    # 检查是否为空
    if not name or not isinstance(name, str):
        return False, "公司名称不能为空"

    # 去除首尾空白
    name = name.strip()

    if not name:
        return False, "公司名称不能为空或仅包含空白字符"

    # 检查长度
    if len(name) > max_length:
        return False, f"公司名称长度不能超过 {max_length} 个字符，当前: {len(name)}"

    # 检查是否包含非法字符
    # 允许：中文、英文、数字、空格、常见标点符号
    if re.search(r"[<>&\x00-\x08\x0b\x0c\x0e-\x1f]", name):
        return False, "公司名称包含非法字符"

    return True, "验证通过"


def validate_emissions_value(
    value: Union[int, float, str], field_name: str = "排放量"
) -> Tuple[bool, str]:
    """验证碳排放量的合法性

    检查碳排放量值是否合法（非负）。

    Args:
        value: 排放量值，可以是整数、浮点数或字符串
        field_name: 字段名称，用于错误信息

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_emissions_value(50000, "范围1排放")
        (True, "验证通过")
        >>> validate_emissions_value(-100, "范围2排放")
        (False, "范围2排放不能为负数")
    """
    return validate_non_negative_number(value, field_name)


def validate_carbon_intensity(value: Union[int, float, str]) -> Tuple[bool, str]:
    """验证碳强度的合法性

    检查碳强度值（吨CO2e/万元营收）是否合法。

    Args:
        value: 碳强度值

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_carbon_intensity(0.5)
        (True, "验证通过")
        >>> validate_carbon_intensity(-1.0)
        (False, "碳强度不能为负数")
    """
    return validate_non_negative_number(value, "碳强度")


def validate_water_intensity(value: Union[int, float, str]) -> Tuple[bool, str]:
    """验证水资源强度的合法性

    检查水资源强度值（立方米/万元营收）是否合法。

    Args:
        value: 水资源强度值

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_water_intensity(10.0)
        (True, "验证通过")
        >>> validate_water_intensity(-5.0)
        (False, "水资源强度不能为负数")
    """
    return validate_non_negative_number(value, "水资源强度")


def validate_training_hours(value: Union[int, float, str]) -> Tuple[bool, str]:
    """验证培训时长的合法性

    检查人均培训时长是否合法（非负，且不超过合理上限）。

    Args:
        value: 培训时长（小时）

    Returns:
        一个元组 (is_valid, message)

    Example:
        >>> validate_training_hours(40)
        (True, "验证通过")
        >>> validate_training_hours(8760)  # 超过一年总小时数
        (False, "培训时长不合理，超过 8760 小时")
    """
    # 先验证是否为非负数
    valid, msg = validate_non_negative_number(value, "人均培训时长")
    if not valid:
        return valid, msg

    # 检查合理上限（一年最多 8760 小时）
    value_float = float(value)
    if value_float > 8760:  # 365 * 24
        return False, f"培训时长不合理，超过 8760 小时（一年总小时数），收到: {value_float}"

    return True, "验证通过"


def validate_esg_metrics(metrics) -> Tuple[bool, List[str]]:
    """验证 ESGMetrics 对象的完整性

    检查 ESGMetrics 对象的所有字段是否符合规范。

    Args:
        metrics: ESGMetrics 对象

    Returns:
        一个元组 (is_valid, errors)
        - is_valid: 验证是否通过
        - errors: 错误信息列表

    Example:
        >>> from src.esg.core.models import ESGMetrics
        >>> metrics = ESGMetrics(company_name="测试公司", year="2024")
        >>> is_valid, errors = validate_esg_metrics(metrics)
        >>> if not is_valid:
        ...     print(f"验证失败: {errors}")
    """
    errors: List[str] = []

    # 验证必填字段
    if not metrics.company_name:
        errors.append("公司名称不能为空")
    else:
        valid, msg = validate_company_name(metrics.company_name)
        if not valid:
            errors.append(f"公司名称无效: {msg}")

    if not metrics.year:
        errors.append("年份不能为空")
    else:
        valid, msg = validate_year(metrics.year)
        if not valid:
            errors.append(f"年份无效: {msg}")

    # 验证百分比字段（0-100）
    percentage_fields = {
        "renewable_energy_ratio": "可再生能源占比",
        "energy_efficiency": "能源效率",
        "waste_recycling_rate": "废物回收率",
        "female_ratio": "女性员工比例",
        "board_independence_ratio": "董事会独立董事比例",
        "ethics_training_coverage": "道德培训覆盖率",
        "turbine_availability": "风机可利用率",
        "battery_recycling_rate": "电池回收率",
        "electrolysis_efficiency": "电解效率",
    }

    for field_name, display_name in percentage_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_percentage(value, display_name)
            if not valid:
                errors.append(msg)

    # 验证 0-100 评分字段
    score_fields = {
        "biodiversity_impact_score": "生物多样性影响评分",
        "energy_storage_safety_score": "储能安全评分",
        "esg_report_quality": "ESG报告质量评分",
    }

    for field_name, display_name in score_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_score(value)
            if not valid:
                errors.append(f"{display_name}: {msg}")

    # 验证正整数字段
    positive_int_fields = {
        "employee_count": "员工数量",
        "battery_cycle_life": "电池循环寿命",
    }

    for field_name, display_name in positive_int_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_positive_int(value, display_name)
            if not valid:
                errors.append(msg)

    # 验证非负整数字段（安全事故数可以为0）
    if metrics.safety_incidents is not None:
        if metrics.safety_incidents < 0:
            errors.append("安全事故数不能为负数")

    # 验证排放量字段（非负）
    emissions_fields = {
        "carbon_emissions": "总碳排放量",
        "scope1_emissions": "范围1排放",
        "scope2_emissions_location": "范围2排放（位置法）",
        "scope2_emissions_market": "范围2排放（市场法）",
        "scope3_emissions": "范围3排放",
    }

    for field_name, display_name in emissions_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_emissions_value(value, display_name)
            if not valid:
                errors.append(msg)

    # 验证强度字段
    if metrics.carbon_intensity is not None:
        valid, msg = validate_carbon_intensity(metrics.carbon_intensity)
        if not valid:
            errors.append(msg)

    if metrics.water_intensity is not None:
        valid, msg = validate_water_intensity(metrics.water_intensity)
        if not valid:
            errors.append(msg)

    # 验证用水量（非负）
    if metrics.water_consumption is not None:
        valid, msg = validate_non_negative_number(metrics.water_consumption, "用水量")
        if not valid:
            errors.append(msg)

    # 验证社区投资金额（非负）
    if metrics.community_investment is not None:
        valid, msg = validate_non_negative_number(metrics.community_investment, "社区投资金额")
        if not valid:
            errors.append(msg)

    # 验证培训时长
    if metrics.training_hours is not None:
        valid, msg = validate_training_hours(metrics.training_hours)
        if not valid:
            errors.append(msg)

    return len(errors) == 0, errors
