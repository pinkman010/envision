"""SBTi目标追踪器

提供SBTi气候目标的设置、进度追踪和评分功能。
支持CDP和MSCI评级标准。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.esg.core.models import SBTiTarget


class SBTiTracker:
    """SBTi目标追踪器
    
    管理企业SBTi气候目标的全生命周期，包括：
    - 目标设定与验证状态追踪
    - 减排进度监控
    - CDP/MSCI评级对标
    - 偏差预警与改进建议
    """
    
    def __init__(self):
        self.targets: List[SBTiTarget] = []
        
    def create_target(
        self,
        baseline_year: int,
        target_year: int,
        baseline_emissions: float,
        reduction_rate: float,
        target_type: str = "absolute",
        pathway: str = "wb2c",
        scope_coverage: str = "1+2+3",
    ) -> SBTiTarget:
        """创建新的SBTi目标
        
        Args:
            baseline_year: 基准年
            target_year: 目标年
            baseline_emissions: 基准年排放量（吨CO2e）
            reduction_rate: 目标减排率（0-1）
            target_type: 目标类型（absolute/intensity/renewable）
            pathway: 温升路径（1.5c/wb2c/2c）
            scope_coverage: 覆盖范围（1+2/1+2+3）
            
        Returns:
            SBTiTarget对象
        """
        target_emissions = baseline_emissions * (1 - reduction_rate)
        
        target = SBTiTarget(
            status="target_set",
            target_type=target_type,
            baseline_year=baseline_year,
            target_year=target_year,
            baseline_emissions=baseline_emissions,
            target_emissions=target_emissions,
            reduction_rate=reduction_rate,
            pathway=pathway,
            scope_coverage=scope_coverage,
        )
        
        self.targets.append(target)
        return target
    
    def update_progress(
        self,
        target: SBTiTarget,
        current_year: int,
        current_emissions: float,
    ) -> Dict[str, Any]:
        """更新目标进度
        
        Args:
            target: SBTi目标对象
            current_year: 当前年份
            current_emissions: 当前排放量
            
        Returns:
            进度更新结果
        """
        target.current_year = current_year
        target.current_emissions = current_emissions
        
        progress_rate = target.get_progress_rate()
        progress_score = target.get_progress_score()
        on_track = target.is_on_track()
        
        # 生成预警信息
        warnings = []
        if on_track is False:
            warnings.append(f"警告：{current_year}年减排进度落后目标")
        elif on_track is True and progress_score < 50:
            warnings.append(f"提醒：当前减排进度{progress_rate:.1%}，需加速推进")
        
        return {
            "progress_rate": progress_rate,
            "progress_score": progress_score,
            "on_track": on_track,
            "warnings": warnings,
            "overall_score": target.get_overall_score(),
        }
    
    def validate_target(
        self,
        target: SBTiTarget,
        validation_date: str,
        pathway: str = "wb2c",
    ) -> SBTiTarget:
        """验证SBTi目标
        
        模拟SBTi官方验证流程。
        
        Args:
            target: SBTi目标对象
            validation_date: 验证日期（ISO格式）
            pathway: 验证通过的温升路径
            
        Returns:
            更新后的SBTiTarget对象
        """
        target.validation_date = validation_date
        target.pathway = pathway
        
        # 根据温升路径设置状态
        if pathway == "1.5c":
            target.status = "validated_1.5c"
        elif pathway == "wb2c":
            target.status = "validated_wb2c"
        elif pathway == "2c":
            target.status = "validated_2c"
        else:
            target.status = "validated"
        
        return target
    
    def get_cdp_alignment_score(self, target: SBTiTarget) -> Dict[str, Any]:
        """计算CDP对齐评分
        
        评估目标与CDP标准的对齐程度。
        
        Args:
            target: SBTi目标对象
            
        Returns:
            CDP对齐评分详情
        """
        score = 0
        details = []
        
        # 1. 目标验证状态（30分）
        if target.status.startswith("validated"):
            score += 30
            details.append("目标已通过SBTi验证 (+30)")
        elif target.status == "target_set":
            score += 15
            details.append("目标已设定但未验证 (+15)")
        elif target.status == "committed":
            score += 5
            details.append("已承诺但尚未设定目标 (+5)")
        
        # 2. 温升路径雄心（25分）
        if target.pathway == "1.5c":
            score += 25
            details.append("1.5°C雄心目标 (+25)")
        elif target.pathway == "wb2c":
            score += 20
            details.append("Well-below 2°C目标 (+20)")
        elif target.pathway == "2c":
            score += 15
            details.append("2°C目标 (+15)")
        
        # 3. 覆盖范围（20分）
        if target.scope_coverage == "1+2+3":
            score += 20
            details.append("覆盖范围1+2+3排放 (+20)")
        elif target.scope_coverage == "1+2":
            score += 12
            details.append("覆盖范围1+2排放 (+12)")
        
        # 4. 进度表现（25分）
        progress_score = target.get_progress_score()
        if progress_score >= 80:
            score += 25
            details.append("减排进度优秀 (+25)")
        elif progress_score >= 60:
            score += 18
            details.append("减排进度良好 (+18)")
        elif progress_score >= 40:
            score += 10
            details.append("减排进度一般 (+10)")
        else:
            details.append("减排进度落后 (+0)")
        
        # 确定CDP等级
        if score >= 80:
            cdp_level = "A/A-"
        elif score >= 60:
            cdp_level = "B/B-"
        elif score >= 40:
            cdp_level = "C/C-"
        else:
            cdp_level = "D/D-"
        
        return {
            "total_score": score,
            "cdp_level": cdp_level,
            "details": details,
            "target_status": target.status,
            "pathway": target.pathway,
            "progress_score": progress_score,
        }
    
    def get_msci_alignment_score(self, target: SBTiTarget) -> Dict[str, Any]:
        """计算MSCI ESG对齐评分
        
        评估目标对MSCI ESG评级的贡献。
        
        Args:
            target: SBTi目标对象
            
        Returns:
            MSCI对齐评分详情
        """
        score = 0
        key_issues = []
        
        # 1. 气候目标雄心（40分）
        if target.pathway == "1.5c":
            score += 40
            key_issues.append("气候目标：1.5°C雄心级别 (+40)")
        elif target.pathway == "wb2c":
            score += 35
            key_issues.append("气候目标：Well-below 2°C (+35)")
        elif target.pathway == "2c":
            score += 25
            key_issues.append("气候目标：2°C路径 (+25)")
        
        # 2. 目标验证可信度（30分）
        if target.status == "validated_1.5c":
            score += 30
            key_issues.append("SBTi验证：1.5°C目标 (+30)")
        elif target.status in ("validated_wb2c", "validated_2c", "validated"):
            score += 25
            key_issues.append("SBTi验证：通过 (+25)")
        elif target.status == "target_set":
            score += 10
            key_issues.append("目标待验证 (+10)")
        
        # 3. 减排进度（30分）
        progress = target.get_progress_rate()
        if progress is not None:
            if progress >= target.reduction_rate * 1.1:  # 超额完成
                score += 30
                key_issues.append("减排进度：超额完成 (+30)")
            elif progress >= target.reduction_rate * 0.9:  # 按计划
                score += 25
                key_issues.append("减排进度：按计划推进 (+25)")
            elif progress >= target.reduction_rate * 0.7:  # 略有滞后
                score += 15
                key_issues.append("减排进度：略有滞后 (+15)")
            else:
                key_issues.append("减排进度：明显落后 (+0)")
        
        # 确定对MSCI评级的预期贡献
        if score >= 80:
            contribution = "显著提升"
        elif score >= 60:
            contribution = "正面贡献"
        elif score >= 40:
            contribution = "中性"
        else:
            contribution = "潜在拖累"
        
        return {
            "total_score": score,
            "contribution": contribution,
            "key_issues": key_issues,
            "recommendations": self._generate_msci_recommendations(target, score),
        }
    
    def _generate_msci_recommendations(
        self, target: SBTiTarget, score: float
    ) -> List[str]:
        """生成MSCI评级改进建议
        
        Args:
            target: SBTi目标对象
            score: 当前得分
            
        Returns:
            改进建议列表
        """
        recommendations = []
        
        if target.status in ("not_committed", "removed"):
            recommendations.append("优先行动：加入SBTi并提交目标承诺")
        elif target.status == "committed":
            recommendations.append("优先行动：设定具体减排目标并提交验证")
        elif target.status == "target_set":
            recommendations.append("建议：尽快提交SBTi官方验证")
        
        if target.pathway not in ("1.5c", "wb2c"):
            recommendations.append("建议：提升目标雄心至Well-below 2°C或1.5°C路径")
        
        if target.scope_coverage != "1+2+3":
            recommendations.append("建议：扩展目标覆盖范围至范围3排放")
        
        if not target.is_on_track():
            recommendations.append("紧急：制定行动计划以重回减排轨道")
        
        return recommendations
    
    def generate_progress_report(self, target: SBTiTarget) -> Dict[str, Any]:
        """生成目标进度报告
        
        Args:
            target: SBTi目标对象
            
        Returns:
            完整进度报告
        """
        return {
            "target_summary": {
                "status": target.status,
                "baseline_year": target.baseline_year,
                "target_year": target.target_year,
                "reduction_target": f"{target.reduction_rate:.0%}",
                "pathway": target.pathway,
                "scope_coverage": target.scope_coverage,
            },
            "current_status": {
                "current_year": target.current_year,
                "progress_rate": target.get_progress_rate(),
                "progress_percentage": f"{target.get_progress_rate():.1%}" if target.get_progress_rate() else None,
                "on_track": target.is_on_track(),
            },
            "scores": {
                "sbti_score": target.get_overall_score(),
                "status_score": target.get_status_score(),
                "progress_score": target.get_progress_score(),
            },
            "cdp_alignment": self.get_cdp_alignment_score(target),
            "msci_alignment": self.get_msci_alignment_score(target),
        }


def create_sbti_tracker() -> SBTiTracker:
    """创建SBTi追踪器实例"""
    return SBTiTracker()


# 便捷函数
def quick_create_target(
    baseline_year: int,
    target_year: int,
    baseline_emissions: float,
    reduction_rate: float,
    pathway: str = "wb2c",
) -> SBTiTarget:
    """快速创建SBTi目标
    
    Args:
        baseline_year: 基准年
        target_year: 目标年
        baseline_emissions: 基准年排放量
        reduction_rate: 目标减排率
        pathway: 温升路径
        
    Returns:
        SBTiTarget对象
    """
    tracker = SBTiTracker()
    return tracker.create_target(
        baseline_year=baseline_year,
        target_year=target_year,
        baseline_emissions=baseline_emissions,
        reduction_rate=reduction_rate,
        pathway=pathway,
    )
