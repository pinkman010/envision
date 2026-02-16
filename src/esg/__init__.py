"""ESG智能分析框架主包

基于AI的新能源行业ESG披露与沟通智能分析框架。

Example:
    >>> from src.esg.core import ESGMetrics
    >>> from src.esg.extraction import PDFExtractor
    >>> from src.esg.analysis import GapAnalyzer

Version: 1.4.1
"""

__version__ = "1.4.1"
__author__ = "ESG智能分析团队"

# 注意：避免在此文件进行包级别的深度导入，以防止循环导入问题
# 如需导入具体类，请直接从对应模块导入，如：
# from src.esg.analysis.gap_analyzer import GapAnalyzer
# from src.esg.core.models import ESGMetrics
__all__ = []
