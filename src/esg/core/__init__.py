"""ESG核心模块

该模块包含ESG分析的核心数据模型和分析引擎。

主要组件:
    - ESGMetrics: ESG指标数据类
    - AnalysisResult: 分析结果类
    - BenchmarkData: 行业基准数据类
    - ScoreCalculator: 评分计算器

常量:
    - DEFAULT_SCORE: 默认得分 (50.0)
    - GAP_THRESHOLD_HIGH: 高差距阈值 (15.0)
    - GAP_THRESHOLD_MEDIUM: 中差距阈值 (8.0)
    - CARBON_INTENSITY_BENCHMARKS: 按行业细分的碳强度基准

子模块:
    - models: 数据模型（ESGMetrics, BenchmarkData, AnalysisResult）
    - scoring: 评分计算器

Version: 1.4.1
"""

# 先导入constants，避免循环依赖
from src.esg.core.constants import (
    CARBON_INTENSITY_BENCHMARK_HIGH,
    CARBON_INTENSITY_BENCHMARK_LOW,
    CARBON_INTENSITY_BENCHMARKS,
    WATER_INTENSITY_BENCHMARK_HIGH,
    WATER_INTENSITY_BENCHMARK_LOW,
)
from src.esg.core.models import (
    DEFAULT_SCORE,
    GAP_THRESHOLD_HIGH,
    GAP_THRESHOLD_MEDIUM,
    AnalysisResult,
    BenchmarkData,
    ESGMetrics,
)
from src.esg.core.scoring import (
    ScoreCalculator,
    calculate_carbon_intensity_score,
    get_score_calculator,
)

__all__ = [
    # 核心类
    "ESGMetrics",
    "AnalysisResult",
    "BenchmarkData",
    "ScoreCalculator",
    # 常量
    "DEFAULT_SCORE",
    "GAP_THRESHOLD_HIGH",
    "GAP_THRESHOLD_MEDIUM",
    "CARBON_INTENSITY_BENCHMARK_HIGH",
    "CARBON_INTENSITY_BENCHMARK_LOW",
    "CARBON_INTENSITY_BENCHMARKS",
    "WATER_INTENSITY_BENCHMARK_HIGH",
    "WATER_INTENSITY_BENCHMARK_LOW",
    # 函数
    "get_score_calculator",
    "calculate_carbon_intensity_score",
]

__version__ = "1.4.1"
