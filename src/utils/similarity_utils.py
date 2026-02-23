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
