"""合规检查器

实现国际标准合规检查功能，支持ISSB S1/S2和GRI Standards的合规性检查。
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from src.core.models import ESGMetrics
from src.config import (
    DISCLOSURE_STANDARDS,
    REQUIREMENT_MANDATORY,
    COMPLIANCE_STATUS_COMPLIANT,
    COMPLIANCE_STATUS_NON_COMPLIANT,
    COMPLIANCE_STATUS_PARTIAL,
)


# 合规检查阈值配置
COMPLIANCE_THRESHOLDS = {
    # 碳排放相关阈值
    "carbon_emissions": {
        "min_absolute": 1000,        # 最小绝对排放量（吨CO2e）
        "max_intensity": 10.0,       # 最大碳强度（吨CO2e/万元营收）
    },
    # 可再生能源比例阈值
    "renewable_energy_ratio": {
        "min": 20.0,  # 至少20%使用可再生能源
    },
    # 董事会独立性阈值
    "board_independence": {
        "min_ratio": 0.3,  # 至少30%独立董事
    },
    # 培训覆盖率阈值
    "ethics_training": {
        "min_coverage": 80.0,  # 至少80%员工接受道德培训
    },
    # 废物回收率阈值
    "waste_recycling": {
        "min_rate": 50.0,  # 至少50%废物回收
    },
    # 性别多样性阈值
    "gender_diversity": {
        "min_female_ratio": 0.3,  # 至少30%女性员工
    },
}

# 排放数据质量阈值
EMISSIONS_QUALITY_THRESHOLDS = {
    "scope1_min": 100,       # 范围1最小披露值
    "scope2_min": 100,       # 范围2最小披露值
    "scope3_min": 500,       # 范围3最小披露值（通常较大）
    "intensity_max": 5.0,    # 合理碳强度上限
}


@dataclass
class ComplianceCheckResult:
    """单个条款合规检查结果"""
    standard_id: str
    clause_name: str
    requirement_type: str
    status: str
    score: float
    missing_items: List[str]
    description: str


class ComplianceChecker:
    """ESG国际标准合规检查器
    
    检查ESG指标数据是否符合ISSB S1/S2和GRI Standards等国际标准的要求。
    支持基于阈值的详细合规验证和碳排放范围分离检查。
    
    Attributes:
        standards: 披露标准配置字典
        thresholds: 合规检查阈值配置
        
    Example:
        >>> metrics = ESGMetrics(company_name="Test", year="2024", carbon_emissions=1000)
        >>> checker = ComplianceChecker()
        >>> result = checker.check_compliance(metrics)
        >>> print(checker.get_compliance_rate())
    """
    
    def __init__(self):
        """初始化合规检查器，加载披露标准配置"""
        self.standards = DISCLOSURE_STANDARDS
        self.thresholds = COMPLIANCE_THRESHOLDS
        
        # 字段映射：检查项 -> metrics字段名
        self._field_mapping = {
            # 碳排放相关
            "碳排放数据存在": "carbon_emissions",
            "范围1排放数据": "scope1_emissions",
            "范围2排放数据": "scope2_emissions",
            "范围3排放数据": "scope3_emissions",
            "范围1+2+3完整": "carbon_emissions",
            "碳强度数据": "carbon_intensity",
            # 能源相关
            "可再生能源占比": "renewable_energy_ratio",
            "总能耗数据": "energy_efficiency",
            "能源效率指标": "energy_efficiency",
            # 水资源
            "用水总量": "water_consumption",
            "水资源强度": "water_intensity",
            "水资源压力区": "water_consumption",
            # 废弃物
            "废弃物回收率": "waste_recycling_rate",
            "废弃物总量": "waste_recycling_rate",
            # 生物多样性
            "生物多样性影响": "biodiversity_impact_score",
            # 员工相关
            "员工总数": "employee_count",
            "按性别分类": "female_ratio",
            "人均培训时长": "training_hours",
            "培训覆盖率": "training_hours",
            # 安全
            "安全事故数": "safety_incidents",
            # 治理相关
            "董事会独立性": "board_independence_ratio",
            "治理架构描述": "board_independence_ratio",
            "董事会气候监督": "board_independence_ratio",
            "董事会监督机制": "board_independence_ratio",
            "管理角色指定": "board_independence_ratio",
            "管理层气候职责": "board_independence_ratio",
            "道德培训覆盖率": "ethics_training_coverage",
            # ESG报告
            "ESG报告质量": "esg_report_quality",
            "报告边界": "esg_report_quality",
            "定量指标披露": "esg_report_quality",
            "报告周期": "esg_report_quality",
            # 战略和风险管理
            "战略描述": "esg_report_quality",
            "战略整合": "esg_report_quality",
            "风险管理": "esg_report_quality",
            "风险识别流程": "esg_report_quality",
            "气候战略": "renewable_energy_ratio",
            "转型计划": "renewable_energy_ratio",
            # 社区投资
            "社区投资": "community_investment",
            "社区投资金额": "community_investment",
            # 新能源特色指标
            "风机可利用率": "turbine_availability",
            "电池循环寿命": "battery_cycle_life",
            "电池回收率": "battery_recycling_rate",
            "电解效率": "electrolysis_efficiency",
            "储能安全评分": "energy_storage_safety_score",
        }
        
        # 特殊检查项处理器
        self._special_checks: Dict[str, Callable[[ESGMetrics], bool]] = {
            "范围1排放数据": self._check_scope1_emissions,
            "范围2排放数据": self._check_scope2_emissions,
            "范围3排放数据": self._check_scope3_emissions,
            "范围1+2+3完整": self._check_complete_emissions,
            "可再生能源占比": self._check_renewable_energy,
            "董事会独立性": self._check_board_independence,
            "道德培训覆盖率": self._check_ethics_training,
            "废弃物回收率": self._check_waste_recycling,
            "按性别分类": self._check_gender_diversity,
            "碳强度数据": self._check_carbon_intensity,
        }
    
    def _check_scope1_emissions(self, metrics: ESGMetrics) -> bool:
        """检查范围1排放数据
        
        验证范围1排放是否存在且符合合理范围。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.scope1_emissions is None:
            # 回退检查carbon_emissions
            return metrics.carbon_emissions is not None and metrics.carbon_emissions > 0
        
        return metrics.scope1_emissions >= 0
    
    def _check_scope2_emissions(self, metrics: ESGMetrics) -> bool:
        """检查范围2排放数据
        
        验证范围2排放是否存在（位置法或市场法）。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        has_location = metrics.scope2_emissions_location is not None and metrics.scope2_emissions_location >= 0
        has_market = metrics.scope2_emissions_market is not None and metrics.scope2_emissions_market >= 0
        
        # 接受任一方法的数据
        return has_location or has_market
    
    def _check_scope3_emissions(self, metrics: ESGMetrics) -> bool:
        """检查范围3排放数据
        
        验证范围3排放是否存在。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.scope3_emissions is None:
            # 如果范围1+2存在，可部分接受
            has_scope1 = metrics.scope1_emissions is not None
            has_scope2 = metrics.scope2_emissions_location is not None or metrics.scope2_emissions_market is not None
            return has_scope1 and has_scope2
        
        return metrics.scope3_emissions >= 0
    
    def _check_complete_emissions(self, metrics: ESGMetrics) -> bool:
        """检查完整的范围1+2+3排放数据
        
        验证所有三个范围的排放数据是否完整。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        has_scope1 = self._check_scope1_emissions(metrics)
        has_scope2 = self._check_scope2_emissions(metrics)
        has_scope3 = metrics.scope3_emissions is not None and metrics.scope3_emissions >= 0
        
        # 完全合规：三个范围都有数据
        if has_scope1 and has_scope2 and has_scope3:
            return True
        
        # 部分接受：至少范围1+2有数据
        if has_scope1 and has_scope2:
            return True
        
        # 最低要求：carbon_emissions存在
        return metrics.carbon_emissions is not None and metrics.carbon_emissions > 0
    
    def _check_renewable_energy(self, metrics: ESGMetrics) -> bool:
        """检查可再生能源占比
        
        验证可再生能源比例是否存在且达到最低阈值。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.renewable_energy_ratio is None:
            return False
        
        # 检查是否达到最低阈值
        min_ratio = self.thresholds["renewable_energy_ratio"]["min"]
        return metrics.renewable_energy_ratio >= min_ratio
    
    def _check_board_independence(self, metrics: ESGMetrics) -> bool:
        """检查董事会独立性
        
        验证独立董事比例是否达到最低要求。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.board_independence_ratio is None:
            return False
        
        min_ratio = self.thresholds["board_independence"]["min_ratio"]
        return metrics.board_independence_ratio >= min_ratio * 100  # 转换为百分比
    
    def _check_ethics_training(self, metrics: ESGMetrics) -> bool:
        """检查道德培训覆盖率
        
        验证道德培训覆盖率是否达到最低要求。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.ethics_training_coverage is None:
            return False
        
        min_coverage = self.thresholds["ethics_training"]["min_coverage"]
        return metrics.ethics_training_coverage >= min_coverage
    
    def _check_waste_recycling(self, metrics: ESGMetrics) -> bool:
        """检查废弃物回收率
        
        验证废弃物回收率是否达到最低要求。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.waste_recycling_rate is None:
            return False
        
        min_rate = self.thresholds["waste_recycling"]["min_rate"]
        return metrics.waste_recycling_rate >= min_rate
    
    def _check_gender_diversity(self, metrics: ESGMetrics) -> bool:
        """检查性别多样性
        
        验证女性员工比例是否存在且合理。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.female_ratio is None:
            return False
        
        # 检查比例是否在合理范围内（1%-99%）
        return 0.01 <= metrics.female_ratio <= 0.99 or 1 <= metrics.female_ratio <= 99
    
    def _check_carbon_intensity(self, metrics: ESGMetrics) -> bool:
        """检查碳强度数据
        
        验证碳强度是否存在且在合理范围内。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            是否通过检查
        """
        if metrics.carbon_intensity is None:
            return False
        
        # 检查是否在合理范围内
        max_intensity = self.thresholds["carbon_emissions"]["max_intensity"]
        return 0 < metrics.carbon_intensity <= max_intensity * 10  # 允许一定弹性
    
    def check_compliance(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """检查ESG指标的合规性
        
        遍历所有标准条款，检查metrics对象中对应字段是否存在且有效。
        支持基于阈值的详细合规验证和碳排放范围分离检查。
        
        Args:
            metrics: ESG指标数据对象
            
        Returns:
            合规检查结果字典，结构为：
            {
                "standard_id": {
                    "status": "已合规"/"未合规"/"部分合规",
                    "score": float (0-100),
                    "missing_items": List[str],
                    "requirement_type": "强制"/"建议"
                }
            }
        """
        results = {}
        
        for standard_key, standard_config in self.standards.items():
            for clause in standard_config.get("clauses", []):
                standard_id = clause["standard_id"]
                check_items = clause.get("check_items", [])
                requirement_type = clause.get("requirement_type", REQUIREMENT_MANDATORY)
                
                # 检查每个检查项
                missing_items = []
                passed_items = 0
                
                for item in check_items:
                    if self._check_item(metrics, item):
                        passed_items += 1
                    else:
                        missing_items.append(item)
                
                # 计算得分
                total_items = len(check_items)
                score = (passed_items / total_items * 100) if total_items > 0 else 0.0
                
                # 确定状态
                if score >= 80:
                    status = COMPLIANCE_STATUS_COMPLIANT
                elif score >= 40:
                    status = COMPLIANCE_STATUS_PARTIAL
                else:
                    status = COMPLIANCE_STATUS_NON_COMPLIANT
                
                results[standard_id] = {
                    "status": status,
                    "score": round(score, 1),
                    "missing_items": missing_items,
                    "requirement_type": requirement_type,
                    "clause_name": clause.get("clause_name", ""),
                    "description": clause.get("description", ""),
                    "standard_name": standard_config.get("name", ""),
                }
        
        return results
    
    def _check_item(self, metrics: ESGMetrics, item: str) -> bool:
        """检查单个检查项
        
        支持特殊检查逻辑和基于阈值的验证。
        
        Args:
            metrics: ESG指标数据
            item: 检查项名称
            
        Returns:
            是否通过检查
        """
        # 优先使用特殊检查器
        if item in self._special_checks:
            return self._special_checks[item](metrics)
        
        # 获取对应的字段名
        field_name = self._field_mapping.get(item)
        if not field_name:
            # 无法映射的检查项，默认通过（依赖描述性披露）
            return True
        
        # 获取字段值
        value = getattr(metrics, field_name, None)
        
        # 检查值是否有效
        if value is None:
            return False
        
        # 数值型字段检查
        if isinstance(value, (int, float)):
            # 安全事故数量可以为0
            if field_name == "safety_incidents":
                return value >= 0
            # 其他数值必须大于0
            return value > 0
        
        # 其他类型（字符串等），非空即为有效
        return bool(value)
    
    def check_emissions_compliance(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """专门检查碳排放合规性
        
        分别检查范围1/2/3排放数据的合规状态。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            碳排放合规性详细结果
        """
        scope1_ok = self._check_scope1_emissions(metrics)
        scope2_ok = self._check_scope2_emissions(metrics)
        scope3_ok = self._check_scope3_emissions(metrics)
        intensity_ok = self._check_carbon_intensity(metrics)
        
        # 计算各范围得分
        scope1_score = 100 if scope1_ok else 0
        scope2_score = 100 if scope2_ok else 0
        scope3_score = 100 if scope3_ok else 50 if metrics.scope1_emissions and metrics.scope2_emissions_location else 0
        intensity_score = 100 if intensity_ok else 0
        
        # 计算总体排放合规得分
        scores = [scope1_score, scope2_score]
        if metrics.scope3_emissions is not None:
            scores.append(scope3_score)
        if metrics.carbon_intensity is not None:
            scores.append(intensity_score)
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # 确定总体状态
        if overall_score >= 80:
            overall_status = COMPLIANCE_STATUS_COMPLIANT
        elif overall_score >= 50:
            overall_status = COMPLIANCE_STATUS_PARTIAL
        else:
            overall_status = COMPLIANCE_STATUS_NON_COMPLIANT
        
        return {
            "overall_status": overall_status,
            "overall_score": round(overall_score, 1),
            "breakdown": {
                "scope1": {
                    "status": "已合规" if scope1_ok else "未合规",
                    "score": scope1_score,
                    "value": metrics.scope1_emissions if metrics.scope1_emissions is not None else metrics.carbon_emissions,
                    "requirement": "强制",
                },
                "scope2": {
                    "status": "已合规" if scope2_ok else "未合规",
                    "score": scope2_score,
                    "value_location": metrics.scope2_emissions_location,
                    "value_market": metrics.scope2_emissions_market,
                    "requirement": "强制",
                },
                "scope3": {
                    "status": "已合规" if scope3_ok else ("部分合规" if scope1_ok and scope2_ok else "未合规"),
                    "score": scope3_score,
                    "value": metrics.scope3_emissions,
                    "requirement": "建议",
                },
                "carbon_intensity": {
                    "status": "已合规" if intensity_ok else "未合规",
                    "score": intensity_score,
                    "value": metrics.carbon_intensity,
                    "requirement": "建议",
                },
            },
            "total_emissions": metrics.get_total_emissions(),
            "scope1_2_emissions": metrics.get_scope1_2_emissions(),
        }
    
    def get_compliance_rate(self, metrics: ESGMetrics) -> float:
        """计算合规率
        
        计算已合规强制条款数 / 总强制条款数
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            合规率 (0-1之间的浮点数)
        """
        results = self.check_compliance(metrics)
        
        mandatory_total = 0
        mandatory_compliant = 0
        
        for standard_id, result in results.items():
            if result.get("requirement_type") == REQUIREMENT_MANDATORY:
                mandatory_total += 1
                if result.get("status") == COMPLIANCE_STATUS_COMPLIANT:
                    mandatory_compliant += 1
        
        if mandatory_total == 0:
            return 0.0
        
        return round(mandatory_compliant / mandatory_total, 3)
    
    def get_compliance_summary(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """获取合规性汇总信息
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            合规性汇总字典
        """
        results = self.check_compliance(metrics)
        emissions_check = self.check_emissions_compliance(metrics)
        
        total_clauses = len(results)
        compliant_count = sum(1 for r in results.values() if r["status"] == COMPLIANCE_STATUS_COMPLIANT)
        partial_count = sum(1 for r in results.values() if r["status"] == COMPLIANCE_STATUS_PARTIAL)
        non_compliant_count = sum(1 for r in results.values() if r["status"] == COMPLIANCE_STATUS_NON_COMPLIANT)
        
        mandatory_total = sum(1 for r in results.values() if r["requirement_type"] == REQUIREMENT_MANDATORY)
        mandatory_compliant = sum(
            1 for r in results.values() 
            if r["requirement_type"] == REQUIREMENT_MANDATORY and r["status"] == COMPLIANCE_STATUS_COMPLIANT
        )
        
        # 按标准分组统计
        standards_summary = {}
        for standard_key, standard_config in self.standards.items():
            standard_clauses = [c["standard_id"] for c in standard_config.get("clauses", [])]
            standard_results = {k: v for k, v in results.items() if k in standard_clauses}
            
            if standard_results:
                standards_summary[standard_key] = {
                    "name": standard_config.get("name", ""),
                    "total": len(standard_results),
                    "compliant": sum(1 for r in standard_results.values() if r["status"] == COMPLIANCE_STATUS_COMPLIANT),
                    "partial": sum(1 for r in standard_results.values() if r["status"] == COMPLIANCE_STATUS_PARTIAL),
                    "non_compliant": sum(1 for r in standard_results.values() if r["status"] == COMPLIANCE_STATUS_NON_COMPLIANT),
                }
        
        return {
            "overall_rate": self.get_compliance_rate(metrics),
            "total_clauses": total_clauses,
            "compliant_count": compliant_count,
            "partial_count": partial_count,
            "non_compliant_count": non_compliant_count,
            "mandatory_total": mandatory_total,
            "mandatory_compliant": mandatory_compliant,
            "standards_summary": standards_summary,
            "emissions_compliance": emissions_check,
        }
    
    def get_non_compliant_items(self, metrics: ESGMetrics, requirement_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取未合规的条款列表
        
        Args:
            metrics: ESG指标数据
            requirement_type: 可选，筛选特定要求类型（"强制"或"建议"）
            
        Returns:
            未合规条款列表
        """
        results = self.check_compliance(metrics)
        non_compliant = []
        
        for standard_id, result in results.items():
            if result["status"] != COMPLIANCE_STATUS_COMPLIANT:
                if requirement_type is None or result.get("requirement_type") == requirement_type:
                    non_compliant.append({
                        "standard_id": standard_id,
                        "clause_name": result.get("clause_name", ""),
                        "requirement_type": result.get("requirement_type", ""),
                        "status": result.get("status", ""),
                        "missing_items": result.get("missing_items", []),
                        "description": result.get("description", ""),
                    })
        
        # 按要求类型排序：强制在前，建议在后
        priority = {"强制": 0, "建议": 1}
        non_compliant.sort(key=lambda x: priority.get(x["requirement_type"], 2))
        
        return non_compliant
    
    def get_compliance_gaps(self, metrics: ESGMetrics) -> Dict[str, List[str]]:
        """获取合规差距分析
        
        识别具体哪些指标未达到合规阈值。
        
        Args:
            metrics: ESG指标数据
            
        Returns:
            按维度分组的差距列表
        """
        gaps = {
            "environmental": [],
            "social": [],
            "governance": [],
        }
        
        # 环境维度检查
        if not self._check_scope1_emissions(metrics):
            gaps["environmental"].append("范围1排放数据缺失")
        if not self._check_scope2_emissions(metrics):
            gaps["environmental"].append("范围2排放数据缺失（位置法或市场法）")
        if metrics.scope3_emissions is None:
            gaps["environmental"].append("范围3排放数据缺失（建议披露）")
        if metrics.carbon_intensity is None:
            gaps["environmental"].append("碳强度数据缺失")
        if not self._check_renewable_energy(metrics):
            if metrics.renewable_energy_ratio is None:
                gaps["environmental"].append("可再生能源比例数据缺失")
            else:
                gaps["environmental"].append(f"可再生能源比例({metrics.renewable_energy_ratio:.1f}%)低于阈值({self.thresholds['renewable_energy_ratio']['min']}%)")
        
        # 社会维度检查
        if not self._check_gender_diversity(metrics):
            gaps["social"].append("性别多样性数据缺失或不合理")
        if metrics.employee_count is None:
            gaps["social"].append("员工数量数据缺失")
        
        # 治理维度检查
        if not self._check_board_independence(metrics):
            if metrics.board_independence_ratio is None:
                gaps["governance"].append("董事会独立性数据缺失")
            else:
                gaps["governance"].append(f"独立董事比例({metrics.board_independence_ratio:.1f}%)低于阈值({self.thresholds['board_independence']['min_ratio']*100}%)")
        if not self._check_ethics_training(metrics):
            if metrics.ethics_training_coverage is None:
                gaps["governance"].append("道德培训覆盖率数据缺失")
            else:
                gaps["governance"].append(f"道德培训覆盖率({metrics.ethics_training_coverage:.1f}%)低于阈值({self.thresholds['ethics_training']['min_coverage']}%)")
        
        return gaps
