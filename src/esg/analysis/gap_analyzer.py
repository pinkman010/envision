"""差距分析器

对标行业标杆，计算维度差距和指标差距。
简化版：只计算差距值，返回差距等级，不生成策略建议。
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.esg.config import DEFAULT_SCORE, ESG_DIMENSION_NAMES, MOCK_DATA_DIR
from src.esg.core.models import ESGMetrics


class GapLevel(Enum):
    """差距等级"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class GapResult:
    """维度差距分析结果"""

    dimension: str
    current: float
    benchmark: float
    gap: float
    gap_percentage: float
    level: GapLevel


@dataclass
class IndicatorGap:
    """指标差距"""

    indicator_id: str
    indicator_name: str
    current_score: float
    benchmark_score: float
    gap: float
    level: GapLevel


class BenchmarkRepository(ABC):
    """标杆数据仓库抽象基类"""

    @abstractmethod
    def load_data(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        pass

    @abstractmethod
    def get_available_companies(self) -> List[str]:
        pass

    @abstractmethod
    def get_benchmark(self, company: str) -> Optional[Dict[str, Any]]:
        pass


class JsonBenchmarkRepository(BenchmarkRepository):
    """JSON文件标杆数据仓库"""

    DEFAULT_BENCHMARK_DATA = {
        "companies": {
            "行业平均": {
                "overall_score": 70.0,
                "dimensions": {"E": 68.0, "S": 70.0, "G": 72.0},
                "indicators": {
                    "renewable_energy": {"score": 65.0},
                    "carbon_emissions": {"score": 68.0},
                    "employee_diversity": {"score": 72.0},
                    "board_independence": {"score": 75.0},
                },
            },
            "维斯塔斯": {
                "overall_score": 88.0,
                "dimensions": {"E": 90.0, "S": 85.0, "G": 89.0},
                "indicators": {
                    "renewable_energy": {"score": 95.0},
                    "carbon_emissions": {"score": 90.0},
                    "employee_diversity": {"score": 82.0},
                    "board_independence": {"score": 90.0},
                },
            },
            "西门子歌美飒": {
                "overall_score": 85.0,
                "dimensions": {"E": 87.0, "S": 82.0, "G": 86.0},
                "indicators": {
                    "renewable_energy": {"score": 92.0},
                    "carbon_emissions": {"score": 88.0},
                    "employee_diversity": {"score": 80.0},
                    "board_independence": {"score": 88.0},
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
        self.data_source = data_source or (MOCK_DATA_DIR / "benchmark_data.json")
        self._benchmark_data: Dict[str, Any] = {}
        self._indicator_names: Dict[str, str] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            if self.data_source.exists():
                with open(self.data_source, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._benchmark_data = data.get("companies", {})
                self._indicator_names = data.get("indicator_names", {})
            else:
                self._benchmark_data = self.DEFAULT_BENCHMARK_DATA["companies"]
                self._indicator_names = self.DEFAULT_BENCHMARK_DATA["indicator_names"]
        except (FileNotFoundError, json.JSONDecodeError):
            self._benchmark_data = self.DEFAULT_BENCHMARK_DATA["companies"]
            self._indicator_names = self.DEFAULT_BENCHMARK_DATA["indicator_names"]

    def load_data(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        return self._benchmark_data, self._indicator_names

    def get_available_companies(self) -> List[str]:
        return list(self._benchmark_data.keys())

    def get_benchmark(self, company: str) -> Optional[Dict[str, Any]]:
        return self._benchmark_data.get(company)


class GapAnalyzer:
    """ESG差距分析器（简化版）

    对标行业标杆企业，计算维度差距和指标差距。
    简化后功能：只计算差距值，返回差距等级，不生成策略建议。
    """

    # 差距阈值配置
    GAP_THRESHOLDS = {
        "HIGH": 15.0,  # 差距 >= 15 为高
        "MEDIUM": 8.0,  # 8 <= 差距 < 15 为中
        "LOW": 0.0,  # 差距 < 8 为低
    }

    def __init__(
        self, repository: Optional[BenchmarkRepository] = None, data_source: Optional[Path] = None
    ):
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
            gap_percentage = (gap / target * 100) if target > 0 else 0.0
            level = self._calculate_gap_level(gap)

            results[dim] = GapResult(
                dimension=dim,
                current=round(current, 1),
                benchmark=round(target, 1),
                gap=round(gap, 1),
                gap_percentage=round(gap_percentage, 1),
                level=level,
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

            gap = bench_score - current_score
            level = self._calculate_gap_level(gap)

            results.append(
                IndicatorGap(
                    indicator_id=indicator_id,
                    indicator_name=self.indicator_names.get(indicator_id, indicator_id),
                    current_score=round(current_score, 1),
                    benchmark_score=round(bench_score, 1),
                    gap=round(gap, 1),
                    level=level,
                )
            )

        # 按差距从大到小排序
        results.sort(key=lambda x: abs(x.gap), reverse=True)
        return results

    def get_available_benchmarks(self) -> List[str]:
        """获取可用的标杆企业列表"""
        return self.repository.get_available_companies()

    def _calculate_gap_level(self, gap: float) -> GapLevel:
        """根据差距值计算差距等级

        Args:
            gap: 差距值

        Returns:
            差距等级：高/中/低
        """
        abs_gap = abs(gap)
        if abs_gap >= self.GAP_THRESHOLDS["HIGH"]:
            return GapLevel.HIGH
        elif abs_gap >= self.GAP_THRESHOLDS["MEDIUM"]:
            return GapLevel.MEDIUM
        else:
            return GapLevel.LOW

    def _calculate_indicator_scores(self, metrics: ESGMetrics) -> Dict[str, float]:
        """计算各项指标分数（简化版）"""
        scores = {}

        # 简单的直接映射
        indicator_mapping = {
            "renewable_energy": (
                metrics.renewable_energy_ratio * 100 if metrics.renewable_energy_ratio else None
            ),
            "carbon_emissions": (
                min(100, (metrics.carbon_emissions or 0) / 1000)
                if metrics.carbon_emissions
                else None
            ),
            "employee_diversity": metrics.female_ratio * 100 if metrics.female_ratio else None,
            "board_independence": (
                metrics.board_independence_ratio * 100 if metrics.board_independence_ratio else None
            ),
        }

        for indicator_id, value in indicator_mapping.items():
            if value is not None:
                scores[indicator_id] = max(0, min(100, value))

        return scores
