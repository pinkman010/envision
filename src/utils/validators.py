"""数据校验工具模块

提供各种数据校验功能，用于验证文件类型、年份、评分等数据的合法性。
主要用于 ESG 报告处理场景。
"""

import re
from pathlib import Path
from typing import Optional, Union, Tuple


# 允许的 PDF MIME 类型
ALLOWED_PDF_MIME_TYPES = [
    "application/pdf",
    "application/x-pdf",
]

# 允许的文件扩展名
ALLOWED_PDF_EXTENSIONS = [".pdf"]

# 最大文件大小（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024


def validate_pdf(
    file_path: Union[str, Path],
    check_mime: bool = False,
    max_size: Optional[int] = None
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
    
    # 检查范围
    MIN_SCORE = 0.0
    MAX_SCORE = 100.0
    
    if score_float < MIN_SCORE:
        return False, f"评分不能小于 {MIN_SCORE}，收到: {score_float}"
    
    if score_float > MAX_SCORE:
        return False, f"评分不能大于 {MAX_SCORE}，收到: {score_float}"
    
    # 检查是否为有效数值（非 NaN, Inf）
    import math
    if math.isnan(score_float):
        return False, "评分不能为 NaN"
    
    if math.isinf(score_float):
        return False, "评分不能为无穷大"
    
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
    if re.match(r'^\d{6}$', code):
        return True, "验证通过"
    
    # 港股：1-5位数字
    if re.match(r'^\d{1,5}$', code):
        return True, "验证通过"
    
    # 其他格式：字母数字组合
    if re.match(r'^[A-Z0-9]{4,10}$', code):
        return True, "验证通过"
    
    return False, "公司代码格式不正确"


def validate_report_year_range(
    start_year: Union[int, str],
    end_year: Union[int, str]
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
