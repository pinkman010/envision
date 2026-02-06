"""数据补全引擎

提供 ESG 指标缺失值补全功能，支持基于行业基准、历史数据和规则推理的补全策略。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from src.core.models import ESGMetrics, BenchmarkData
from src.config import DEFAULT_SCORE


@dataclass
class CompletionLog:
    """补全日志条目"""
    field_name: str                    # 补全的字段名
    original_value: Optional[Any]      # 原始值（None表示缺失）
    completed_value: Any               # 补全后的值
    method: str                        # 补全方法: "benchmark", "historical", "inference", "default"
    confidence: float                  # 置信度 0-1
    reason: str                        # 补全原因说明
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CompletionResult:
    """数据补全结果"""
    metrics: ESGMetrics                  # 补全后的指标数据
    logs: List[CompletionLog]            # 补全日志列表
    completion_rate: float               # 补全率
    overall_confidence: float            # 整体置信度


class DataCompletionEngine:
    """ESG数据补全引擎
    
    用于补全缺失的 ESG 指标数据，支持多种补全策略：
    - 行业基准补全: 基于行业平均水平
    - 历史趋势补全: 基于历史数据趋势
    - 规则推理补全: 基于相关指标推算
    - 默认值补全: 使用预设默认值
    
    Attributes:
        benchmark_data: 行业基准数据
        historical_data: 历史数据字典 {年份: ESGMetrics}
        default_values: 默认补全值配置
    """
    
    # 默认补全值配置
    DEFAULT_VALUES = {
        # 环境指标默认值
        "carbon_emissions": 50000.0,
        "renewable_energy_ratio": 30.0,
        "energy_efficiency": 70.0,
        "water_consumption": 100000.0,
        "waste_recycling_rate": 60.0,
        # 社会指标默认值
        "employee_count": 5000,
        "female_ratio": 40.0,
        "training_hours": 20.0,
        "safety_incidents": 0,
        "community_investment": 1000000.0,
        # 治理指标默认值
        "board_independence_ratio": 60.0,
        "ethics_training_coverage": 80.0,
        "esg_report_quality": 70.0,
    }
    
    # 字段与 ESG 维度的映射
    DIMENSION_MAP = {
        "E": ["carbon_emissions", "renewable_energy_ratio", "energy_efficiency", 
              "water_consumption", "waste_recycling_rate"],
        "S": ["employee_count", "female_ratio", "training_hours", 
              "safety_incidents", "community_investment"],
        "G": ["board_independence_ratio", "ethics_training_coverage", "esg_report_quality"]
    }
    
    def __init__(
        self,
        benchmark_data: Optional[BenchmarkData] = None,
        historical_data: Optional[Dict[str, ESGMetrics]] = None,
        default_values: Optional[Dict[str, Any]] = None
    ):
        """初始化数据补全引擎
        
        Args:
            benchmark_data: 行业基准数据
            historical_data: 历史数据字典 {年份: ESGMetrics}
            default_values: 自定义默认补全值
        """
        self.benchmark_data = benchmark_data
        self.historical_data = historical_data or {}
        self.default_values = default_values or self.DEFAULT_VALUES.copy()
        self._logs: List[CompletionLog] = []
    
    def complete(
        self, 
        metrics: ESGMetrics,
        target_fields: Optional[List[str]] = None,
        min_confidence: float = 0.5
    ) -> CompletionResult:
        """执行数据补全
        
        对缺失的 ESG 指标进行智能补全，按优先级尝试不同补全策略。
        
        Args:
            metrics: 原始 ESG 指标数据
            target_fields: 指定需要补全的字段列表，None 表示补全所有缺失字段
            min_confidence: 最小置信度阈值，低于此值的补全将被忽略
            
        Returns:
            CompletionResult: 包含补全后数据和日志的结果对象
            
        Example:
            >>> engine = DataCompletionEngine(benchmark_data=benchmark)
            >>> result = engine.complete(metrics)
            >>> print(f"补全率: {result.completion_rate:.1%}")
        """
        self._logs = []
        
        # 确定需要补全的字段
        fields_to_complete = target_fields or self._get_missing_fields(metrics)
        
        # 创建指标的副本用于补全
        completed_metrics = self._copy_metrics(metrics)
        
        for field_name in fields_to_complete:
            current_value = getattr(metrics, field_name)
            
            # 只在值为 None 时进行补全
            if current_value is not None:
                continue
            
            # 按优先级尝试不同补全策略
            completed_value, method, confidence, reason = self._try_complete_field(
                field_name, metrics
            )
            
            # 只接受满足最小置信度的补全
            if confidence >= min_confidence:
                setattr(completed_metrics, field_name, completed_value)
                
                log = CompletionLog(
                    field_name=field_name,
                    original_value=current_value,
                    completed_value=completed_value,
                    method=method,
                    confidence=confidence,
                    reason=reason
                )
                self._logs.append(log)
        
        # 计算统计信息
        completion_rate = len(self._logs) / len(fields_to_complete) if fields_to_complete else 1.0
        overall_confidence = (
            sum(log.confidence for log in self._logs) / len(self._logs) 
            if self._logs else 1.0
        )
        
        return CompletionResult(
            metrics=completed_metrics,
            logs=self._logs.copy(),
            completion_rate=completion_rate,
            overall_confidence=overall_confidence
        )
    
    def _get_missing_fields(self, metrics: ESGMetrics) -> List[str]:
        """获取所有缺失值的字段名列表
        
        Args:
            metrics: ESG 指标数据
            
        Returns:
            缺失值的字段名列表
        """
        all_fields = list(self.DEFAULT_VALUES.keys())
        return [f for f in all_fields if getattr(metrics, f) is None]
    
    def _copy_metrics(self, metrics: ESGMetrics) -> ESGMetrics:
        """创建 ESGMetrics 的深拷贝
        
        Args:
            metrics: 原始指标数据
            
        Returns:
            指标数据的副本
        """
        return ESGMetrics(
            company_name=metrics.company_name,
            year=metrics.year,
            carbon_emissions=metrics.carbon_emissions,
            renewable_energy_ratio=metrics.renewable_energy_ratio,
            energy_efficiency=metrics.energy_efficiency,
            water_consumption=metrics.water_consumption,
            waste_recycling_rate=metrics.waste_recycling_rate,
            employee_count=metrics.employee_count,
            female_ratio=metrics.female_ratio,
            training_hours=metrics.training_hours,
            safety_incidents=metrics.safety_incidents,
            community_investment=metrics.community_investment,
            board_independence_ratio=metrics.board_independence_ratio,
            ethics_training_coverage=metrics.ethics_training_coverage,
            esg_report_quality=metrics.esg_report_quality,
            source=metrics.source,
            extracted_at=metrics.extracted_at,
            confidence=metrics.confidence.copy(),
            data_sources=metrics.data_sources.copy()
        )
    
    def _try_complete_field(
        self, 
        field_name: str, 
        metrics: ESGMetrics
    ) -> Tuple[Any, str, float, str]:
        """尝试补全单个字段
        
        按优先级尝试：行业基准 -> 历史数据 -> 规则推理 -> 默认值
        
        Args:
            field_name: 字段名
            metrics: 当前指标数据（含已补全值）
            
        Returns:
            (补全值, 方法, 置信度, 原因) 元组
        """
        # 策略1: 使用行业基准数据
        value, confidence, reason = self._complete_from_benchmark(field_name)
        if value is not None:
            return value, "benchmark", confidence, reason
        
        # 策略2: 使用历史数据趋势
        value, confidence, reason = self._complete_from_historical(field_name)
        if value is not None:
            return value, "historical", confidence, reason
        
        # 策略3: 使用规则推理
        value, confidence, reason = self._complete_by_inference(field_name, metrics)
        if value is not None:
            return value, "inference", confidence, reason
        
        # 策略4: 使用默认值
        value = self.default_values.get(field_name)
        reason = f"使用预设默认值: {value}"
        return value, "default", 0.5, reason
    
    def _complete_from_benchmark(
        self, 
        field_name: str
    ) -> Tuple[Optional[Any], float, str]:
        """从行业基准数据补全
        
        Args:
            field_name: 字段名
            
        Returns:
            (值, 置信度, 原因) 元组，无法补全时值为 None
        """
        if not self.benchmark_data:
            return None, 0.0, "无行业基准数据"
        
        benchmark_map = {
            "renewable_energy_ratio": self.benchmark_data.avg_renewable_energy_ratio,
            "energy_efficiency": self.benchmark_data.avg_energy_efficiency,
            "female_ratio": self.benchmark_data.avg_female_ratio,
            "training_hours": self.benchmark_data.avg_training_hours,
            "board_independence_ratio": self.benchmark_data.avg_board_independence_ratio,
        }
        
        value = benchmark_map.get(field_name)
        if value is not None:
            return value, 0.85, f"基于行业基准数据 (样本数: {self.benchmark_data.sample_size})"
        
        return None, 0.0, "行业基准中无此字段数据"
    
    def _complete_from_historical(
        self, 
        field_name: str
    ) -> Tuple[Optional[Any], float, str]:
        """从历史数据趋势补全
        
        使用简单的线性趋势外推。
        
        Args:
            field_name: 字段名
            
        Returns:
            (值, 置信度, 原因) 元组，无法补全时值为 None
        """
        if not self.historical_data or len(self.historical_data) < 2:
            return None, 0.0, "历史数据不足"
        
        # 收集历史值
        historical_values = []
        for year, hist_metrics in sorted(self.historical_data.items()):
            value = getattr(hist_metrics, field_name)
            if value is not None:
                historical_values.append((int(year), value))
        
        if len(historical_values) < 2:
            return None, 0.0, "该字段历史数据不足"
        
        # 简单线性趋势外推
        years = [v[0] for v in historical_values]
        values = [v[1] for v in historical_values]
        
        # 计算年均变化率
        total_change = values[-1] - values[0]
        year_span = years[-1] - years[0]
        annual_change = total_change / year_span if year_span > 0 else 0
        
        # 外推到下一年
        predicted_value = values[-1] + annual_change
        
        # 置信度与历史数据点数量相关
        confidence = min(0.5 + len(historical_values) * 0.1, 0.8)
        
        reason = f"基于 {len(historical_values)} 年历史数据趋势预测"
        return predicted_value, confidence, reason
    
    def _complete_by_inference(
        self, 
        field_name: str,
        metrics: ESGMetrics
    ) -> Tuple[Optional[Any], float, str]:
        """通过规则推理补全
        
        基于相关指标之间的逻辑关系进行推算。
        
        Args:
            field_name: 字段名
            metrics: 当前指标数据
            
        Returns:
            (值, 置信度, 原因) 元组，无法补全时值为 None
        """
        # 规则1: 基于能源效率推算可再生能源比例
        if field_name == "renewable_energy_ratio":
            efficiency = metrics.energy_efficiency
            if efficiency is not None:
                # 能源效率与可再生能源比例通常正相关
                estimated = efficiency * 0.4  # 粗略估算
                return estimated, 0.6, f"基于能源效率({efficiency})估算"
        
        # 规则2: 基于培训时长推算道德培训覆盖率
        if field_name == "ethics_training_coverage":
            training = metrics.training_hours
            if training is not None:
                # 培训时长较长时，通常覆盖率也较高
                estimated = min(training * 3, 100)
                return estimated, 0.55, f"基于培训时长({training}h)估算"
        
        # 规则3: 基于女性比例推算多元化水平
        if field_name == "board_independence_ratio":
            female_ratio = metrics.female_ratio
            if female_ratio is not None:
                # 女性比例高的公司通常治理更规范
                estimated = 50 + (female_ratio - 30) * 0.5
                return max(30, min(estimated, 90)), 0.5, f"基于女性比例({female_ratio}%)估算"
        
        return None, 0.0, "无适用的推理规则"
    
    def get_completion_summary(self) -> Dict[str, Any]:
        """获取补全摘要统计
        
        Returns:
            包含补全统计信息的字典
        """
        if not self._logs:
            return {
                "total_completed": 0,
                "by_method": {},
                "by_dimension": {},
                "avg_confidence": 0.0
            }
        
        # 按方法统计
        by_method = {}
        for log in self._logs:
            by_method[log.method] = by_method.get(log.method, 0) + 1
        
        # 按维度统计
        by_dimension = {"E": 0, "S": 0, "G": 0}
        for log in self._logs:
            for dim, fields in self.DIMENSION_MAP.items():
                if log.field_name in fields:
                    by_dimension[dim] += 1
                    break
        
        return {
            "total_completed": len(self._logs),
            "by_method": by_method,
            "by_dimension": by_dimension,
            "avg_confidence": sum(log.confidence for log in self._logs) / len(self._logs)
        }
