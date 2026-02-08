"""ESG智能分析框架主包

基于AI的新能源行业ESG披露与沟通智能分析框架。

Example:
    >>> from src.esg.core import ESGMetrics
    >>> from src.esg.extraction import PDFExtractor
    >>> from src.esg.analysis import GapAnalyzer
"""

__version__ = "1.2.0"
__author__ = "ESG智能分析团队"

# 核心组件
from src.esg.core.models import ESGMetrics, AnalysisResult
from src.esg.core.engine import ESGAnalysisEngine

# 提取器
from src.esg.extraction.pdf_extractor import PDFExtractor
from src.esg.extraction.metric_extractor import MetricExtractor

# 分析器
from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.analysis.strategy_generator import StrategyGenerator

# 融合引擎
from src.esg.fusion.ahp import AHPFusionEngine

# 报告生成
from src.esg.completion.report_generator import ReportGenerator

__all__ = [
    "ESGMetrics",
    "AnalysisResult",
    "ESGAnalysisEngine",
    "PDFExtractor",
    "MetricExtractor",
    "GapAnalyzer",
    "StrategyGenerator",
    "AHPFusionEngine",
    "ReportGenerator",
]
