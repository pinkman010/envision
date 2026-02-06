"""ESG核心模块

该模块包含ESG分析的核心数据模型和分析引擎。

主要组件:
    - ESGMetrics: ESG指标数据类
    - AnalysisResult: 分析结果类
    - BenchmarkData: 行业基准数据类
    - ESGAnalysisEngine: ESG分析引擎

常量:
    - DEFAULT_SCORE: 默认得分 (50.0)
    - GAP_THRESHOLD_HIGH: 高差距阈值 (15.0)
    - GAP_THRESHOLD_MEDIUM: 中差距阈值 (8.0)

使用示例:
    >>> from src.core import ESGMetrics, ESGAnalysisEngine
    >>> 
    >>> # 创建ESG指标
    >>> metrics = ESGMetrics(
    ...     company_name="示例公司",
    ...     year="2024",
    ...     renewable_energy_ratio=45.0,
    ...     female_ratio=40.0,
    ...     board_independence_ratio=60.0
    ... )
    >>> 
    >>> # 执行分析
    >>> engine = ESGAnalysisEngine()
    >>> result = engine.analyze(metrics)
    >>> print(f"总体得分: {result.overall_score}")
"""

from src.core.models import (
    ESGMetrics,
    AnalysisResult,
    BenchmarkData,
    DEFAULT_SCORE,
    GAP_THRESHOLD_HIGH,
    GAP_THRESHOLD_MEDIUM
)
from src.core.engine import ESGAnalysisEngine

__all__ = [
    "ESGMetrics",
    "AnalysisResult", 
    "BenchmarkData",
    "ESGAnalysisEngine",
    "DEFAULT_SCORE",
    "GAP_THRESHOLD_HIGH",
    "GAP_THRESHOLD_MEDIUM"
]

__version__ = "1.0.0"
