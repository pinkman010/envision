"""ESG核心模块

该模块包含ESG分析的核心数据模型和分析引擎。

主要组件:
    - ESGMetrics: ESG指标数据类
    - SBTiTarget: SBTi气候目标数据类
    - AnalysisResult: 分析结果类
    - BenchmarkData: 行业基准数据类
    - ESGAnalysisEngine: ESG分析引擎
    - ScoreCalculator: 评分计算器
    - SBTiTracker: SBTi目标追踪器
    - ClimateScenarioAnalyzer: TCFD气候情景分析器

常量:
    - DEFAULT_SCORE: 默认得分 (50.0)
    - GAP_THRESHOLD_HIGH: 高差距阈值 (15.0)
    - GAP_THRESHOLD_MEDIUM: 中差距阈值 (8.0)
    - CARBON_INTENSITY_BENCHMARKS: 按行业细分的碳强度基准

子模块:
    - models: 数据模型（ESGMetrics, SBTiTarget, BenchmarkData, AnalysisResult）
    - scoring: 评分计算器
    - sbti_tracker: SBTi目标追踪
    - climate_scenario: TCFD气候情景分析

使用示例:
    >>> from src.esg.core import ESGMetrics, ESGAnalysisEngine, SBTiTarget
    >>>
    >>> # 创建SBTi目标
    >>> sbti = SBTiTarget(
    ...     status="validated_wb2c",
    ...     baseline_year=2020,
    ...     target_year=2030,
    ...     baseline_emissions=100000,
    ...     reduction_rate=0.42,
    ...     pathway="wb2c"
    ... )
    >>>
    >>> # 创建ESG指标
    >>> metrics = ESGMetrics(
    ...     company_name="示例公司",
    ...     year="2024",
    ...     industry_sector="wind_power",
    ...     carbon_intensity=0.12,
    ...     sbti_target=sbti,
    ...     renewable_energy_ratio=45.0,
    ...     female_ratio=40.0,
    ...     board_independence_ratio=60.0
    ... )
    >>>
    >>> # 执行分析
    >>> engine = ESGAnalysisEngine()
    >>> result = engine.analyze(metrics)
    >>> print(f"总体得分: {result.overall_score}")
    >>>
    >>> # 气候情景分析
    >>> report = metrics.get_climate_scenario_analysis()
    >>> print(f"韧性评分范围: {report['resilience_assessment']['best_case']:.1f} - "
    ...       f"{report['resilience_assessment']['worst_case']:.1f}")
"""

# 先导入constants，避免循环依赖
from src.esg.core.constants import (
    CARBON_INTENSITY_BENCHMARK_HIGH,
    CARBON_INTENSITY_BENCHMARK_LOW,
    CARBON_INTENSITY_BENCHMARKS,
    SBTI_STATUS_SCORES,
    WATER_INTENSITY_BENCHMARK_HIGH,
    WATER_INTENSITY_BENCHMARK_LOW,
)
from src.esg.core.cdp_auto_filing import (
    CDPAutoFiler,
    CDPAnswer,
    CDPModule,
    CDPQuestion,
    CDPQuestionType,
    CDP_QUESTIONNAIRE,
    CDP_QUESTION_INDEX,
    CDP_SCORING_WEIGHTS,
    ClimateOpportunity,
    ClimateRisk,
    create_cdp_filer,
    quick_generate_cdp_filing,
)
from src.esg.core.scope3_emissions import (
    NEW_ENERGY_SECTOR_RELEVANCE,
    SCOPE3_CATEGORY_INFO,
    DataQuality,
    Scope3Calculator,
    Scope3Category,
    Scope3CategoryData,
    Scope3Inventory,
    create_empty_inventory,
    quick_calculate_scope3_summary,
)
from src.esg.core.engine import ESGAnalysisEngine
from src.esg.core.models import (
    DEFAULT_SCORE,
    GAP_THRESHOLD_HIGH,
    GAP_THRESHOLD_MEDIUM,
    AnalysisResult,
    BenchmarkData,
    ClimateGovernance,
    ESGMetrics,
    SBTiTarget,
    TCFDDisclosure,
)
from src.esg.core.scoring import (
    ScoreCalculator,
    calculate_carbon_intensity_score,
    calculate_sbti_score,
    get_score_calculator,
)
from src.esg.core.sbti_tracker import (
    SBTiTracker,
    create_sbti_tracker,
    quick_create_target,
)
from src.esg.core.climate_scenario import (
    ClimateScenario,
    ClimateScenarioAnalyzer,
    ScenarioImpact,
    ScenarioType,
    STANDARD_SCENARIOS,
    quick_analyze_scenarios,
)

__all__ = [
    # 核心类
    "ESGMetrics",
    "SBTiTarget",
    "AnalysisResult",
    "BenchmarkData",
    "ClimateGovernance",
    "TCFDDisclosure",
    "ESGAnalysisEngine",
    "ScoreCalculator",
    "SBTiTracker",
    # 范围3排放
    "Scope3Inventory",
    "Scope3Category",
    "Scope3CategoryData",
    "Scope3Calculator",
    "DataQuality",
    "SCOPE3_CATEGORY_INFO",
    "NEW_ENERGY_SECTOR_RELEVANCE",
    # CDP自动填报
    "CDPAutoFiler",
    "CDPAnswer",
    "CDPModule",
    "CDPQuestion",
    "CDPQuestionType",
    "CDP_QUESTIONNAIRE",
    "CDP_QUESTION_INDEX",
    "ClimateRisk",
    "ClimateOpportunity",
    # 常量
    "DEFAULT_SCORE",
    "GAP_THRESHOLD_HIGH",
    "GAP_THRESHOLD_MEDIUM",
    "CARBON_INTENSITY_BENCHMARK_HIGH",
    "CARBON_INTENSITY_BENCHMARK_LOW",
    "CARBON_INTENSITY_BENCHMARKS",
    "WATER_INTENSITY_BENCHMARK_HIGH",
    "WATER_INTENSITY_BENCHMARK_LOW",
    "SBTI_STATUS_SCORES",
    "CDP_SCORING_WEIGHTS",
    # 函数
    "get_score_calculator",
    "calculate_carbon_intensity_score",
    "calculate_sbti_score",
    "create_sbti_tracker",
    "quick_create_target",
    "create_empty_inventory",
    "quick_calculate_scope3_summary",
    "create_cdp_filer",
    "quick_generate_cdp_filing",
    # 气候情景分析
    "ClimateScenario",
    "ClimateScenarioAnalyzer",
    "ScenarioImpact",
    "ScenarioType",
    "STANDARD_SCENARIOS",
    "quick_analyze_scenarios",
]

__version__ = "1.1.0"
