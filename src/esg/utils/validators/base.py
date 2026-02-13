"""基础验证模块

提供文件验证和年份验证功能。
"""

import math
import re
from pathlib import Path
from typing import Tuple, Union

# ============ 常量定义 ============

ALLOWED_PDF_MIME_TYPES = [
    "application/pdf",
    "application/x-pdf",
]

ALLOWED_PDF_EXTENSIONS = [".pdf"]

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

MIN_YEAR = 2000


def validate_pdf(
    file_path: Union[str, Path], check_mime: bool = False, max_size: int = MAX_FILE_SIZE
) -> Tuple[bool, str]:
    """验证 PDF 文件的合法性

    检查文件是否为合法的 PDF 文件，包括文件存在性、扩展名、
    MIME 类型（可选）和文件大小检查。

    Args:
        file_path: 文件路径
        check_mime: 是否检查 MIME 类型，默认为 False
        max_size: 最大允许的文件大小（字节），默认 100MB

    Returns:
        (is_valid, message) 元组
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
    file_size = path.stat().st_size
    if file_size > max_size:
        size_mb = max_size / (1024 * 1024)
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
            pass
        except Exception as e:
            return False, f"MIME 类型检查失败: {str(e)}"

    # 检查 PDF 文件头（魔术数字）
    try:
        with open(path, "rb") as f:
            header = f.read(4)
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
        (is_valid, message) 元组
    """
    from datetime import datetime

    # 转换为整数
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        return False, f"年份必须是有效的数字，收到: {year}"

    # 定义合法年份范围
    max_year = datetime.now().year + 1

    # 检查范围
    if year_int < MIN_YEAR:
        return False, f"年份必须大于等于 {MIN_YEAR}，收到: {year_int}"

    if year_int > max_year:
        return False, f"年份必须小于等于 {max_year}，收到: {year_int}"

    return True, "验证通过"


def validate_report_year_range(
    start_year: Union[int, str], end_year: Union[int, str]
) -> Tuple[bool, str]:
    """验证报告年份范围的合法性

    检查起始年份和结束年份是否构成合法的年份范围。

    Args:
        start_year: 起始年份
        end_year: 结束年份

    Returns:
        (is_valid, message) 元组
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
