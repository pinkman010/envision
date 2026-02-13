"""字段验证模块

提供各种字段验证功能，包括评分、公司代码、百分比等。
"""

import math
import re
from typing import Tuple, Union

# ============ 常量定义 ============

PERCENTAGE_MIN = 0.0
PERCENTAGE_MAX = 100.0

RATIO_MIN = 0.0
RATIO_MAX = 1.0

SCORE_MIN = 0.0
SCORE_MAX = 100.0


def validate_score(score: Union[int, float, str]) -> Tuple[bool, str]:
    """验证 ESG 评分的合法性

    检查给定的值是否为合法的 ESG 评分。
    合法评分范围：0-100 分

    Args:
        score: 评分值，可以是整数、浮点数或字符串

    Returns:
        (is_valid, message) 元组
    """
    try:
        score_float = float(score)
    except (ValueError, TypeError):
        return False, f"评分必须是有效的数字，收到: {score}"

    # 检查是否为有效数值（非 NaN, Inf）
    if math.isnan(score_float):
        return False, "评分不能为 NaN"

    if math.isinf(score_float):
        return False, "评分不能为无穷大"

    # 检查范围
    if score_float < SCORE_MIN:
        return False, f"评分不能小于 {SCORE_MIN}，收到: {score_float}"

    if score_float > SCORE_MAX:
        return False, f"评分不能大于 {SCORE_MAX}，收到: {score_float}"

    return True, "验证通过"


def validate_company_code(code: str) -> Tuple[bool, str]:
    """验证公司代码的合法性

    检查给定的字符串是否为合法的公司代码（股票代码）。
    支持 A 股（6位数字）、港股（数字/字母组合）等格式。

    Args:
        code: 公司代码字符串

    Returns:
        (is_valid, message) 元组
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


def validate_percentage(
    value: Union[int, float, str], field_name: str = "百分比"
) -> Tuple[bool, str]:
    """验证百分比值的合法性

    检查给定的值是否在 0-100 的百分比范围内。

    Args:
        value: 百分比值
        field_name: 字段名称

    Returns:
        (is_valid, message) 元组
    """
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

    Args:
        value: 比例值
        field_name: 字段名称

    Returns:
        (is_valid, message) 元组
    """
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

    Args:
        value: 整数值
        field_name: 字段名称

    Returns:
        (is_valid, message) 元组
    """
    try:
        value_int = int(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的整数，收到: {value}"

    if value_int <= 0:
        return False, f"{field_name}必须是正整数（大于0），收到: {value_int}"

    return True, "验证通过"


def validate_company_name(name: str, max_length: int = 100) -> Tuple[bool, str]:
    """验证公司名称的合法性

    检查给定的字符串是否为合法的公司名称。

    Args:
        name: 公司名称字符串
        max_length: 最大允许长度

    Returns:
        (is_valid, message) 元组
    """
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
    if re.search(r"[<>&\x00-\x08\x0b\x0c\x0e-\x1f]", name):
        return False, "公司名称包含非法字符"

    return True, "验证通过"
