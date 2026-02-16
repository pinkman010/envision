"""差距分析器

对标行业标杆，计算维度差距和指标差距。
采用Repository模式实现数据访问层的解耦。
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.esg.config import DEFAULT_SCORE, ESG_DIMENSION_NAMES, MOCK_DATA_DIR
from src.esg.core.models import ESGMetrics

# 历史数据文件路径
HISTORICAL_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "mock_historical_metrics.json"


@dataclass
class GapResult:
    """差距分析结果"""

    dimension: str
    current: float
    benchmark: float
    gap: float
    gap_percentage: float
    priority: str


@dataclass
class IndicatorGap:
    """指标差距"""

    indicator_id: str
    indicator_name: str
    current_score: float
    benchmark_score: float
    gap: float
    disclosure_level: str


class BenchmarkRepository(ABC):
    """标杆数据仓库抽象基类

    定义标杆数据访问的标准接口，支持不同的数据源实现。
    """

    @abstractmethod
    def load_data(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """加载标杆数据

        Returns:
            (companies_data, indicator_names) 元组
        """
        pass

    @abstractmethod
    def get_available_companies(self) -> List[str]:
        """获取可用的标杆企业列表"""
        pass

    @abstractmethod
    def get_benchmark(self, company: str) -> Optional[Dict[str, Any]]:
        """获取指定企业的标杆数据"""
        pass


class JsonBenchmarkRepository(BenchmarkRepository):
    """JSON文件标杆数据仓库

    从JSON文件加载标杆数据，支持fallback到默认数据。
    """

    # 默认标杆数据（当文件不存在时使用）
    DEFAULT_BENCHMARK_DATA = {
        "companies": {
            "行业平均": {
                "overall_score": 70.0,
                "dimensions": {"E": 68.0, "S": 70.0, "G": 72.0},
                "indicators": {
                    "renewable_energy": {"score": 65.0, "disclosure": "中"},
                    "carbon_emissions": {"score": 68.0, "disclosure": "中"},
                    "employee_diversity": {"score": 72.0, "disclosure": "中"},
                    "board_independence": {"score": 75.0, "disclosure": "中"},
                },
            },
            "维斯塔斯": {
                "overall_score": 88.0,
                "dimensions": {"E": 90.0, "S": 85.0, "G": 89.0},
                "indicators": {
                    "renewable_energy": {"score": 95.0, "disclosure": "高"},
                    "carbon_emissions": {"score": 90.0, "disclosure": "高"},
                    "employee_diversity": {"score": 82.0, "disclosure": "高"},
                    "board_independence": {"score": 90.0, "disclosure": "高"},
                },
            },
            "西门子歌美飒": {
                "overall_score": 85.0,
                "dimensions": {"E": 87.0, "S": 82.0, "G": 86.0},
                "indicators": {
                    "renewable_energy": {"score": 92.0, "disclosure": "高"},
                    "carbon_emissions": {"score": 88.0, "disclosure": "高"},
                    "employee_diversity": {"score": 80.0, "disclosure": "高"},
                    "board_independence": {"score": 88.0, "disclosure": "高"},
                },
            },
        },
        "indicator_names": {
            "renewable_energy": "可再生能源使用比例",
            "carbon_emissions": "碳排放管理",
            "employee_diversity": "员工多元化",
            "board_independence": "董事会独立性",
        },
    }

    def __init__(self, data_source: Optional[Path] = None):
        """初始化仓库

        Args:
            data_source: JSON文件路径，默认为 MOCK_DATA_DIR / "benchmark_data.json"
        """
        self.data_source = data_source or (MOCK_DATA_DIR / "benchmark_data.json")
        self._benchmark_data: Dict[str, Any] = {}
        self._indicator_names: Dict[str, str] = {}
        self._load_data()

    def _load_data(self) -> None:
        """加载数据，文件不存在时使用默认数据"""
        try:
            if self.data_source.exists():
                with open(self.data_source, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._benchmark_data = data.get("companies", {})
                self._indicator_names = data.get("indicator_names", {})
            else:
                # 使用默认fallback数据
                self._benchmark_data = self.DEFAULT_BENCHMARK_DATA["companies"]
                self._indicator_names = self.DEFAULT_BENCHMARK_DATA["indicator_names"]
        except (FileNotFoundError, json.JSONDecodeError):
            # 文件不存在或解析错误时使用默认数据
            self._benchmark_data = self.DEFAULT_BENCHMARK_DATA["companies"]
            self._indicator_names = self.DEFAULT_BENCHMARK_DATA["indicator_names"]

    def load_data(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """加载标杆数据"""
        return self._benchmark_data, self._indicator_names

    def get_available_companies(self) -> List[str]:
        """获取可用的标杆企业列表"""
        return list(self._benchmark_data.keys())

    def get_benchmark(self, company: str) -> Optional[Dict[str, Any]]:
        """获取指定企业的标杆数据"""
        return self._benchmark_data.get(company)


class GapAnalyzer:
    """ESG差距分析器

    对标行业标杆企业，计算维度差距和指标差距。
    支持依赖注入不同的BenchmarkRepository实现。

    Attributes:
        repository: 标杆数据仓库
        benchmark_data: 标杆数据字典
        indicator_names: 指标名称映射
    """

    # 指标映射：从ESGMetrics字段到benchmark指标ID
    # 完整覆盖E/S/G三维度核心指标，与models.py中的权重配置对齐
    INDICATOR_MAPPING = {
        # ===== 环境维度 (E) - 对应 E_DIMENSION_WEIGHTS =====
        # 一级指标：排放与气候（45%）
        "carbon_intensity": "carbon_intensity",
        "scope3_coverage_percentage": "scope3_coverage",
        "sbti_target": "sbti_target",
        # 二级指标：运营效率（30%）
        "renewable_energy_ratio": "renewable_energy",
        "energy_efficiency": "energy_efficiency",
        "waste_recycling_rate": "waste_recycling",
        "water_intensity": "water_management",
        # 三级指标：新能源特色（25%）
        "turbine_availability": "turbine_performance",
        "curtailment_rate": "curtailment_management",
        "battery_cycle_life": "battery_durability",
        "battery_recycling_rate": "battery_recycling",
        "electrolysis_efficiency": "hydrogen_production",
        "energy_storage_safety_score": "storage_safety",
        # ===== 社会维度 (S) - 对应 S_DIMENSION_WEIGHTS =====
        # 一级指标：员工发展与多元化（45%）
        "female_ratio": "gender_diversity",
        "female_executive_ratio": "executive_diversity",
        "training_hours": "training_development",
        "employee_count": "employee_scale",
        # 二级指标：安全与福祉（30%）
        "trir": "safety_performance",
        "ltifr": "safety_performance",
        "safety_investment_ratio": "safety_investment",
        # 三级指标：社区责任（25%）
        "community_investment_per_revenue": "community_engagement",
        "local_employment_ratio": "local_employment",
        # ===== 治理维度 (G) - 对应 G_DIMENSION_WEIGHTS =====
        # 第一层：董事会与治理结构（35%）
        "board_independence_ratio": "board_independence",
        "esg_committee_independence": "esg_governance_structure",
        # 第二层：合规与商业道德（30%）
        "ethics_training_coverage": "ethics_compliance",
        "anti_corruption_training_coverage": "anti_corruption",
        "whistleblower_protection": "whistleblower_protection",
        # 第三层：气候治理（20%）
        "climate_governance": "climate_governance_framework",
        "tcfd_disclosure": "tcfd_disclosure_quality",
        # 第四层：透明度与问责（15%）
        "esg_report_quality": "report_quality",
    }

    def __init__(
        self, repository: Optional[BenchmarkRepository] = None, data_source: Optional[Path] = None
    ):
        """初始化分析器

        Args:
            repository: 自定义标杆数据仓库（优先使用）
            data_source: 自定义标杆数据源路径（当repository为None时使用）
        """
        if repository is not None:
            self.repository = repository
        else:
            self.repository = JsonBenchmarkRepository(data_source)

        self.benchmark_data, self.indicator_names = self.repository.load_data()

    def analyze_dimension_gap(
        self, metrics: ESGMetrics, benchmark_company: str = "行业平均"
    ) -> Dict[str, GapResult]:
        """分析维度差距

        Args:
            metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称

        Returns:
            各维度差距分析结果
        """
        benchmark = self.repository.get_benchmark(benchmark_company)
        if not benchmark:
            raise ValueError(f"未找到标杆企业: {benchmark_company}")

        results = {}
        for dim in ["E", "S", "G"]:
            current = metrics.get_dimension_score(dim)
            target = benchmark["dimensions"].get(dim, DEFAULT_SCORE)
            gap = target - current

            # 计算差距百分比
            gap_percentage = (gap / target * 100) if target > 0 else 0.0

            # 确定优先级
            priority = self._calculate_priority(abs(gap))

            results[dim] = GapResult(
                dimension=dim,
                current=round(current, 1),
                benchmark=round(target, 1),
                gap=round(gap, 1),
                gap_percentage=round(gap_percentage, 1),
                priority=priority,
            )

        return results

    def analyze_indicator_gap(
        self, metrics: ESGMetrics, benchmark_company: str = "行业平均"
    ) -> List[IndicatorGap]:
        """分析指标级差距

        Args:
            metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称

        Returns:
            指标差距列表
        """
        benchmark = self.repository.get_benchmark(benchmark_company)
        if not benchmark:
            raise ValueError(f"未找到标杆企业: {benchmark_company}")

        results = []
        benchmark_indicators = benchmark.get("indicators", {})

        # 计算当前指标分数
        current_indicators = self._calculate_indicator_scores(metrics)

        for indicator_id, current_score in current_indicators.items():
            bench_data = benchmark_indicators.get(indicator_id, {})
            bench_score = (
                bench_data.get("score", DEFAULT_SCORE)
                if isinstance(bench_data, dict)
                else bench_data
            )

            gap = IndicatorGap(
                indicator_id=indicator_id,
                indicator_name=self.indicator_names.get(indicator_id, indicator_id),
                current_score=round(current_score, 1),
                benchmark_score=round(bench_score, 1),
                gap=round(bench_score - current_score, 1),
                disclosure_level=(
                    bench_data.get("disclosure", "未知") if isinstance(bench_data, dict) else "未知"
                ),
            )
            results.append(gap)

        # 按差距从大到小排序
        results.sort(key=lambda x: abs(x.gap), reverse=True)
        return results

    def compare_with_multiple(
        self, metrics: ESGMetrics, benchmark_companies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """与多家标杆企业对比

        Args:
            metrics: 当前企业ESG指标
            benchmark_companies: 标杆企业列表，默认使用所有可用标杆

        Returns:
            多标杆对比结果
        """
        if benchmark_companies is None:
            benchmark_companies = self.repository.get_available_companies()

        comparisons = []
        for company in benchmark_companies:
            benchmark = self.repository.get_benchmark(company)
            if not benchmark:
                continue

            dim_gaps = self.analyze_dimension_gap(metrics, company)
            total_gap = sum(abs(g.gap) for g in dim_gaps.values())

            comparisons.append(
                {
                    "company": company,
                    "overall_score": benchmark.get("overall_score", 0),
                    "dimension_scores": {
                        dim: {"benchmark": g.benchmark, "current": g.current, "gap": g.gap}
                        for dim, g in dim_gaps.items()
                    },
                    "total_gap": round(total_gap, 1),
                }
            )

        # 按总差距排序
        comparisons.sort(key=lambda x: x["total_gap"])

        # 计算最佳标杆
        best_benchmark = comparisons[0]["company"] if comparisons else None

        return {
            "comparisons": comparisons,
            "best_benchmark": best_benchmark,
            "overall_ranking": self._calculate_ranking(metrics),
        }

    def get_improvement_areas(
        self, metrics: ESGMetrics, top_n: int = 3, benchmark_company: str = "行业平均"
    ) -> List[Dict[str, Any]]:
        """获取优先改进领域

        Args:
            metrics: 当前企业ESG指标
            top_n: 返回前N个改进领域
            benchmark_company: 标杆企业名称

        Returns:
            优先改进领域列表
        """
        dim_gaps = self.analyze_dimension_gap(metrics, benchmark_company)
        indicator_gaps = self.analyze_indicator_gap(metrics, benchmark_company)

        # 合并维度和指标差距
        all_gaps = []

        # 添加维度差距
        for dim, gap in dim_gaps.items():
            if gap.gap > 0:
                all_gaps.append(
                    {
                        "type": "dimension",
                        "id": dim,
                        "name": ESG_DIMENSION_NAMES.get(dim, dim),
                        "gap": gap.gap,
                        "priority": gap.priority,
                    }
                )

        # 添加指标差距（前N个）
        for ind_gap in indicator_gaps[: top_n * 2]:
            if ind_gap.gap > 0:
                all_gaps.append(
                    {
                        "type": "indicator",
                        "id": ind_gap.indicator_id,
                        "name": ind_gap.indicator_name,
                        "gap": ind_gap.gap,
                        "priority": self._calculate_priority(ind_gap.gap),
                    }
                )

        # 按差距排序并去重
        all_gaps.sort(key=lambda x: x["gap"], reverse=True)

        # 返回前N个
        return all_gaps[:top_n]

    def get_available_benchmarks(self) -> List[str]:
        """获取可用的标杆企业列表"""
        return self.repository.get_available_companies()

    # ============================================================================
    # 指标评分规则配置 (配置驱动模式)
    # ============================================================================
    # 使用配置驱动的评分规则，替代大量硬编码的if语句
    # 评分类型: direct(直接), ratio(比例), inverse(逆向), threshold(分段), boolean(布尔)

    INDICATOR_SCORING_RULES = {
        # ===== 环境维度 (E) =====
        # 碳强度（逆向：越低越好）
        "carbon_intensity": {"type": "inverse", "excellent": 0, "poor": 100},
        # 范围3覆盖率
        "scope3_coverage": {"type": "range", "ranges": [(0.8, 100), (0.4, 0), (0, 100)]},
        # SBTi目标（对象方法）
        "sbti_target": {"type": "method", "method": "get_overall_score"},
        # 直接比例型
        "renewable_energy": {"type": "ratio", "max": 100},
        "energy_efficiency": {"type": "direct", "max": 100},
        "waste_recycling": {"type": "ratio", "max": 100},
        # 水资源强度（逆向）
        "water_management": {"type": "inverse", "excellent": 15, "poor": 100},
        # 风机可利用率（基准比例）
        "turbine_performance": {"type": "benchmark", "benchmark": 97.0},
        # 弃风率（逆向）
        "curtailment_management": {"type": "inverse", "excellent": 2, "poor": 10},
        # 电池循环寿命
        "battery_durability": {"type": "benchmark", "benchmark": 6000.0},
        "battery_recycling": {"type": "ratio", "max": 100},
        # 电解效率
        "hydrogen_production": {"type": "benchmark", "benchmark": 70.0},
        # 直接分数
        "storage_safety": {"type": "direct", "max": 100},
        # ===== 社会维度 (S) =====
        # 性别多元化（分段计算，在单独方法中处理）
        "gender_diversity": {"type": "composite"},
        "executive_diversity": {"type": "ratio", "max": 100},
        # 培训发展（复合）
        "training_development": {"type": "composite"},
        # 员工规模（对数）
        "employee_scale": {"type": "log_scale", "base": 100.0, "factor": 20.0},
        # 安全绩效（复合）
        "safety_performance": {"type": "composite"},
        "safety_investment": {"type": "ratio", "max": 100},
        "community_engagement": {"type": "ratio", "max": 100},
        "local_employment": {"type": "ratio", "max": 100},
        # ===== 治理维度 (G) =====
        # 董事会独立性（分段）
        "board_independence": {"type": "threshold", "ranges": [(50, 100), (33, 60), (0, 0)]},
        # ESG治理架构
        "esg_governance_structure": {"type": "ratio", "max": 50},
        # 合规（复合）
        "ethics_compliance": {"type": "composite"},
        "anti_corruption": {"type": "composite"},
        # 举报人保护
        "whistleblower_protection": {"type": "boolean"},
        # 气候治理（复合）
        "climate_governance_framework": {"type": "composite"},
        # TCFD披露（复合）
        "tcfd_disclosure_quality": {"type": "composite"},
        # 报告质量
        "report_quality": {"type": "direct", "max": 100},
    }

    def _calculate_indicator_scores(self, metrics: ESGMetrics) -> Dict[str, float]:
        """计算各项指标分数

        基于ESGMetrics数据计算各细分指标分数，与INDICATOR_MAPPING对齐。
        使用配置驱动的评分规则，大幅降低圈复杂度。

        Returns:
            Dict[str, float]: 指标ID到分数的映射
        """
        scores = {}

        # 批量计算通用指标
        for metric_name, indicator_id in self.INDICATOR_MAPPING.items():
            value = getattr(metrics, metric_name, None)
            if value is None:
                continue

            rule = self.INDICATOR_SCORING_RULES.get(indicator_id)
            if not rule:
                continue

            score = self._compute_score_from_rule(value, rule, metrics)
            if score is not None:
                scores[indicator_id] = score

        return scores

    def _compute_score_from_rule(self, value, rule: dict, metrics: ESGMetrics) -> Optional[float]:
        """根据规则计算分数

        Args:
            value: 指标值
            rule: 评分规则
            metrics: 完整的ESGMetrics对象（用于复合指标计算）

        Returns:
            计算后的分数
        """
        rule_type = rule.get("type")

        if rule_type == "direct":
            return min(rule.get("max", 100), float(value))

        elif rule_type == "ratio":
            return min(rule.get("max", 100), float(value) * 100)

        elif rule_type == "inverse":
            excellent = rule.get("excellent", 0)
            poor = rule.get("poor", 100)
            if value <= excellent:
                return 100.0
            if value >= poor:
                return 0.0
            return 100.0 * (1 - (value - excellent) / (poor - excellent))

        elif rule_type == "benchmark":
            benchmark = rule.get("benchmark", 100)
            return min(100.0, float(value) / benchmark * 100)

        elif rule_type == "boolean":
            return 100.0 if value else 0.0

        elif rule_type == "range":
            # 简化处理：0-1范围的比例
            if value >= 0.8:
                return 100.0
            if value <= 0.4:
                return 0.0
            return 100.0 * (value - 0.4) / 0.4

        elif rule_type == "threshold":
            ranges = rule.get("ranges", [])
            for threshold, score in ranges:
                if value >= threshold:
                    if threshold == 0:
                        return score
                    return (
                        score + (value - threshold) / threshold * (100 - score)
                        if score < 100
                        else score
                    )
            return 0.0

        elif rule_type == "log_scale":
            import math

            base = rule.get("base", 100)
            factor = rule.get("factor", 20)
            if value > 0:
                return min(100.0, max(0.0, factor * math.log10(value / base)))
            return 0.0

        elif rule_type == "method":
            method_name = rule.get("method")
            if hasattr(value, method_name):
                return getattr(value, method_name)()
            return None

        elif rule_type == "composite":
            # 复合指标在下面专门处理
            return self._calculate_composite_score(value, rule, metrics)

        return None

    def _calculate_composite_score(self, value, rule: dict, metrics: ESGMetrics) -> Optional[float]:
        """计算复合指标分数

        复合指标需要多个字段综合计算。
        """
        indicator_id = None
        for metric_name, ind_id in self.INDICATOR_MAPPING.items():
            if self.INDICATOR_SCORING_RULES.get(ind_id) == rule:
                indicator_id = ind_id
                break

        if indicator_id == "gender_diversity":
            return self._calc_gender_diversity(metrics)
        elif indicator_id == "training_development":
            return self._calc_training_development(metrics)
        elif indicator_id == "safety_performance":
            return self._calc_safety_performance(metrics)
        elif indicator_id in ("ethics_compliance", "anti_corruption"):
            return self._calc_compliance(metrics)
        elif indicator_id == "climate_governance_framework":
            return self._calc_climate_governance(metrics)
        elif indicator_id == "tcfd_disclosure_quality":
            return self._calc_tcfd_disclosure(metrics)

        return None

    def _calc_gender_diversity(self, metrics: ESGMetrics) -> Optional[float]:
        """计算性别多元化综合分数"""
        scores = []
        if metrics.female_ratio is not None:
            fr = metrics.female_ratio
            if fr >= 40:
                scores.append(100.0)
            elif fr >= 35:
                scores.append(80.0 + (fr - 35.0) / 5.0 * 20.0)
            elif fr >= 20:
                scores.append(60.0 + (fr - 20.0) / 15.0 * 20.0)
            else:
                scores.append(max(0.0, fr / 20.0 * 60.0))
        if metrics.female_executive_ratio is not None:
            fer = metrics.female_executive_ratio
            if fer >= 30:
                scores.append(100.0)
            elif fer >= 20:
                scores.append(70.0 + (fer - 20.0) / 10.0 * 30.0)
            elif fer >= 10:
                scores.append(50.0 + (fer - 10.0) / 10.0 * 20.0)
            else:
                scores.append(max(0.0, fer / 10.0 * 50.0))
        return sum(scores) / len(scores) if scores else None

    def _calc_training_development(self, metrics: ESGMetrics) -> Optional[float]:
        """计算培训发展综合分数"""
        scores = []
        if metrics.training_hours is not None:
            scores.append(min(100.0, metrics.training_hours / 40.0 * 100))
        if metrics.training_investment_per_employee is not None:
            scores.append(min(100.0, metrics.training_investment_per_employee / 500.0 * 100))
        return sum(scores) / len(scores) if scores else None

    def _calc_safety_performance(self, metrics: ESGMetrics) -> Optional[float]:
        """计算安全绩效综合分数"""
        scores = []
        if metrics.trir is not None:
            trir = metrics.trir
            if trir <= 0.5:
                scores.append(100.0)
            elif trir >= 3.0:
                scores.append(0.0)
            else:
                scores.append(100.0 * (1 - (trir - 0.5) / 2.5))
        ltifr = metrics.ltifr if metrics.ltifr is not None else metrics.lost_time_injury_rate
        if ltifr is not None:
            if ltifr <= 0.3:
                scores.append(100.0)
            elif ltifr >= 1.8:
                scores.append(0.0)
            else:
                scores.append(100.0 * (1 - (ltifr - 0.3) / 1.5))
        return sum(scores) / len(scores) if scores else None

    def _calc_compliance(self, metrics: ESGMetrics) -> Optional[float]:
        """计算合规培训综合分数"""
        scores = []
        if metrics.ethics_training_coverage is not None:
            scores.append(min(100.0, metrics.ethics_training_coverage / 95.0 * 100))
        if metrics.anti_corruption_training_coverage is not None:
            scores.append(min(100.0, metrics.anti_corruption_training_coverage / 90.0 * 100))
        return sum(scores) / len(scores) if scores else None

    def _calc_climate_governance(self, metrics: ESGMetrics) -> Optional[float]:
        """计算气候治理分数"""
        if not hasattr(metrics, "climate_governance") or not metrics.climate_governance:
            return None
        cg = metrics.climate_governance
        scores = []
        if getattr(cg, "board_climate_committee", False):
            scores.append(100.0)
        else:
            scores.append(0.0)
        if getattr(cg, "exec_comp_linked_to_climate", False):
            scores.append(100.0)
        else:
            scores.append(0.0)
        if getattr(cg, "climate_risk_identification_process", False):
            scores.append(100.0)
        else:
            scores.append(0.0)
        if getattr(cg, "regular_climate_reporting_to_board", False):
            scores.append(100.0)
        else:
            scores.append(0.0)
        return sum(scores) / len(scores)

    def _calc_tcfd_disclosure(self, metrics: ESGMetrics) -> Optional[float]:
        """计算TCFD披露分数"""
        if not hasattr(metrics, "tcfd_disclosure") or not metrics.tcfd_disclosure:
            return None
        tcfd = metrics.tcfd_disclosure
        scores = []
        for attr in [
            "governance_disclosed",
            "strategy_disclosed",
            "risk_management_disclosed",
            "metrics_targets_disclosed",
        ]:
            if getattr(tcfd, attr, False):
                scores.append(100.0)
            else:
                scores.append(0.0)
        return sum(scores) / len(scores)

    def _calculate_priority(self, gap: float) -> str:
        """根据差距计算优先级"""
        if gap >= 15:
            return "高"
        elif gap >= 8:
            return "中"
        else:
            return "低"

    def _calculate_ranking(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """计算在所有标杆中的相对排名"""
        # 计算当前企业总体分数
        current_scores = {
            "E": metrics.get_dimension_score("E"),
            "S": metrics.get_dimension_score("S"),
            "G": metrics.get_dimension_score("G"),
        }
        current_overall = sum(current_scores.values()) / 3

        # 收集所有标杆分数
        all_scores = [("当前企业", current_overall)]
        for company, data in self.benchmark_data.items():
            all_scores.append((company, data.get("overall_score", 0)))

        # 排序
        all_scores.sort(key=lambda x: x[1], reverse=True)

        # 查找排名
        rank = next(i for i, (name, _) in enumerate(all_scores, 1) if name == "当前企业")
        total = len(all_scores)

        return {
            "rank": rank,
            "total": total,
            "percentile": round((total - rank + 1) / total * 100, 1),
            "overall_score": round(current_overall, 1),
        }

    def analyze_historical_trend(self, company_name: str) -> Dict[str, Any]:
        """分析企业历史趋势

        从Mock JSON读取历史数据，返回各维度分数的时间序列。

        Args:
            company_name: 公司名称（"绿色能源集团"/"新能源科技有限公司"/"传统能源企业"）

        Returns:
            {
                "years": ["2022", "2023", "2024"],
                "trends": {
                    "E": [70, 75, 80],
                    "S": [68, 72, 78],
                    "G": [70, 74, 80]
                },
                "overall": [69.3, 73.7, 79.3]
            }
        """
        try:
            with open(HISTORICAL_DATA_PATH, "r", encoding="utf-8") as f:
                historical_data = json.load(f)
        except FileNotFoundError:
            return {"years": [], "trends": {}, "overall": []}
        except json.JSONDecodeError:
            return {"years": [], "trends": {}, "overall": []}

        company_data = historical_data.get(company_name, {})
        if not company_data:
            return {"years": [], "trends": {}, "overall": []}

        years = sorted(company_data.keys())

        trends = {"E": [], "S": [], "G": []}
        overall = []

        for year in years:
            year_data = company_data[year]
            trends["E"].append(year_data.get("E", 0))
            trends["S"].append(year_data.get("S", 0))
            trends["G"].append(year_data.get("G", 0))
            overall.append(year_data.get("overall", 0))

        return {"years": years, "trends": trends, "overall": overall}

    def predict_next_year(self, historical_trend: Dict[str, Any]) -> Dict[str, Any]:
        """基于简单线性回归预测下一年数据

        使用(2024-2023)的差值外推2025年预测值。

        Args:
            historical_trend: analyze_historical_trend返回的历史数据

        Returns:
            {
                "year": "2025",
                "predicted": {"E": 85, "S": 82, "G": 84},
                "overall": 83.7
            }
        """
        # 输入参数验证
        if not isinstance(historical_trend, dict):
            return {"year": "2025", "predicted": {}, "overall": 0}

        years = historical_trend.get("years", [])
        trends = historical_trend.get("trends", {})
        overall = historical_trend.get("overall", [])

        # 边界条件检查：至少需要两年数据才能预测
        if len(years) < 2:
            return {"year": "2025", "predicted": {}, "overall": 0}

        # 计算最近两年的差值
        def predict_dimension(values):
            """预测单个维度的下一年数值

            Args:
                values: 历史数值列表

            Returns:
                预测值，范围在0-100之间
            """
            # 边界条件检查
            if not isinstance(values, (list, tuple)) or len(values) == 0:
                return 0

            if len(values) >= 2:
                # 计算最近两年的差值
                diff = values[-1] - values[-2]
                predicted = values[-1] + diff
                # 限制在0-100范围内（边界检查）
                return max(0.0, min(100.0, predicted))

            # 只有一年数据时，直接返回该值
            return float(values[-1]) if values else 0.0

        predicted = {
            "E": predict_dimension(trends.get("E", [])),
            "S": predict_dimension(trends.get("S", [])),
            "G": predict_dimension(trends.get("G", [])),
        }

        predicted_overall = predict_dimension(overall)

        return {"year": "2025", "predicted": predicted, "overall": round(predicted_overall, 1)}
