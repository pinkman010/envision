"""ESG核心模块

该模块包含ESG分析的核心数据模型和分析引擎。

主要组件:
    - ESGMetrics: ESG指标数据类（内置评分计算逻辑）
    - AnalysisResult: 分析结果类
    - BenchmarkData: 行业基准数据类

常量:
    - DEFAULT_SCORE: 默认得分 (50.0)
    - GAP_THRESHOLD_HIGH: 高差距阈值 (15.0)
    - GAP_THRESHOLD_MEDIUM: 中差距阈值 (8.0)
    - CARBON_INTENSITY_BENCHMARKS: 按行业细分的碳强度基准

子模块:
    - models: 数据模型（ESGMetrics, BenchmarkData, AnalysisResult）

Version: 1.6.0 (移除ScoreCalculator，使用ESGMetrics内置评分)
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
    SCORE_MAX,
    AnalysisResult,
    BenchmarkData,
    ESGMetrics,
    _calculate_weighted_score,
)

__all__ = [
    # 核心类
    "ESGMetrics",
    "AnalysisResult",
    "BenchmarkData",
    # 常量
    "DEFAULT_SCORE",
    "GAP_THRESHOLD_HIGH",
    "GAP_THRESHOLD_MEDIUM",
    "SCORE_MAX",
    "CARBON_INTENSITY_BENCHMARK_HIGH",
    "CARBON_INTENSITY_BENCHMARK_LOW",
    "CARBON_INTENSITY_BENCHMARKS",
    "WATER_INTENSITY_BENCHMARK_HIGH",
    "WATER_INTENSITY_BENCHMARK_LOW",
    # 函数
    "_calculate_weighted_score",
]

__version__ = "1.6.0"
