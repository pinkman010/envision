"""ESG增强功能模块

提供碳足迹计算、多语言支持、数据可视化等增强功能。
"""

from src.esg.extraction.carbon_footprint import (
    CarbonFootprintCalculator,
    EmissionScope,
    CarbonFootprintResult,
    calculate_carbon_intensity,
    estimate_scope3_emissions
)
from src.esg.extraction.multilingual import (
    MultilingualReportGenerator,
    Language,
    translate_report,
    generate_multilingual_report
)
from src.esg.config.standards import (
    StandardsManager,
    StandardType,
    ComplianceChecker,
    SASBStandards,
    TCFDStandards
)

__all__ = [
    # 碳足迹
    'CarbonFootprintCalculator',
    'EmissionScope',
    'CarbonFootprintResult',
    'calculate_carbon_intensity',
    'estimate_scope3_emissions',
    # 多语言
    'MultilingualReportGenerator',
    'Language',
    'translate_report',
    'generate_multilingual_report',
    # 标准
    'StandardsManager',
    'StandardType',
    'ComplianceChecker',
    'SASBStandards',
    'TCFDStandards',
]
