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
    INDICATOR_MAPPING = {
        "renewable_energy_ratio": "renewable_energy",
        "carbon_emissions": "carbon_emissions",
        "female_ratio": "employee_diversity",
        "board_independence_ratio": "board_independence",
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

    def _calculate_indicator_scores(self, metrics: ESGMetrics) -> Dict[str, float]:
        """计算各项指标分数"""
        scores = {}

        # 环境指标
        if metrics.renewable_energy_ratio is not None:
            scores["renewable_energy"] = metrics.renewable_energy_ratio
        if metrics.carbon_emissions is not None:
            # 碳排放分数：假设排放越低越好，基于行业基准反推
            scores["carbon_emissions"] = max(0, 100 - metrics.carbon_emissions / 10000)

        # 社会指标
        if metrics.female_ratio is not None:
            scores["employee_diversity"] = metrics.female_ratio * 100

        # 治理指标
        if metrics.board_independence_ratio is not None:
            scores["board_independence"] = metrics.board_independence_ratio * 100

        return scores

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
