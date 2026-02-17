"""
ESG 指标提取器模块（简化版）

使用正则表达式从文本中提取 ESG 相关指标数据。
简化版：只保留正则表达式模式匹配，核心指标提取（碳排放、能源、员工等）。
复杂提取逻辑已移除，复杂提取通过llm模块处理。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Pattern

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型枚举"""

    ENVIRONMENT = "E"
    SOCIAL = "S"
    GOVERNANCE = "G"


@dataclass
class ExtractedMetric:
    """提取的指标数据类"""

    name: str
    value: float
    unit: str = ""
    confidence: float = 0.0
    source: str = ""
    metric_type: MetricType = MetricType.ENVIRONMENT


class MetricExtractor:
    """ESG 指标提取器（简化版）

    使用正则表达式从文本中提取 ESG 相关指标数据。
    简化后功能：正则提取基础指标，复杂提取通过llm模块处理。

    支持提取的指标：
    - 碳排放、能源相关（E维度）
    - 员工相关（S维度）
    - 治理相关（G维度）
    """

    # 简化的指标模式定义 - 只保留核心指标
    PATTERNS: Dict[str, Dict[str, Any]] = {
        # ===== 环境指标 (E) =====
        "carbon_emissions": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"(?:carbon|温室气体|二氧化碳|碳)排放[量]?[：:\s]*([0-9,]+\.?\d*)\s*(?:吨|t|万吨|kt)",
                r"CO2.*?(?:排放)?[：:\s]*([0-9,]+\.?\d*)\s*(?:吨|t)",
            ],
            "unit": "吨",
            "multiplier": 1.0,
        },
        "renewable_energy_ratio": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"可再生能源.*?[占比率]?[：:\s]*([0-9.]+)\s*%",
                r"绿电.*?[占比]?[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        "energy_efficiency": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"能源效率[：:\s]*([0-9.]+)",
            ],
            "unit": "",
            "multiplier": 1.0,
        },
        "water_consumption": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"用?水[量]?[：:\s]*([0-9,]+\.?\d*)\s*(?:立方米|m3|吨|t)",
            ],
            "unit": "立方米",
            "multiplier": 1.0,
        },
        "waste_recycling_rate": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"废弃物回收率[：:\s]*([0-9.]+)\s*%",
                r"垃圾回收率[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        # ===== 社会指标 (S) =====
        "employee_count": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"员工[总]?数[：:\s]*([0-9,]+)",
                r"employees?[：:\s]*([0-9,]+)",
            ],
            "unit": "人",
            "multiplier": 1.0,
            "is_integer": True,
        },
        "female_ratio": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"女性员工[占比率]?[：:\s]*([0-9.]+)\s*%",
                r"女性[占占比]?[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        "training_hours": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"培训.*?小时[数]?[：:\s]*([0-9,]+\.?\d*)",
                r"人均培训[：:\s]*([0-9,]+\.?\d*)\s*小时",
            ],
            "unit": "小时",
            "multiplier": 1.0,
        },
        # ===== 治理指标 (G) =====
        "board_independence_ratio": {
            "type": MetricType.GOVERNANCE,
            "patterns": [
                r"独立董事[占比率]?[：:\s]*([0-9.]+)\s*%",
                r"independent\s+directors?[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        "ethics_training_coverage": {
            "type": MetricType.GOVERNANCE,
            "patterns": [
                r"道德培训覆盖率[：:\s]*([0-9.]+)\s*%",
                r"合规培训覆盖率[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        "esg_report_quality": {
            "type": MetricType.GOVERNANCE,
            "patterns": [
                r"报告质量[评分]?[：:\s]*([0-9.]+)",
            ],
            "unit": "分",
            "multiplier": 1.0,
        },
    }

    def __init__(self, custom_patterns: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """初始化指标提取器

        Args:
            custom_patterns: 自定义指标模式，用于扩展或覆盖默认模式
        """
        self.patterns = self.PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)

        # 编译正则表达式以提高性能
        self._compiled_patterns: Dict[str, List[Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """编译所有正则表达式模式"""
        for metric_name, config in self.patterns.items():
            compiled = []
            for pattern in config.get("patterns", []):
                try:
                    compiled.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"模式编译失败 [{metric_name}]: {e}")
            self._compiled_patterns[metric_name] = compiled

    def extract(
        self, text: str, company: str = "未知", year: str = "", confidence_threshold: float = 0.0
    ) -> Dict[str, ExtractedMetric]:
        """从文本中提取 ESG 指标（简化接口）

        Args:
            text: 待提取的文本内容
            company: 公司名称
            year: 报告年份
            confidence_threshold: 置信度阈值，低于此值的指标将被过滤

        Returns:
            Dict[str, ExtractedMetric]: 提取的指标字典
        """
        if not text or not isinstance(text, str):
            logger.warning("输入文本为空或类型错误")
            return {}

        results = {}

        for metric_name, config in self.patterns.items():
            try:
                metric = self._extract_single_metric(text, metric_name, config)
                if metric and metric.confidence >= confidence_threshold:
                    results[metric_name] = metric
            except Exception as e:
                logger.warning(f"提取指标 [{metric_name}] 时出错: {e}")

        return results

    def _extract_single_metric(
        self, text: str, metric_name: str, config: Dict[str, Any]
    ) -> Optional[ExtractedMetric]:
        """提取单个指标"""
        compiled_patterns = self._compiled_patterns.get(metric_name, [])

        for pattern in compiled_patterns:
            for match in pattern.finditer(text):
                try:
                    raw_value = match.group(1).replace(",", "")
                    value = float(raw_value)

                    # 应用乘数
                    multiplier = config.get("multiplier", 1.0)
                    value *= multiplier

                    # 整数类型转换
                    if config.get("is_integer", False):
                        value = int(value)

                    # 归一化（如百分比大于 1 则除以 100）
                    if value > 1 and config.get("unit") == "%":
                        value /= 100

                    # 计算置信度
                    confidence = self._calculate_confidence(match)

                    return ExtractedMetric(
                        name=metric_name,
                        value=value,
                        unit=config.get("unit", ""),
                        confidence=confidence,
                        source=match.group(0)[:200],
                        metric_type=config.get("type", MetricType.ENVIRONMENT),
                    )

                except (ValueError, IndexError):
                    continue

        return None

    def _calculate_confidence(self, match: Any) -> float:
        """计算匹配的置信度"""
        matched_text = match.group(0)
        base_confidence = 0.6

        # 匹配文本越长，置信度越高
        length_bonus = min(len(matched_text) / 50, 0.2)

        # 检查是否有明确的单位
        unit_bonus = (
            0.1 if any(unit in matched_text for unit in ["吨", "%", "人", "小时", "元"]) else 0
        )

        confidence = base_confidence + length_bonus + unit_bonus
        return min(confidence, 1.0)
