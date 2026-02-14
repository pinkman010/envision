"""ESG分析引擎

整合差距分析和策略生成，提供统一的ESG分析入口。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.analysis.strategy_generator import StrategyGenerator
from src.esg.core.models import (
    DEFAULT_TARGET_SCORE,
    GAP_THRESHOLD_HIGH,
    GAP_THRESHOLD_MEDIUM,
    AnalysisResult,
    BenchmarkData,
    ESGMetrics,
)


class ESGAnalysisEngine:
    """ESG分析引擎

    执行ESG指标的完整分析流程，包括数据质量校验、差距分析
    和改进策略生成。

    Attributes:
        weights: 各维度权重 (E/S/G)
        target_score: 目标得分
        warnings: 数据质量警告列表
    """

    def __init__(
        self, weights: Optional[Dict[str, float]] = None, target_score: float = DEFAULT_TARGET_SCORE
    ):
        """初始化分析引擎

        Args:
            weights: 各维度权重，默认为 {"E": 0.4, "S": 0.3, "G": 0.3}
            target_score: 目标得分，默认为配置值
        """
        self.weights: Dict[str, float] = weights or {"E": 0.4, "S": 0.3, "G": 0.3}
        self.target_score: float = target_score
        self.warnings: List[str] = []
        
        # 初始化专业的分析器和策略生成器
        self.gap_analyzer = GapAnalyzer()
        self.strategy_generator = StrategyGenerator(self.gap_analyzer)

        # 验证权重
        if abs(sum(self.weights.values()) - 1.0) > 0.001:
            raise ValueError("权重总和必须等于1.0")

    def analyze(
        self, metrics: ESGMetrics, benchmark: Optional[BenchmarkData] = None
    ) -> AnalysisResult:
        """执行完整的ESG分析

        Args:
            metrics: ESG指标数据
            benchmark: 可选的行业基准数据

        Returns:
            分析结果对象
        """
        self.warnings = []

        # 数据质量校验
        self._validate_data_quality(metrics)

        # 计算各维度得分
        e_score: float = metrics.get_dimension_score("E")
        s_score: float = metrics.get_dimension_score("S")
        g_score: float = metrics.get_dimension_score("G")

        # 计算总体得分
        overall: float = (
            e_score * self.weights["E"] + s_score * self.weights["S"] + g_score * self.weights["G"]
        )

        # 差距分析 - 使用专业的 GapAnalyzer
        gaps: Dict[str, Any] = self._analyze_gaps_with_analyzer(metrics, benchmark)

        # 生成改进策略 - 使用专业的 StrategyGenerator
        strategies: List[Dict[str, Any]] = self._generate_strategies_with_generator(metrics, benchmark)

        return AnalysisResult(
            metrics=metrics,
            weights=self.weights,
            gap_analysis=gaps,
            strategies=strategies,
            overall_score=round(overall, 1),
            confidence_level=metrics.calculate_overall_confidence(),
            data_quality_warnings=self.warnings.copy(),
            analyzed_at=datetime.now().isoformat(),
        )

    def _validate_data_quality(self, metrics: ESGMetrics) -> None:
        """数据质量校验 - 全面覆盖E/S/G维度核心指标

        检查数据中的异常值和潜在问题。
        """
        # ===== 环境维度 (E) =====
        # 碳排放数值合理性检查
        if metrics.carbon_emissions is not None:
            if metrics.carbon_emissions < 1000:
                self.warnings.append(
                    f"碳排放数值({metrics.carbon_emissions})疑似单位错误，通常应为吨CO2当量"
                )
            elif metrics.carbon_emissions > 1_000_000_000:
                self.warnings.append(f"碳排放数值({metrics.carbon_emissions})异常巨大，请核实单位")
        
        # 碳强度检查
        if metrics.carbon_intensity is not None:
            if metrics.carbon_intensity < 0:
                self.warnings.append("碳强度为负数，数据有误")
            elif metrics.carbon_intensity > 100:
                self.warnings.append("碳强度异常高，请核实单位是否为吨CO2e/百万元营收")
        
        # 范围3覆盖率检查
        if metrics.scope3_coverage_percentage is not None:
            if not 0 <= metrics.scope3_coverage_percentage <= 1:
                self.warnings.append("范围3覆盖率应在0-100%之间")
        
        # 可再生能源比例检查
        if metrics.renewable_energy_ratio is not None:
            if metrics.renewable_energy_ratio > 100:
                self.warnings.append("可再生能源比例超过100%，数据有误")
            elif metrics.renewable_energy_ratio < 0:
                self.warnings.append("可再生能源比例为负数，数据有误")
        
        # 新能源特色指标检查
        if metrics.turbine_availability is not None and not 0 <= metrics.turbine_availability <= 100:
            self.warnings.append("风机可利用率应在0-100%之间")
        if metrics.battery_cycle_life is not None and metrics.battery_cycle_life < 0:
            self.warnings.append("电池循环寿命不能为负数")
        if metrics.electrolysis_efficiency is not None and not 0 <= metrics.electrolysis_efficiency <= 100:
            self.warnings.append("电解效率应在0-100%之间")

        # ===== 社会维度 (S) =====
        # 员工数量检查
        if metrics.employee_count is not None:
            if metrics.employee_count < 10:
                self.warnings.append("员工数异常偏低，可能未包含全部员工")
            elif metrics.employee_count > 5_000_000:
                self.warnings.append("员工数异常巨大，请核实数据")
        
        # 性别比例检查
        if metrics.female_ratio is not None:
            if metrics.female_ratio > 100:
                self.warnings.append("女性员工比例超过100%，数据有误")
            elif metrics.female_ratio < 0:
                self.warnings.append("女性员工比例为负数，数据有误")
        
        if metrics.female_executive_ratio is not None:
            if metrics.female_executive_ratio > 100:
                self.warnings.append("高管层女性比例超过100%，数据有误")
            elif metrics.female_executive_ratio < 0:
                self.warnings.append("高管层女性比例为负数，数据有误")
        
        # 安全指标检查
        if metrics.trir is not None and metrics.trir < 0:
            self.warnings.append("TRIR不能为负数")
        if metrics.ltifr is not None and metrics.ltifr < 0:
            self.warnings.append("LTIFR不能为负数")

        # ===== 治理维度 (G) =====
        # 董事会独立性检查
        if metrics.board_independence_ratio is not None:
            if metrics.board_independence_ratio > 100:
                self.warnings.append("董事会独立比例超过100%，数据有误")
            elif metrics.board_independence_ratio < 0:
                self.warnings.append("董事会独立比例为负数，数据有误")
        
        if metrics.esg_committee_independence is not None:
            if not 0 <= metrics.esg_committee_independence <= 100:
                self.warnings.append("ESG委员会独立性应在0-100%之间")
        
        # 培训覆盖率检查
        if metrics.ethics_training_coverage is not None and not 0 <= metrics.ethics_training_coverage <= 100:
            self.warnings.append("道德培训覆盖率应在0-100%之间")
        if metrics.anti_corruption_training_coverage is not None and not 0 <= metrics.anti_corruption_training_coverage <= 100:
            self.warnings.append("反腐败培训覆盖率应在0-100%之间")

        # 数据完整性检查
        missing_dimensions: List[str] = []
        for dim in ["E", "S", "G"]:
            if not metrics.has_dimension_data(dim):
                missing_dimensions.append(dim)

        if missing_dimensions:
            self.warnings.append(f"以下维度缺少数据: {', '.join(missing_dimensions)}")

    def _analyze_gaps_with_analyzer(
        self, metrics: ESGMetrics, benchmark: Optional[BenchmarkData] = None
    ) -> Dict[str, Any]:
        """差距分析 - 使用专业的 GapAnalyzer

        Args:
            metrics: ESG指标数据
            benchmark: 可选的行业基准数据

        Returns:
            差距分析结果字典
        """
        benchmark_company = "行业平均"
        if benchmark is not None:
            benchmark_company = f"{benchmark.industry}行业平均"
        
        # 使用 GapAnalyzer 进行维度差距分析
        try:
            dim_gaps = self.gap_analyzer.analyze_dimension_gap(metrics, benchmark_company)
            
            gaps: Dict[str, Any] = {"dimensions": {}, "overall": {}}
            
            for dim in ["E", "S", "G"]:
                gap_result = dim_gaps.get(dim)
                if gap_result:
                    gaps["dimensions"][dim] = {
                        "current": gap_result.current,
                        "target": gap_result.benchmark,
                        "gap": gap_result.gap,
                        "gap_level": gap_result.priority,
                        "comparison": benchmark_company,
                    }
                else:
                    # 回退到简单计算
                    current = metrics.get_dimension_score(dim)
                    target = self.target_score
                    gaps["dimensions"][dim] = {
                        "current": round(current, 1),
                        "target": target,
                        "gap": round(target - current, 1),
                        "gap_level": "中" if target - current > 0 else "已达目标",
                        "comparison": "目标值",
                    }
            
            # 总体差距
            overall_current = sum(
                gaps["dimensions"][dim]["current"] * self.weights[dim] for dim in ["E", "S", "G"]
            )
            overall_target = sum(
                gaps["dimensions"][dim]["target"] * self.weights[dim] for dim in ["E", "S", "G"]
            )
            
            gaps["overall"] = {
                "current": round(overall_current, 1),
                "target": round(overall_target, 1),
                "gap": round(overall_target - overall_current, 1),
                "score": round(overall_current, 1),
            }
            
            return gaps
            
        except Exception as e:
            # 如果 GapAnalyzer 失败，回退到简单计算
            return self._analyze_gaps_simple(metrics, benchmark)
    
    def _analyze_gaps_simple(
        self, metrics: ESGMetrics, benchmark: Optional[BenchmarkData] = None
    ) -> Dict[str, Any]:
        """简单的差距分析（回退方案）"""
        gaps: Dict[str, Any] = {"dimensions": {}, "overall": {}}

        for dim in ["E", "S", "G"]:
            current: float = metrics.get_dimension_score(dim)
            target: float = self.target_score
            gap: float = target - current

            if gap >= GAP_THRESHOLD_HIGH:
                gap_level = "高"
            elif gap >= GAP_THRESHOLD_MEDIUM:
                gap_level = "中"
            elif gap > 0:
                gap_level = "低"
            else:
                gap_level = "已达目标"

            gaps["dimensions"][dim] = {
                "current": round(current, 1),
                "target": target,
                "gap": round(gap, 1),
                "gap_level": gap_level,
                "comparison": "目标值",
            }

        overall_current = sum(
            gaps["dimensions"][dim]["current"] * self.weights[dim] for dim in ["E", "S", "G"]
        )
        overall_target = sum(
            gaps["dimensions"][dim]["target"] * self.weights[dim] for dim in ["E", "S", "G"]
        )

        gaps["overall"] = {
            "current": round(overall_current, 1),
            "target": round(overall_target, 1),
            "gap": round(overall_target - overall_current, 1),
            "score": round(overall_current, 1),
        }

        return gaps

    def _generate_strategies_with_generator(
        self, metrics: ESGMetrics, benchmark: Optional[BenchmarkData] = None
    ) -> List[Dict[str, Any]]:
        """生成改进策略 - 使用专业的 StrategyGenerator

        Args:
            metrics: ESG指标数据
            benchmark: 可选的行业基准数据

        Returns:
            改进策略列表
        """
        benchmark_company = "行业平均"
        if benchmark is not None:
            benchmark_company = f"{benchmark.industry}行业平均"
        
        try:
            # 使用 StrategyGenerator 生成专业策略
            strategies = self.strategy_generator.generate_strategies(
                metrics, 
                benchmark_company=benchmark_company,
                max_strategies=6
            )
            
            # 转换为字典格式
            return [self.strategy_generator.to_dict(s) for s in strategies]
            
        except Exception as e:
            # 如果 StrategyGenerator 失败，回退到简单策略
            return self._generate_strategies_simple(metrics, benchmark_company)
    
    def _generate_strategies_simple(self, metrics: ESGMetrics, benchmark_company: str) -> List[Dict[str, Any]]:
        """简单的策略生成（回退方案）"""
        strategies: List[Dict[str, Any]] = []
        scores = metrics.get_all_dimension_scores()
        
        for dim in ["E", "S", "G"]:
            current = scores[dim]
            gap = self.target_score - current
            
            if gap > 0:
                if gap >= GAP_THRESHOLD_HIGH:
                    priority = "高"
                elif gap >= GAP_THRESHOLD_MEDIUM:
                    priority = "中"
                else:
                    priority = "低"
                
                strategies.append({
                    "dimension": dim,
                    "title": f"提升{dim}维度表现",
                    "description": f"改进{dim}维度的ESG指标",
                    "priority": priority,
                    "current_score": round(current, 1),
                    "target_gap": round(gap, 1),
                    "actions": [f"识别{dim}维度改进机会", "制定行动计划"],
                })
        
        # 按优先级排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        strategies.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return strategies

    def _estimate_timeline(self, gap: float) -> str:
        """估算改进时间线

        Args:
            gap: 差距值

        Returns:
            预计时间范围
        """
        if gap >= GAP_THRESHOLD_HIGH:
            return "12-24个月"
        elif gap >= GAP_THRESHOLD_MEDIUM:
            return "6-12个月"
        elif gap > 0:
            return "3-6个月"
        return "已达标"

    def quick_analyze(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """快速分析

        执行简化的快速分析，返回核心结果。

        Args:
            metrics: ESG指标数据

        Returns:
            简化版分析结果
        """
        scores: Dict[str, float] = metrics.get_all_dimension_scores()
        overall: float = sum(scores[d] * self.weights[d] for d in ["E", "S", "G"])

        return {
            "company": metrics.company_name,
            "year": metrics.year,
            "scores": {
                "environmental": round(scores["E"], 1),
                "social": round(scores["S"], 1),
                "governance": round(scores["G"], 1),
                "overall": round(overall, 1),
            },
            "confidence": metrics.calculate_overall_confidence(),
        }
