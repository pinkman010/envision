"""ESG增强功能模块

提供多语言支持、数据可视化等增强功能。
"""

from src.esg.config.standards import (
    ComplianceChecker,
    SASBStandards,
    StandardsManager,
    StandardType,
    TCFDStandards,
)
from src.esg.extraction.multilingual import (
    Language,
    MultilingualReportGenerator,
    generate_multilingual_report,
    translate_report,
)

__all__ = [
    # 多语言
    "MultilingualReportGenerator",
    "Language",
    "translate_report",
    "generate_multilingual_report",
    # 标准
    "StandardsManager",
    "StandardType",
    "ComplianceChecker",
    "SASBStandards",
    "TCFDStandards",
]
