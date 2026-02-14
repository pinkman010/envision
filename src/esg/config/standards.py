"""ISSB/GRI标准配置 - 纯配置文件

仅包含配置数据，业务逻辑类从core模块导入。

配置数据：
- ISSB S1/S2 披露条款
- GRI Standards 披露条款  
- 合规状态常量

业务类（从core导入）：
- ComplianceChecker: 合规检查器
- StandardsManager: 标准管理器
- SASBStandards: SASB标准
- TCFDStandards: TCFD标准
"""

from src.esg.core.compliance_checker import (
    # 配置数据
    DISCLOSURE_STANDARDS,
    ISSB_S1_CLAUSES,
    ISSB_S2_CLAUSES,
    GRI_STANDARDS_CLAUSES,
    COMPLIANCE_THRESHOLDS,
    EMISSIONS_QUALITY_THRESHOLDS,
    # 状态常量
    COMPLIANCE_STATUS_COMPLIANT,
    COMPLIANCE_STATUS_NON_COMPLIANT,
    COMPLIANCE_STATUS_PARTIAL,
    REQUIREMENT_MANDATORY,
    REQUIREMENT_RECOMMENDED,
    # 业务类
    ComplianceChecker,
    StandardsManager,
    SASBStandards,
    TCFDStandards,
    StandardType,
    StandardRequirement,
    StandardsComplianceCheckResult,
    ComplianceCheckResult,
)

__all__ = [
    # 配置数据
    "DISCLOSURE_STANDARDS",
    "ISSB_S1_CLAUSES",
    "ISSB_S2_CLAUSES",
    "GRI_STANDARDS_CLAUSES",
    "COMPLIANCE_THRESHOLDS",
    "EMISSIONS_QUALITY_THRESHOLDS",
    # 状态常量
    "COMPLIANCE_STATUS_COMPLIANT",
    "COMPLIANCE_STATUS_NON_COMPLIANT",
    "COMPLIANCE_STATUS_PARTIAL",
    "REQUIREMENT_MANDATORY",
    "REQUIREMENT_RECOMMENDED",
    # 业务类
    "ComplianceChecker",
    "StandardsManager",
    "SASBStandards",
    "TCFDStandards",
    "StandardType",
    "StandardRequirement",
    "StandardsComplianceCheckResult",
    "ComplianceCheckResult",
]
