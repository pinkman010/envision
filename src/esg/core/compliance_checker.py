"""合规检查器

实现简化的国际标准合规检查功能。
只保留GRI和ISSB核心条款，返回简化的合规状态（合规/不合规/部分合规）。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.esg.core.models import ESGMetrics

# 合规状态常量
COMPLIANCE_STATUS_COMPLIANT = "合规"
COMPLIANCE_STATUS_NON_COMPLIANT = "不合规"
COMPLIANCE_STATUS_PARTIAL = "部分合规"


class ComplianceStatus(Enum):
    """合规状态"""

    COMPLIANT = "合规"
    NON_COMPLIANT = "不合规"
    PARTIAL = "部分合规"


# 只保留GRI和ISSB核心条款（简化版）
# ISSB S1 - 可持续发展相关财务信息披露（核心4条）
ISSB_S1_CLAUSES = [
    {
        "standard_id": "ISSB-S1-01",
        "clause_name": "治理",
        "check_items": ["治理架构描述", "管理角色指定"],
    },
    {
        "standard_id": "ISSB-S1-02",
        "clause_name": "战略整合",
        "check_items": ["战略描述", "商业模式影响"],
    },
    {
        "standard_id": "ISSB-S1-03",
        "clause_name": "风险管理",
        "check_items": ["风险识别流程", "风险评估方法"],
    },
    {
        "standard_id": "ISSB-S1-04",
        "clause_name": "指标与目标",
        "check_items": ["定量指标披露", "目标设定"],
    },
]

# ISSB S2 - 气候相关披露（核心5条）
ISSB_S2_CLAUSES = [
    {
        "standard_id": "ISSB-S2-01",
        "clause_name": "气候治理",
        "check_items": ["气候治理架构", "董事会气候监督"],
    },
    {
        "standard_id": "ISSB-S2-02",
        "clause_name": "气候战略",
        "check_items": ["气候风险描述", "气候机遇识别"],
    },
    {
        "standard_id": "ISSB-S2-03",
        "clause_name": "范围1+2排放",
        "check_items": ["范围1排放数据", "范围2排放数据"],
    },
    {
        "standard_id": "ISSB-S2-04",
        "clause_name": "范围3排放",
        "check_items": ["范围3排放数据"],
    },
    {
        "standard_id": "ISSB-S2-05",
        "clause_name": "能源使用披露",
        "check_items": ["总能耗数据", "可再生能源占比"],
    },
]

# GRI Standards - 核心6条
GRI_STANDARDS_CLAUSES = [
    {
        "standard_id": "GRI-2-01",
        "clause_name": "组织概况",
        "check_items": ["组织规模", "运营地点"],
    },
    {
        "standard_id": "GRI-2-02",
        "clause_name": "可持续发展报告披露",
        "check_items": ["报告周期", "报告边界"],
    },
    {
        "standard_id": "GRI-305-01",
        "clause_name": "直接温室气体排放(范围1)",
        "check_items": ["范围1排放数据"],
    },
    {
        "standard_id": "GRI-302-01",
        "clause_name": "组织内部的能源消耗",
        "check_items": ["能源消耗总量", "可再生能源用量"],
    },
    {
        "standard_id": "GRI-401-01",
        "clause_name": "员工雇佣",
        "check_items": ["员工总数", "按性别分类"],
    },
    {
        "standard_id": "GRI-404-01",
        "clause_name": "员工培训",
        "check_items": ["人均培训时长"],
    },
]

# 合并所有披露标准
DISCLOSURE_STANDARDS = {
    "ISSB-S1": {
        "name": "ISSB S1 - 可持续发展相关财务信息披露",
        "clauses": ISSB_S1_CLAUSES,
    },
    "ISSB-S2": {
        "name": "ISSB S2 - 气候相关披露",
        "clauses": ISSB_S2_CLAUSES,
    },
    "GRI": {
        "name": "GRI Standards",
        "clauses": GRI_STANDARDS_CLAUSES,
    },
}


@dataclass
class ComplianceCheckResult:
    """单个条款合规检查结果"""

    standard_id: str
    clause_name: str
    status: ComplianceStatus
    score: float
    passed_items: List[str]
    failed_items: List[str]


class ComplianceChecker:
    """ESG国际标准合规检查器（简化版）

    只保留GRI和ISSB核心条款。
    简化后功能：检查指标是否满足核心标准条款，返回合规状态。
    """

    # 合规检查阈值
    _COMPLIANT_THRESHOLD = 80.0
    _PARTIAL_THRESHOLD = 40.0

    def __init__(self):
        self.standards = DISCLOSURE_STANDARDS

        # 字段映射
        self._field_mapping = {
            "范围1排放数据": "scope1_emissions",
            "范围2排放数据": "scope2_emissions_location",
            "范围3排放数据": "scope3_emissions",
            "可再生能源占比": "renewable_energy_ratio",
            "总能耗数据": "energy_efficiency",
            "能源消耗总量": "energy_efficiency",
            "可再生能源用量": "renewable_energy_ratio",
            "员工总数": "employee_count",
            "按性别分类": "female_ratio",
            "人均培训时长": "training_hours",
            "组织规模": "employee_count",
            "运营地点": "esg_report_quality",
            "治理架构描述": "board_independence_ratio",
            "管理角色指定": "board_independence_ratio",
            "战略描述": "esg_report_quality",
            "商业模式影响": "esg_report_quality",
            "风险识别流程": "esg_report_quality",
            "风险评估方法": "esg_report_quality",
            "定量指标披露": "esg_report_quality",
            "目标设定": "esg_report_quality",
            "气候治理架构": "board_independence_ratio",
            "董事会气候监督": "board_independence_ratio",
            "气候风险描述": "esg_report_quality",
            "气候机遇识别": "esg_report_quality",
            "报告周期": "esg_report_quality",
            "报告边界": "esg_report_quality",
        }

    def check_compliance(self, metrics: ESGMetrics) -> Dict[str, ComplianceCheckResult]:
        """检查ESG指标的合规性

        Args:
            metrics: ESG指标数据

        Returns:
            合规检查结果字典
        """
        results = {}

        for standard_key, standard_config in self.standards.items():
            for clause in standard_config.get("clauses", []):
                standard_id = clause["standard_id"]
                check_items = clause.get("check_items", [])

                passed_items = []
                failed_items = []

                for item in check_items:
                    if self._check_item(metrics, item):
                        passed_items.append(item)
                    else:
                        failed_items.append(item)

                # 计算得分
                total_items = len(check_items)
                score = (len(passed_items) / total_items * 100) if total_items > 0 else 0.0

                # 确定状态
                status = self._calculate_status(score)

                results[standard_id] = ComplianceCheckResult(
                    standard_id=standard_id,
                    clause_name=clause.get("clause_name", ""),
                    status=status,
                    score=round(score, 1),
                    passed_items=passed_items,
                    failed_items=failed_items,
                )

        return results

    def _check_item(self, metrics: ESGMetrics, item: str) -> bool:
        """检查单个检查项"""
        field_name = self._field_mapping.get(item)
        if not field_name:
            # 无法映射的检查项，默认通过
            return True

        value = getattr(metrics, field_name, None)
        if value is None:
            return False

        if isinstance(value, (int, float)):
            return value > 0

        return bool(value)

    def _calculate_status(self, score: float) -> ComplianceStatus:
        """根据得分返回合规状态"""
        if score >= self._COMPLIANT_THRESHOLD:
            return ComplianceStatus.COMPLIANT
        elif score >= self._PARTIAL_THRESHOLD:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT

    def get_compliance_summary(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """获取合规性汇总

        Args:
            metrics: ESG指标数据

        Returns:
            合规性汇总字典
        """
        results = self.check_compliance(metrics)

        total = len(results)
        compliant = sum(1 for r in results.values() if r.status == ComplianceStatus.COMPLIANT)
        partial = sum(1 for r in results.values() if r.status == ComplianceStatus.PARTIAL)
        non_compliant = sum(
            1 for r in results.values() if r.status == ComplianceStatus.NON_COMPLIANT
        )

        # 计算合规率
        compliance_rate = (compliant / total * 100) if total > 0 else 0.0

        # 按标准分组统计
        standards_summary = {}
        for standard_key, standard_config in self.standards.items():
            standard_clauses = [c["standard_id"] for c in standard_config.get("clauses", [])]
            standard_results = {k: v for k, v in results.items() if k in standard_clauses}

            if standard_results:
                standards_summary[standard_key] = {
                    "name": standard_config.get("name", ""),
                    "total": len(standard_results),
                    "compliant": sum(
                        1
                        for r in standard_results.values()
                        if r.status == ComplianceStatus.COMPLIANT
                    ),
                    "partial": sum(
                        1 for r in standard_results.values() if r.status == ComplianceStatus.PARTIAL
                    ),
                    "non_compliant": sum(
                        1
                        for r in standard_results.values()
                        if r.status == ComplianceStatus.NON_COMPLIANT
                    ),
                }

        return {
            "compliance_rate": round(compliance_rate, 1),
            "total_clauses": total,
            "compliant_count": compliant,
            "partial_count": partial,
            "non_compliant_count": non_compliant,
            "standards_summary": standards_summary,
            "results": results,
        }

    def check_indicator_compliance(
        self, metrics: ESGMetrics, indicator_id: str
    ) -> ComplianceStatus:
        """检查单个指标是否符合核心标准

        Args:
            metrics: ESG指标数据
            indicator_id: 指标ID

        Returns:
            合规状态
        """
        # 定义指标与标准的映射
        indicator_standards = {
            "carbon_emissions": ["ISSB-S2-03", "GRI-305-01"],
            "renewable_energy_ratio": ["ISSB-S2-05", "GRI-302-01"],
            "employee_count": ["GRI-401-01"],
            "female_ratio": ["GRI-401-01"],
            "training_hours": ["GRI-404-01"],
            "board_independence_ratio": ["ISSB-S1-01", "ISSB-S2-01"],
        }

        relevant_standards = indicator_standards.get(indicator_id, [])
        if not relevant_standards:
            return ComplianceStatus.PARTIAL

        results = self.check_compliance(metrics)

        # 如果所有相关标准都合规，则返回合规
        compliant_count = sum(
            1
            for sid in relevant_standards
            if sid in results and results[sid].status == ComplianceStatus.COMPLIANT
        )

        if compliant_count == len(relevant_standards):
            return ComplianceStatus.COMPLIANT
        elif compliant_count > 0:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT
