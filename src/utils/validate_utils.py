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
    
    # 移除 Markdown 代码块（支持多行和嵌套）
    markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    markdown_match = re.search(markdown_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if markdown_match:
        cleaned = markdown_match.group(1).strip()
    
    # 尝试直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # 移除常见的前缀文字，找到第一个 { 的位置
    json_start = cleaned.find('{')
    if json_start > 0:
        try:
            return json.loads(cleaned[json_start:])
        except json.JSONDecodeError:
            pass
    
    # 暴力提取最外层的大括号内容
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\})*)*\}'
    json_match = re.search(json_pattern, cleaned, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # 记录失败时的原始输出，便于调试
    log.error(f"[JSON_PARSE_FAILED] 无法解析的LLM输出: {llm_output[:1000]}")
    raise ValidationException("无法从LLM输出中提取有效JSON")
