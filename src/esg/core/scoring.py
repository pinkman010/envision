"""ESG评分计算器

提供ESG各维度指标的评分计算功能。
"""

from typing import Dict, List, Optional

from src.esg.core.constants import (
    BATTERY_CYCLE_LIFE_BENCHMARK,
    BATTERY_RECYCLING_RATE_BENCHMARK,
    BIODIVERSITY_IMPACT_BENCHMARK,
    CARBON_INTENSITY_BENCHMARK_HIGH,
    CARBON_INTENSITY_BENCHMARK_LOW,
    COMMUNITY_INVESTMENT_MAX,
    DEFAULT_SCORE,
    ELECTROLYSIS_EFFICIENCY_BENCHMARK,
    ENERGY_STORAGE_SAFETY_BENCHMARK,
    SCORE_MAX,
    TRAINING_HOURS_MAX,
    TURBINE_AVAILABILITY_BENCHMARK,
    WATER_INTENSITY_BENCHMARK_HIGH,
    WATER_INTENSITY_BENCHMARK_LOW,
)


class ScoreCalculator:
    """ESG评分计算器

    提供各种ESG指标的评分计算方法，支持自定义阈值和基准。
    """

    @staticmethod
    def calculate_carbon_intensity_score(intensity: Optional[float]) -> Optional[float]:
        """计算碳强度得分（越低越好）

        使用反向计分：碳强度越低得分越高

        Args:
            intensity: 碳强度（吨CO2e/万元营收）

        Returns:
            碳强度得分(0-100)或None
        """
        if intensity is None:
            return None

        # 低于优秀阈值得满分
        if intensity <= CARBON_INTENSITY_BENCHMARK_LOW:
            return SCORE_MAX
        # 高于较差阈值得0分
        if intensity >= CARBON_INTENSITY_BENCHMARK_HIGH:
            return 0.0

        # 线性插值计算得分
        ratio = (intensity - CARBON_INTENSITY_BENCHMARK_LOW) / (
            CARBON_INTENSITY_BENCHMARK_HIGH - CARBON_INTENSITY_BENCHMARK_LOW
        )
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def calculate_water_intensity_score(intensity: Optional[float]) -> Optional[float]:
        """计算水资源强度得分（越低越好）

        Args:
            intensity: 水资源强度（立方米/万元营收）

        Returns:
            水资源强度得分(0-100)或None
        """
        if intensity is None:
            return None

        # 低于优秀阈值得满分
        if intensity <= WATER_INTENSITY_BENCHMARK_LOW:
            return SCORE_MAX
        # 高于较差阈值得0分
        if intensity >= WATER_INTENSITY_BENCHMARK_HIGH:
            return 0.0

        # 线性插值
        ratio = (intensity - WATER_INTENSITY_BENCHMARK_LOW) / (
            WATER_INTENSITY_BENCHMARK_HIGH - WATER_INTENSITY_BENCHMARK_LOW
        )
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def safe_score(
        value: Optional[float], max_val: float = SCORE_MAX, multiplier: float = 1.0
    ) -> Optional[float]:
        """安全地计算分数

        Args:
            value: 原始值
            max_val: 最大值限制
            multiplier: 乘数

        Returns:
            计算后的分数或None
        """
        if value is None:
            return None
        if multiplier != 1.0:
            return min(value * multiplier, max_val)
        return min(value, max_val)

    @staticmethod
    def calculate_percentage_score(value: Optional[float]) -> Optional[float]:
        """计算百分比得分（原始值即为百分比）

        Args:
            value: 百分比值（0-100）

        Returns:
            得分或None
        """
        if value is None:
            return None
        return min(value, SCORE_MAX)

    @staticmethod
    def calculate_dimension_scores(self, metrics, dimension: str) -> List[Optional[float]]:
        """计算指定维度的所有指标得分

        Args:
            metrics: ESGMetrics对象
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            得分列表
        """
        scores: List[Optional[float]] = []

        if dimension == "E":
            # 环境维度评分
            scores = [
                # 碳强度（越低越好）
                self.calculate_carbon_intensity_score(metrics.carbon_intensity),
                # 可再生能源比例
                self.safe_score(metrics.renewable_energy_ratio, SCORE_MAX),
                # 能源效率
                self.safe_score(metrics.energy_efficiency, SCORE_MAX),
                # 废弃物回收率
                self.safe_score(metrics.waste_recycling_rate, SCORE_MAX),
                # 水资源强度（越低越好）
                self.calculate_water_intensity_score(metrics.water_intensity),
                # 生物多样性影响评分
                self.safe_score(metrics.biodiversity_impact_score, SCORE_MAX),
                # 新能源特色指标
                self.safe_score(
                    metrics.turbine_availability,
                    SCORE_MAX,
                    multiplier=SCORE_MAX / TURBINE_AVAILABILITY_BENCHMARK,
                ),
                self.safe_score(
                    metrics.battery_cycle_life,
                    SCORE_MAX,
                    multiplier=SCORE_MAX / BATTERY_CYCLE_LIFE_BENCHMARK,
                ),
                self.safe_score(metrics.battery_recycling_rate, SCORE_MAX),
                self.safe_score(
                    metrics.electrolysis_efficiency,
                    SCORE_MAX,
                    multiplier=SCORE_MAX / ELECTROLYSIS_EFFICIENCY_BENCHMARK,
                ),
                self.safe_score(metrics.energy_storage_safety_score, SCORE_MAX),
            ]
        elif dimension == "S":
            scores = [
                self.safe_score(metrics.female_ratio, SCORE_MAX, multiplier=SCORE_MAX),
                self.safe_score(
                    metrics.training_hours,
                    TRAINING_HOURS_MAX,
                    multiplier=SCORE_MAX / TRAINING_HOURS_MAX,
                ),
                self.safe_score(
                    metrics.community_investment,
                    COMMUNITY_INVESTMENT_MAX,
                    multiplier=SCORE_MAX / COMMUNITY_INVESTMENT_MAX,
                ),
            ]
        elif dimension == "G":
            scores = [
                self.safe_score(metrics.board_independence_ratio, SCORE_MAX),
                self.safe_score(metrics.ethics_training_coverage, SCORE_MAX),
                self.safe_score(metrics.esg_report_quality, SCORE_MAX),
            ]

        return scores

    @staticmethod
    def calculate_dimension_score(self, metrics, dimension: str) -> float:
        """计算指定维度的综合得分

        Args:
            metrics: ESGMetrics对象
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            维度得分 (0-100)
        """
        scores = self.calculate_dimension_scores(self, metrics, dimension)

        valid_scores = [s for s in scores if s is not None]
        if not valid_scores:
            return DEFAULT_SCORE

        return sum(valid_scores) / len(valid_scores)


# 全局评分计算器实例
_calculator = ScoreCalculator()


def get_score_calculator() -> ScoreCalculator:
    """获取全局评分计算器实例"""
    return _calculator


def calculate_carbon_intensity_score(intensity: Optional[float]) -> Optional[float]:
    """便捷函数：计算碳强度得分"""
    return _calculator.calculate_carbon_intensity_score(intensity)


def calculate_water_intensity_score(intensity: Optional[float]) -> Optional[float]:
    """便捷函数：计算水资源强度得分"""
    return _calculator.calculate_water_intensity_score(intensity)
