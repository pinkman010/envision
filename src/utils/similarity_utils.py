"""
文本相似度校验工具：Levenshtein算法，拦截幻觉内容
ESG合规核心工具：确保AI抽取内容100%还原原文
"""

from typing import Tuple

from src.core_config.settings import SIMILARITY_THRESHOLD


def calculate_similarity(str1: str, str2: str) -> float:
    """
    计算两个字符串的Levenshtein相似度
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 相似度（0-1）
    """
    if not str1 or not str2:
        return 0.0
    
    str1_clean = str1.strip()
    str2_clean = str2.strip()
    
    try:
        import Levenshtein
        distance = Levenshtein.distance(str1_clean, str2_clean)
        max_length = max(len(str1_clean), len(str2_clean))
        return 1 - (distance / max_length) if max_length > 0 else 1.0
    except ImportError:
        return _simple_similarity(str1_clean, str2_clean)


def _simple_similarity(str1: str, str2: str) -> float:
    """简单的相似度计算（备用）"""
    if not str1 or not str2:
        return 0.0
    set1 = set(str1)
    set2 = set(str2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def validate_similarity(
    original_text: str,
    extracted_text: str,
    char_start: int,
    char_end: int,
) -> Tuple[bool, float]:
    """
    校验AI抽取内容与原文的相似度
    :param original_text: 完整原文
    :param extracted_text: AI抽取内容
    :param char_start: 起始位置
    :param char_end: 结束位置
    :return: （是否通过校验, 相似度）
    """
    original_snippet = original_text[char_start:char_end]
    similarity = calculate_similarity(original_snippet, extracted_text)
    is_passed = similarity >= SIMILARITY_THRESHOLD
    return is_passed, similarity


def validate_similarity_by_line(
    original_text: str,
    extracted_text: str,
    line_number: int,
    context_lines: int = 2,
) -> Tuple[bool, float, str, int, int]:
    """
    基于行号校验AI抽取内容与原文的相似度
    :param original_text: 完整原文
    :param extracted_text: AI抽取内容
    :param line_number: 行号（从1开始）
    :param context_lines: 上下文行数
    :return: （是否通过校验, 相似度, 匹配文本, 精确起始位置, 精确结束位置）
    """
    if not original_text or not extracted_text or line_number < 1:
        return False, 0.0, "", -1, -1
    
    lines = original_text.split('\n')
    total_lines = len(lines)
    
    search_start = max(0, line_number - 1 - context_lines)
    search_end = min(total_lines, line_number + context_lines)
    
    best_similarity = 0.0
    best_match = ""
    best_line_idx = -1
    
    for i in range(search_start, search_end):
        if i >= total_lines:
            break
        
        line_content = lines[i]
        similarity = calculate_similarity(line_content, extracted_text)
        
        if extracted_text in line_content:
            similarity = max(similarity, 0.95)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = line_content
            best_line_idx = i
    
    if extracted_text in original_text:
        best_similarity = max(best_similarity, 0.9)
        if not best_match:
            for i, line in enumerate(lines):
                if extracted_text in line:
                    best_match = line
                    best_line_idx = i
                    break
    
    exact_char_start = -1
    exact_char_end = -1
    
    if best_line_idx >= 0 and extracted_text in best_match:
        pos_in_line = best_match.find(extracted_text)
        if pos_in_line >= 0:
            line_start_char = sum(len(lines[i]) + 1 for i in range(best_line_idx))
            exact_char_start = line_start_char + pos_in_line
            exact_char_end = exact_char_start + len(extracted_text)
    elif extracted_text in original_text:
        exact_char_start = original_text.find(extracted_text)
        exact_char_end = exact_char_start + len(extracted_text)
    
    is_passed = best_similarity >= SIMILARITY_THRESHOLD
    return is_passed, best_similarity, best_match, exact_char_start, exact_char_end
