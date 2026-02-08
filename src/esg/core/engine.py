"""ESG分析引擎"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.esg.core.models import (
    DEFAULT_SCORE,
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

        # 差距分析
        gaps: Dict[str, Any] = self._analyze_gaps(metrics, benchmark)

        # 生成改进策略
        strategies: List[Dict[str, Any]] = self._generate_strategies(gaps)

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
        """数据质量校验

        检查数据中的异常值和潜在问题。

        Args:
            metrics: ESG指标数据
        """
        # 碳排放数值合理性检查
        if metrics.carbon_emissions is not None:
            if metrics.carbon_emissions < 1000:
                self.warnings.append(
                    f"碳排放数值({metrics.carbon_emissions})疑似单位错误，通常应为吨CO2当量"
                )
            elif metrics.carbon_emissions > 1000000000:
                self.warnings.append(f"碳排放数值({metrics.carbon_emissions})异常巨大，请核实单位")

        # 员工数量检查
        if metrics.employee_count is not None:
            if metrics.employee_count < 10:
                self.warnings.append("员工数异常偏低，可能未包含全部员工")
            elif metrics.employee_count > 5000000:
                self.warnings.append("员工数异常巨大，请核实数据")

        # 可再生能源比例检查
        if metrics.renewable_energy_ratio is not None:
            if metrics.renewable_energy_ratio > 100:
                self.warnings.append("可再生能源比例超过100%，数据有误")
            elif metrics.renewable_energy_ratio < 0:
                self.warnings.append("可再生能源比例为负数，数据有误")

        # 董事会独立性检查
        if metrics.board_independence_ratio is not None:
            if metrics.board_independence_ratio > 100:
                self.warnings.append("董事会独立比例超过100%，数据有误")
            elif metrics.board_independence_ratio < 0:
                self.warnings.append("董事会独立比例为负数，数据有误")

        # 性别比例检查
        if metrics.female_ratio is not None:
            if metrics.female_ratio > 100:
                self.warnings.append("女性员工比例超过100%，数据有误")
            elif metrics.female_ratio < 0:
                self.warnings.append("女性员工比例为负数，数据有误")

        # 数据完整性检查
        missing_dimensions: List[str] = []
        for dim in ["E", "S", "G"]:
            if not metrics.has_dimension_data(dim):
                missing_dimensions.append(dim)

        if missing_dimensions:
            self.warnings.append(f"以下维度缺少数据: {', '.join(missing_dimensions)}")

    def _analyze_gaps(
        self, metrics: ESGMetrics, benchmark: Optional[BenchmarkData] = None
    ) -> Dict[str, Any]:
        """差距分析

        对比当前表现与目标/行业基准的差距。

        Args:
            metrics: ESG指标数据
            benchmark: 可选的行业基准数据

        Returns:
            差距分析结果字典
        """
        gaps: Dict[str, Any] = {"dimensions": {}, "overall": {}}

        for dim in ["E", "S", "G"]:
            current: float = metrics.get_dimension_score(dim)

            # 确定目标值
            if benchmark is not None:
                benchmark_metrics: ESGMetrics = benchmark.to_metrics()
                target: float = benchmark_metrics.get_dimension_score(dim)
                comparison: str = f"{benchmark.industry}行业平均"
            else:
                target = self.target_score
                comparison = "目标值"

            gap: float = target - current

            # 确定差距等级
            if gap >= GAP_THRESHOLD_HIGH:
                gap_level: str = "高"
            elif gap >= GAP_THRESHOLD_MEDIUM:
                gap_level = "中"
            elif gap > 0:
                gap_level = "低"
            else:
                gap_level = "已达目标"

            gaps["dimensions"][dim] = {
                "current": round(current, 1),
                "target": round(target, 1),
                "gap": round(gap, 1),
                "gap_level": gap_level,
                "comparison": comparison,
            }

        # 总体差距
        overall_current: float = sum(
            gaps["dimensions"][dim]["current"] * self.weights[dim] for dim in ["E", "S", "G"]
        )
        overall_target: float = sum(
            gaps["dimensions"][dim]["target"] * self.weights[dim] for dim in ["E", "S", "G"]
        )
        overall_gap: float = overall_target - overall_current

        gaps["overall"] = {
            "current": round(overall_current, 1),
            "target": round(overall_target, 1),
            "gap": round(overall_gap, 1),
            "score": round(overall_current, 1),
        }

        return gaps

    def _generate_strategies(self, gaps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改进策略

        根据差距分析结果生成针对性的改进策略。

        Args:
            gaps: 差距分析结果

        Returns:
            改进策略列表
        """
        strategies: List[Dict[str, Any]] = []

        strategy_templates: Dict[str, Dict[str, Any]] = {
            "E": {
                "title": "提升环境绩效",
                "description": "通过改进能源结构和资源利用效率，降低环境影响",
                "actions": [
                    "建立完善的碳排放核算体系",
                    "制定可再生能源使用目标",
                    "实施能源效率提升计划",
                    "优化废物回收和处理流程",
                ],
                "quick_wins": ["安装智能电表", "更换LED照明"],
            },
            "S": {
                "title": "加强社会责任",
                "description": "提升员工福祉和社区参与度",
                "actions": [
                    "完善员工多元化政策",
                    "增加员工培训投入",
                    "加强职业健康安全管理",
                    "扩大社区投资规模",
                ],
                "quick_wins": ["举办员工活动", "建立反馈渠道"],
            },
            "G": {
                "title": "优化公司治理",
                "description": "提升治理透明度和董事会效能",
                "actions": [
                    "提升董事会独立性",
                    "完善ESG信息披露",
                    "加强商业道德培训",
                    "建立ESG治理架构",
                ],
                "quick_wins": ["发布ESG报告", "制定行为准则"],
            },
        }

        for dim in ["E", "S", "G"]:
            dim_gaps: Dict[str, Any] = gaps.get("dimensions", {}).get(dim, {})
            gap_value: float = dim_gaps.get("gap", 0)
            current: float = dim_gaps.get("current", 0)

            if gap_value > 0:
                template: Dict[str, Any] = strategy_templates[dim]

                # 确定优先级
                if gap_value >= GAP_THRESHOLD_HIGH:
                    priority: str = "高"
                elif gap_value >= GAP_THRESHOLD_MEDIUM:
                    priority = "中"
                else:
                    priority = "低"

                # 根据差距大小调整建议
                actions: List[str] = template["actions"].copy()
                if current < 30:
                    actions.insert(0, f"{dim}维度基础薄弱，建议优先建立管理体系")

                strategies.append(
                    {
                        "dimension": dim,
                        "title": template["title"],
                        "description": template["description"],
                        "priority": priority,
                        "current_score": round(current, 1),
                        "target_gap": round(gap_value, 1),
                        "actions": actions,
                        "quick_wins": template["quick_wins"],
                        "estimated_timeline": self._estimate_timeline(gap_value),
                    }
                )

        # 按优先级排序
        priority_order: Dict[str, int] = {"高": 0, "中": 1, "低": 2}
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
