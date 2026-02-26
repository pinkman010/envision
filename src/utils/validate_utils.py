"""
数据格式校验工具：硬规则强制校验，无AI参与
ESG合规核心工具：拦截格式错误、无锚点的内容
"""

import json
import re
import logging
from typing import Any, List, Optional
from pathlib import Path

from src.utils.exception_utils import ValidationException


def validate_json_format(json_str: str) -> dict[str, Any]:
    """
    校验JSON格式并解析
    :param json_str: JSON字符串
    :return: 解析后的字典
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationException(f"JSON格式错误: {str(e)}") from e


def validate_extraction_result(result: dict[str, Any]) -> bool:
    """
    校验信息抽取结果的完整性
    :param result: 抽取结果字典
    :return: True表示有内容需校验相似度，False表示字段未找到
    """
    if "field_name" not in result or not result["field_name"]:
        raise ValidationException("抽取结果缺少必填字段: field_name")

    extracted_content = result.get("extracted_content", None)
    if extracted_content is None:
        raise ValidationException(f"抽取结果缺少字段: extracted_content")
    if extracted_content == "" or (isinstance(extracted_content, str) and extracted_content.strip() == ""):
        return False

    has_line_number = "line_number" in result and result["line_number"] is not None
    has_char_anchor = "char_start" in result and "char_end" in result
    
    if not has_line_number and not has_char_anchor:
        raise ValidationException(f"抽取结果有内容但缺少位置锚点")
    
    if has_line_number:
        line_number = result["line_number"]
        if not isinstance(line_number, int) or line_number < 1:
            raise ValidationException(f"行号必须为正整数")
    
    if has_char_anchor:
        char_start = result["char_start"]
        char_end = result["char_end"]
        if not isinstance(char_start, int) or not isinstance(char_end, int):
            raise ValidationException(f"字符锚点必须为整数")
        if char_start < 0 or char_end <= char_start:
            raise ValidationException(f"字符锚点位置不合法")

    return True


def validate_file_suffix(file_path: Path, allowed_suffixes: List[str]) -> None:
    """校验文件后缀"""
    if file_path.suffix.lower() not in allowed_suffixes:
        raise ValidationException(f"文件格式不允许，仅支持: {', '.join(allowed_suffixes)}")


_logger = logging.getLogger(__name__)


def clean_and_parse_json(
    llm_output: str,
    logger: Optional[logging.Logger] = None,
) -> dict[str, Any]:
    """
    清洗并解析 LLM 输出的 JSON
    :param llm_output: LLM 原始输出
    :param logger: 可选的日志记录器
    :return: 解析后的字典
    """
    log = logger or _logger
    
    if not llm_output or not isinstance(llm_output, str):
        raise ValidationException("LLM返回内容为空或非字符串")
    
    log.debug(f"[LLM_RAW_OUTPUT] {llm_output[:500]}{'...' if len(llm_output) > 500 else ''}")
    
    cleaned = llm_output.strip()
    
    # 移除 Markdown 代码块
    markdown_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    markdown_match = re.match(markdown_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if markdown_match:
        cleaned = markdown_match.group(1).strip()
    
    # 尝试直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # 暴力提取JSON
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\})*)*\}'
    json_match = re.search(json_pattern, cleaned, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValidationException("无法从LLM输出中提取有效JSON")
