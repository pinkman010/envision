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
    :raises ValidationException: 格式错误时抛出
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationException(f"JSON格式错误: {str(e)}", original_exception=e) from e


def validate_extraction_result(result: dict[str, Any]) -> bool:
    """
    校验信息抽取结果的完整性。
    返回 True 表示有实质内容可做后续相似度校验；
    返回 False 表示该字段在原文中未找到（extracted_content 为空），属合法状态，跳过相似度校验。
    :param result: 抽取结果字典
    :raises ValidationException: 结构性缺失时抛出（field_name 缺失等不可恢复错误）
    """
    # field_name 必须存在且非空，否则是结构性错误
    if "field_name" not in result or not result["field_name"]:
        raise ValidationException("抽取结果缺少必填字段: field_name")

    # extracted_content 为空字符串 = LLM 遵守 Prompt 约定，报告该字段原文中不存在，合法
    extracted_content = result.get("extracted_content", None)
    if extracted_content is None:
        raise ValidationException(f"抽取结果缺少字段: extracted_content (field={result['field_name']})")
    if extracted_content == "" or (isinstance(extracted_content, str) and extracted_content.strip() == ""):
        return False  # 合法的"未找到"状态，调用方跳过相似度校验

    # 有内容时，检查是否有行号或字符位置锚点
    has_line_number = "line_number" in result and result["line_number"] is not None
    has_char_anchor = "char_start" in result and "char_end" in result
    
    if not has_line_number and not has_char_anchor:
        raise ValidationException(f"抽取结果有内容但缺少位置锚点（行号或字符位置）(field={result['field_name']})")
    
    # 如果提供了行号，校验行号合法性
    if has_line_number:
        line_number = result["line_number"]
        if not isinstance(line_number, int) or line_number < 1:
            raise ValidationException(f"行号必须为正整数 (field={result['field_name']}, line_number={line_number})")
    
    # 如果提供了字符位置，校验字符位置合法性
    if has_char_anchor:
        char_start = result["char_start"]
        char_end = result["char_end"]
        if not isinstance(char_start, int) or not isinstance(char_end, int):
            raise ValidationException(f"字符锚点必须为整数 (field={result['field_name']})")
        if char_start < 0 or char_end <= char_start:
            raise ValidationException(f"字符锚点位置不合法 (field={result['field_name']})")

    return True  # 有内容，且锚点合法，需要做相似度校验


def validate_file_suffix(file_path: Path, allowed_suffixes: List[str]) -> None:
    """校验文件后缀是否在允许列表内"""
    if file_path.suffix.lower() not in allowed_suffixes:
        raise ValidationException(f"文件格式不允许，仅支持: {', '.join(allowed_suffixes)}")


# 获取模块级 logger
_logger = logging.getLogger(__name__)


def clean_and_parse_json(
    llm_output: str,
    logger: Optional[logging.Logger] = None,
) -> dict[str, Any]:
    """
    清洗并解析 LLM 输出的 JSON（防御性解析）
    
    处理以下情况：
    1. 空值或非字符串输入
    2. Markdown 代码块包裹 (```json ... ```)
    3. 前后有废话文字
    4. 多个 JSON 对象（取第一个）
    
    :param llm_output: LLM 原始输出字符串
    :param logger: 可选的日志记录器，不传则使用模块级 logger
    :return: 解析后的字典
    :raises ValidationException: 无法解析时抛出
    """
    log = logger or _logger
    
    # 1. 空值检查
    if not llm_output or not isinstance(llm_output, str):
        log.error(f"LLM返回无效内容: type={type(llm_output)}, value={repr(llm_output)}")
        raise ValidationException(
            "LLM返回内容为空或非字符串",
            context={"llm_output_type": str(type(llm_output)), "llm_output_repr": repr(llm_output)[:200]}
        )
    
    # 记录原始输出（截取前500字符避免日志过大）
    log.debug(f"[LLM_RAW_OUTPUT] {llm_output[:500]}{'...' if len(llm_output) > 500 else ''}")
    
    # 2. 预处理：去除首尾空白
    cleaned = llm_output.strip()
    
    # 3. 移除 Markdown 代码块标记
    # 匹配 ```json ... ``` 或 ``` ... ```
    markdown_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    markdown_match = re.match(markdown_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if markdown_match:
        cleaned = markdown_match.group(1).strip()
        log.debug(f"[MARKDOWN_REMOVED] 移除了 Markdown 代码块标记")
    
    # 4. 尝试直接解析
    try:
        result = json.loads(cleaned)
        log.debug(f"[JSON_PARSE_SUCCESS] 直接解析成功")
        return result
    except json.JSONDecodeError:
        log.debug(f"[JSON_PARSE_FAILED] 直接解析失败，尝试提取 JSON 片段")
    
    # 5. 暴力提取：正则匹配第一个 {...} 结构
    # 使用非贪婪匹配，找到第一个完整的 JSON 对象
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\})*)*\}'
    json_match = re.search(json_pattern, cleaned, re.DOTALL)
    
    if json_match:
        extracted = json_match.group(0)
        log.debug(f"[JSON_EXTRACTED] 提取到 JSON 片段: {extracted[:100]}...")
        try:
            result = json.loads(extracted)
            log.debug(f"[JSON_PARSE_SUCCESS] 提取后解析成功")
            return result
        except json.JSONDecodeError as e:
            log.error(f"[JSON_PARSE_FAILED] 提取后解析仍失败: {e}")
    
    # 6. 最终失败：记录完整原始输出并抛出异常
    log.error(f"[JSON_EXTRACTION_FAILED] 无法从 LLM 输出中提取有效 JSON")
    log.error(f"[LLM_FULL_OUTPUT] {llm_output}")
    
    raise ValidationException(
        "LLM未返回有效的JSON结构，原始输出已记录到日志",
        context={
            "llm_output_length": len(llm_output),
            "llm_output_preview": llm_output[:500] if len(llm_output) > 500 else llm_output
        }
    )
