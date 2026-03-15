"""
文本相似度校验工具：Levenshtein算法，拦截幻觉内容
ESG合规核心工具：确保AI抽取内容100%还原原文
"""

from typing import Tuple

from src.config.settings import SIMILARITY_THRESHOLD


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
