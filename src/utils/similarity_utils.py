"""
文本相似度校验工具：Levenshtein算法，拦截幻觉内容
ESG合规核心工具：确保AI抽取内容100%还原原文
"""

from typing import Tuple

from src.core_config.settings import SIMILARITY_THRESHOLD


def calculate_similarity(str1: str, str2: str) -> float:
    """
    计算两个字符串的Levenshtein相似度（归一化到0-1）
    :param str1: 字符串1（原文片段）
    :param str2: 字符串2（AI抽取内容）
    :return: 相似度（0-1，1为完全相同）
    """
    if not str1 or not str2:
        return 0.0
    # 先去除两端空白，避免空白影响相似度
    str1_clean = str1.strip()
    str2_clean = str2.strip()
    
    try:
        import Levenshtein
        distance = Levenshtein.distance(str1_clean, str2_clean)
        max_length = max(len(str1_clean), len(str2_clean))
        return 1 - (distance / max_length) if max_length > 0 else 1.0
    except ImportError:
        # 如果没有安装python-Levenshtein，使用简单实现
        return _simple_similarity(str1_clean, str2_clean)


def _simple_similarity(str1: str, str2: str) -> float:
    """简单的相似度计算（备用方案）"""
    if not str1 or not str2:
        return 0.0
    # 使用集合计算Jaccard相似度
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
    校验AI抽取内容与原文对应片段的相似度
    :param original_text: 完整原文
    :param extracted_text: AI抽取内容
    :param char_start: AI标注的原文起始位置
    :param char_end: AI标注的原文结束位置
    :return: （是否通过校验, 相似度）
    """
    # 截取原文对应片段
    original_snippet = original_text[char_start:char_end]
    similarity = calculate_similarity(original_snippet, extracted_text)
    is_passed = similarity >= SIMILARITY_THRESHOLD
    return is_passed, similarity


def validate_similarity_by_line(
    original_text: str,
    extracted_text: str,
    line_number: int,
    context_lines: int = 2,
) -> Tuple[bool, float, str]:
    """
    基于行号校验AI抽取内容与原文的相似度
    
    在指定的行及其前后几行中搜索匹配的内容，返回最佳匹配的相似度。
    这比字符位置更可靠，因为LLM更擅长识别行号而非精确字符位置。
    
    :param original_text: 完整原文
    :param extracted_text: AI抽取内容
    :param line_number: AI标注的行号（从1开始）
    :param context_lines: 搜索的上下文行数（在指定行前后各搜索多少行）
    :return: （是否通过校验, 相似度, 匹配到的原文片段）
    """
    if not original_text or not extracted_text or line_number < 1:
        return False, 0.0, ""
    
    # 将原文按行分割
    lines = original_text.split('\n')
    total_lines = len(lines)
    
    # 计算搜索范围（考虑边界）
    search_start = max(0, line_number - 1 - context_lines)  # 转换为0索引
    search_end = min(total_lines, line_number + context_lines)
    
    # 在搜索范围内逐行计算相似度，找出最佳匹配
    best_similarity = 0.0
    best_match = ""
    
    for i in range(search_start, search_end):
        if i >= total_lines:
            break
        
        line_content = lines[i]
        # 计算当前行与抽取内容的相似度
        similarity = calculate_similarity(line_content, extracted_text)
        
        # 也尝试在当前行中搜索抽取内容（处理LLM只抽取了部分内容的情况）
        if extracted_text in line_content:
            # 如果抽取内容完全包含在某一行中，给予高相似度
            similarity = max(similarity, 0.95)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = line_content
    
    # 也尝试在整个文本中搜索（作为备选）
    if extracted_text in original_text:
        # 如果能在原文中找到完全匹配，至少给0.9的相似度
        best_similarity = max(best_similarity, 0.9)
        if not best_match:
            # 找到包含该内容的行
            for i, line in enumerate(lines):
                if extracted_text in line:
                    best_match = line
                    break
    
    is_passed = best_similarity >= SIMILARITY_THRESHOLD
    return is_passed, best_similarity, best_match
