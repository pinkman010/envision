"""
ESG 指标提取器模块

使用正则表达式从文本中提取 ESG 相关指标数据
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Pattern, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型枚举"""

    ENVIRONMENT = "E"  # 环境指标
    SOCIAL = "S"  # 社会指标
    GOVERNANCE = "G"  # 治理指标


@dataclass
class ExtractedMetric:
    """提取的指标数据类

    Attributes:
        name: 指标名称
        value: 提取的数值
        unit: 单位
        confidence: 置信度 (0-1)
        source: 原始文本片段
        metric_type: 指标类型
    """

    name: str
    value: float
    unit: str = ""
    confidence: float = 0.0
    source: str = ""
    metric_type: MetricType = MetricType.ENVIRONMENT


@dataclass
class ESGMetricsResult:
    """ESG 指标提取结果类

    Attributes:
        company_name: 公司名称
        year: 报告年份
        metrics: 提取的指标字典
        extraction_time: 提取时间
        warnings: 警告信息列表
    """

    company_name: str
    year: str
    metrics: Dict[str, ExtractedMetric] = field(default_factory=dict)
    extraction_time: str = field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )
    warnings: List[str] = field(default_factory=list)

    def get_metric(self, name: str) -> Optional[ExtractedMetric]:
        """获取指定名称的指标"""
        return self.metrics.get(name)

    def get_by_type(self, metric_type: MetricType) -> Dict[str, ExtractedMetric]:
        """获取指定类型的所有指标"""
        return {k: v for k, v in self.metrics.items() if v.metric_type == metric_type}

    def get_overall_confidence(self) -> float:
        """计算整体置信度"""
        if not self.metrics:
            return 0.0
        return sum(m.confidence for m in self.metrics.values()) / len(self.metrics)


class MetricExtractionError(Exception):
    """指标提取异常基类"""

    pass


class MetricExtractor:
    """ESG 指标提取器

    使用正则表达式从文本中提取 ESG 相关指标数据。
    支持碳排放、可再生能源占比、员工数、女性比例等多种指标。

    Example:
        >>> extractor = MetricExtractor()
        >>> result = extractor.extract(text, company="小米", year="2023")
        >>> print(result.metrics["carbon_emissions"].value)
    """

    # 指标模式定义
    PATTERNS: Dict[str, Dict[str, Any]] = {
        # 环境指标 (E)
        "carbon_emissions": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"(?:carbon|温室气体|二氧化碳|碳)排放[量]?[：:\s]*([0-9,]+\.?\d*)\s*(?:吨|t|万吨|kt)",
                r"(?:Scope|范围)\s*[123].*?排放[：:\s]*([0-9,]+\.?\d*)\s*(?:吨|t)",
                r"CO2.*?(?:排放)?[：:\s]*([0-9,]+\.?\d*)\s*(?:吨|t)",
            ],
            "unit": "吨",
            "multiplier": 1.0,
        },
        "renewable_energy_ratio": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"可再生能源.*?[占占比率]?[：:\s]*([0-9.]+)\s*%",
                r"绿电.*?[占比]?[：:\s]*([0-9.]+)\s*%",
                r"renewable.*?energy.*?ratio[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        "energy_efficiency": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"能源效率[：:\s]*([0-9.]+)",
                r"energy\s+efficiency[：:\s]*([0-9.]+)",
            ],
            "unit": "",
            "multiplier": 1.0,
        },
        "water_consumption": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"用?水[量]?[：:\s]*([0-9,]+\.?\d*)\s*(?:立方米|m3|吨|t)",
                r"water\s+consumption[：:\s]*([0-9,]+\.?\d*)",
            ],
            "unit": "立方米",
            "multiplier": 1.0,
        },
        "waste_recycling_rate": {
            "type": MetricType.ENVIRONMENT,
            "patterns": [
                r"废弃物回收率[：:\s]*([0-9.]+)\s*%",
                r"垃圾回收率[：:\s]*([0-9.]+)\s*%",
                r"waste.*?recycling[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
        },
        # 社会指标 (S)
        "employee_count": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"(?:total|over)?\s*员工[总]?数[：:\s]*([0-9,]+)",
                r"employees?[：:\s]*([0-9,]+)",
                r"员工[总]?数[约]*[：:\s]*([0-9,]+)",
                r"在职员工.*?([0-9,]+)",
                r"全职员工.*?([0-9,]+)",
            ],
            "unit": "人",
            "multiplier": 1.0,
            "is_integer": True,
        },
        "female_ratio": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"女性员工[占占比率]?[：:\s]*([0-9.]+)\s*%",
                r"female.*?employees?[：:\s]*([0-9.]+)\s*%",
                r"女性[占占比]?[：:\s]*([0-9.]+)\s*%",
                r"女员工[占占比]?[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
            "normalize": True,  # 大于 1 时除以 100
        },
        "training_hours": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"培训.*?小时[数]?[：:\s]*([0-9,]+\.?\d*)",
                r"人均培训[：:\s]*([0-9,]+\.?\d*)\s*小时",
                r"training\s+hours[：:\s]*([0-9,]+\.?\d*)",
            ],
            "unit": "小时",
            "multiplier": 1.0,
        },
        "safety_incidents": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"安全事故[数]?[：:\s]*([0-9]+)",
                r"工伤事故[：:\s]*([0-9]+)",
                r"safety\s+incidents?[：:\s]*([0-9]+)",
            ],
            "unit": "起",
            "multiplier": 1.0,
            "is_integer": True,
        },
        "community_investment": {
            "type": MetricType.SOCIAL,
            "patterns": [
                r"社区投资[：:\s]*([0-9,]+\.?\d*)\s*(?:万元|百万元|亿元)?",
                r"公益捐赠[：:\s]*([0-9,]+\.?\d*)\s*(?:万元|百万元|亿元)?",
                r"community\s+investment[：:\s]*([0-9,]+\.?\d*)",
            ],
            "unit": "元",
            "multiplier": 1.0,
        },
        # 治理指标 (G)
        "board_independence_ratio": {
            "type": MetricType.GOVERNANCE,
            "patterns": [
                r"独立董事[占占比率]?[：:\s]*([0-9.]+)\s*%",
                r"independent\s+directors?[：:\s]*([0-9.]+)\s*%",
                r"独董[占占比]?[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
            "normalize": True,
        },
        "ethics_training_coverage": {
            "type": MetricType.GOVERNANCE,
            "patterns": [
                r"道德培训覆盖率[：:\s]*([0-9.]+)\s*%",
                r"合规培训覆盖率[：:\s]*([0-9.]+)\s*%",
                r"ethics\s+training[：:\s]*([0-9.]+)\s*%",
            ],
            "unit": "%",
            "multiplier": 0.01,
            "normalize": True,
        },
        "esg_report_quality": {
            "type": MetricType.GOVERNANCE,
            "patterns": [
                r"报告质量[评分]?[：:\s]*([0-9.]+)",
                r"report\s+quality[：:\s]*([0-9.]+)",
            ],
            "unit": "",
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
    ) -> ESGMetricsResult:
        """从文本中提取 ESG 指标

        Args:
            text: 待提取的文本内容
            company: 公司名称
            year: 报告年份
            confidence_threshold: 置信度阈值，低于此值的指标将被过滤

        Returns:
            ESGMetricsResult: 提取结果对象

        Raises:
            MetricExtractionError: 当提取过程发生严重错误时
        """
        if not text or not isinstance(text, str):
            raise MetricExtractionError("输入文本不能为空且必须是字符串")

        result = ESGMetricsResult(company_name=company, year=year)

        for metric_name, config in self.patterns.items():
            try:
                metric = self._extract_single_metric(text, metric_name, config)
                if metric and metric.confidence >= confidence_threshold:
                    result.metrics[metric_name] = metric
            except Exception as e:
                logger.warning(f"提取指标 [{metric_name}] 时出错: {e}")
                result.warnings.append(f"{metric_name}: {e}")

        return result

    def _extract_single_metric(
        self, text: str, metric_name: str, config: Dict[str, Any]
    ) -> Optional[ExtractedMetric]:
        """提取单个指标

        Args:
            text: 待提取的文本
            metric_name: 指标名称
            config: 指标配置

        Returns:
            Optional[ExtractedMetric]: 提取的指标，失败返回 None
        """
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
                    if config.get("normalize", False) and value > 1:
                        value /= 100

                    # 计算置信度
                    confidence = self._calculate_confidence(match, metric_name)

                    return ExtractedMetric(
                        name=metric_name,
                        value=value,
                        unit=config.get("unit", ""),
                        confidence=confidence,
                        source=match.group(0)[:200],  # 限制长度
                        metric_type=config.get("type", MetricType.ENVIRONMENT),
                    )

                except (ValueError, IndexError) as e:
                    continue

        return None

    def _calculate_confidence(self, match: Any, metric_name: str) -> float:
        """计算匹配的置信度

        基于匹配文本的长度、上下文等因素计算置信度

        Args:
            match: 正则匹配对象
            metric_name: 指标名称

        Returns:
            float: 置信度 (0-1)
        """
        matched_text = match.group(0)
        base_confidence = 0.5

        # 匹配文本越长，置信度越高（最多增加 0.3）
        length_bonus = min(len(matched_text) / 50, 0.3)

        # 检查是否有明确的单位
        unit_bonus = (
            0.1 if any(unit in matched_text for unit in ["吨", "%", "人", "小时", "元"]) else 0
        )

        # 检查是否有明确的数值格式
        number_bonus = 0.1 if re.search(r"\d{1,3}(,\d{3})+\.?\d*", matched_text) else 0

        confidence = base_confidence + length_bonus + unit_bonus + number_bonus
        return min(confidence, 1.0)

    def extract_batch(
        self, texts: List[Tuple[str, str, str]], confidence_threshold: float = 0.0
    ) -> List[ESGMetricsResult]:
        """批量提取多个文本的 ESG 指标

        Args:
            texts: 元组列表 (text, company, year)
            confidence_threshold: 置信度阈值

        Returns:
            List[ESGMetricsResult]: 提取结果列表
        """
        results = []
        for text, company, year in texts:
            try:
                result = self.extract(text, company, year, confidence_threshold)
                results.append(result)
            except MetricExtractionError as e:
                logger.error(f"批量提取失败 [{company} {year}]: {e}")
                # 创建一个空的结果
                results.append(ESGMetricsResult(company_name=company, year=year, warnings=[str(e)]))
        return results

    def add_custom_pattern(
        self,
        name: str,
        patterns: List[str],
        metric_type: MetricType,
        unit: str = "",
        multiplier: float = 1.0,
        **kwargs,
    ) -> None:
        """添加自定义指标模式

        Args:
            name: 指标名称
            patterns: 正则表达式模式列表
            metric_type: 指标类型
            unit: 单位
            multiplier: 数值乘数
            **kwargs: 其他配置参数
        """
        config = {
            "type": metric_type,
            "patterns": patterns,
            "unit": unit,
            "multiplier": multiplier,
        }
        config.update(kwargs)

        self.patterns[name] = config

        # 编译新模式
        compiled = []
        for pattern in patterns:
            try:
                compiled.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"自定义模式编译失败 [{name}]: {e}")
        self._compiled_patterns[name] = compiled
