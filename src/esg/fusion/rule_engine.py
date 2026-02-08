"""规则引擎

基于规则的ESG指标推导引擎，支持规则定义、规则链执行和上下文管理。
可用于从原始数据推导派生指标，或执行ESG分析流程。
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union

from src.esg.core.models import ESGMetrics

logger = logging.getLogger(__name__)


class RulePriority(Enum):
    """规则优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class RuleStatus(Enum):
    """规则执行状态"""

    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class RuleContext:
    """规则执行上下文

    维护规则执行过程中的状态和数据。
    """

    # 输入数据
    metrics: Optional[ESGMetrics] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # 执行状态
    variables: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    # 结果存储
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 元数据
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def set_variable(self, key: str, value: Any) -> None:
        """设置上下文变量"""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取上下文变量"""
        return self.variables.get(key, default)

    def set_result(self, key: str, value: Any) -> None:
        """设置结果"""
        self.results[key] = value

    def get_result(self, key: str, default: Any = None) -> Any:
        """获取结果"""
        return self.results.get(key, default)

    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        logger.error(f"规则上下文错误: {message}")

    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)
        logger.warning(f"规则上下文警告: {message}")

    def add_history(
        self, rule_name: str, status: RuleStatus, details: Dict[str, Any] = None
    ) -> None:
        """添加执行历史"""
        self.history.append(
            {
                "rule": rule_name,
                "status": status.name,
                "timestamp": datetime.now().isoformat(),
                "details": details or {},
            }
        )

    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "variables": self.variables,
            "results": self.results,
            "errors": self.errors,
            "warnings": self.warnings,
            "history": self.history,
            "execution_time": self.execution_time,
        }


@dataclass
class Rule:
    """规则定义

    定义一条可执行的业务规则。
    """

    name: str
    description: str = ""
    priority: RulePriority = RulePriority.NORMAL

    # 条件函数：返回True时执行action
    condition: Optional[Callable[[RuleContext], bool]] = None

    # 执行函数
    action: Callable[[RuleContext], None] = field(default=None)

    # 依赖的规则名列表（这些规则必须先执行）
    dependencies: List[str] = field(default_factory=list)

    # 元数据
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        if self.action is None:
            self.action = lambda ctx: None

    def should_execute(self, context: RuleContext) -> bool:
        """检查是否应该执行"""
        if not self.enabled:
            return False
        if self.condition is None:
            return True
        try:
            return self.condition(context)
        except Exception as e:
            logger.error(f"规则 {self.name} 条件判断失败: {e}")
            return False

    def execute(self, context: RuleContext) -> RuleStatus:
        """执行规则"""
        try:
            self.action(context)
            return RuleStatus.SUCCESS
        except Exception as e:
            context.add_error(f"规则 {self.name} 执行失败: {e}")
            return RuleStatus.FAILED


class RuleBuilder:
    """规则构建器

    用于便捷地构建规则。
    """

    def __init__(self):
        self._name = ""
        self._description = ""
        self._priority = RulePriority.NORMAL
        self._condition = None
        self._action = None
        self._dependencies = []
        self._tags = []

    def name(self, name: str) -> "RuleBuilder":
        """设置规则名称"""
        self._name = name
        return self

    def description(self, desc: str) -> "RuleBuilder":
        """设置规则描述"""
        self._description = desc
        return self

    def priority(self, priority: RulePriority) -> "RuleBuilder":
        """设置优先级"""
        self._priority = priority
        return self

    def when(self, condition: Callable[[RuleContext], bool]) -> "RuleBuilder":
        """设置条件"""
        self._condition = condition
        return self

    def then(self, action: Callable[[RuleContext], None]) -> "RuleBuilder":
        """设置执行动作"""
        self._action = action
        return self

    def depends_on(self, *rule_names: str) -> "RuleBuilder":
        """设置依赖"""
        self._dependencies.extend(rule_names)
        return self

    def with_tags(self, *tags: str) -> "RuleBuilder":
        """添加标签"""
        self._tags.extend(tags)
        return self

    def build(self) -> Rule:
        """构建规则"""
        if not self._name:
            raise ValueError("规则名称不能为空")
        if self._action is None:
            raise ValueError("规则动作不能为空")

        return Rule(
            name=self._name,
            description=self._description,
            priority=self._priority,
            condition=self._condition,
            action=self._action,
            dependencies=self._dependencies,
            tags=self._tags,
        )


class RuleEngine:
    """规则引擎
    
    管理和执行规则链，支持依赖解析、优先级排序和事务性执行。
    
    Example:
        >>> engine = RuleEngine()
        >>> 
        >>> # 定义规则
        >>> rule1 = RuleBuilder().name("calculate_carbon_intensity")\
        ...     .description("计算碳排放强度")\
        ...     .when(lambda ctx: ctx.metrics and ctx.metrics.carbon_emissions is not None)\
        ...     .then(lambda ctx: ctx.set_result("carbon_intensity", 
        ...                                      ctx.metrics.carbon_emissions / 1000))\
        ...     .build()
        >>> 
        >>> engine.add_rule(rule1)
        >>> 
        >>> # 执行规则
        >>> context = RuleContext(metrics=esg_metrics)
        >>> engine.execute(context)
    """

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._execution_order: List[str] = []
        self._execution_stats: Dict[str, Dict[str, Any]] = {}

    def add_rule(self, rule: Rule) -> "RuleEngine":
        """添加规则

        Args:
            rule: 规则对象

        Returns:
            self，支持链式调用
        """
        if rule.name in self._rules:
            logger.warning(f"规则 {rule.name} 已存在，将被覆盖")

        self._rules[rule.name] = rule
        logger.info(f"添加规则: {rule.name}")
        return self

    def add_rules(self, *rules: Rule) -> "RuleEngine":
        """批量添加规则"""
        for rule in rules:
            self.add_rule(rule)
        return self

    def remove_rule(self, name: str) -> bool:
        """移除规则

        Args:
            name: 规则名称

        Returns:
            是否成功移除
        """
        if name in self._rules:
            del self._rules[name]
            logger.info(f"移除规则: {name}")
            return True
        return False

    def get_rule(self, name: str) -> Optional[Rule]:
        """获取规则"""
        return self._rules.get(name)

    def list_rules(self, tag: Optional[str] = None) -> List[Rule]:
        """列出规则

        Args:
            tag: 按标签筛选

        Returns:
            规则列表
        """
        rules = list(self._rules.values())
        if tag:
            rules = [r for r in rules if tag in r.tags]
        return sorted(rules, key=lambda r: r.priority.value, reverse=True)

    def clear_rules(self) -> None:
        """清空所有规则"""
        self._rules.clear()
        self._execution_order.clear()
        logger.info("清空所有规则")

    def _resolve_dependencies(self) -> List[str]:
        """解析规则执行顺序

        使用拓扑排序确保依赖规则先执行。

        Returns:
            按执行顺序排列的规则名称列表

        Raises:
            ValueError: 存在循环依赖时抛出
        """
        # 构建依赖图
        graph: Dict[str, Set[str]] = {name: set() for name in self._rules}
        in_degree: Dict[str, int] = {name: 0 for name in self._rules}

        for name, rule in self._rules.items():
            for dep in rule.dependencies:
                if dep not in self._rules:
                    raise ValueError(f"规则 {name} 依赖未定义的规则 {dep}")
                if name not in graph[dep]:
                    graph[dep].add(name)
                    in_degree[name] += 1

        # Kahn算法拓扑排序
        # 按优先级组织就绪队列
        ready: Dict[int, List[str]] = {p.value: [] for p in RulePriority}
        for name, degree in in_degree.items():
            if degree == 0:
                priority = self._rules[name].priority.value
                ready[priority].append(name)

        result = []
        while any(ready.values()):
            # 按优先级从高到低处理
            for priority in sorted(ready.keys(), reverse=True):
                if ready[priority]:
                    name = ready[priority].pop(0)
                    result.append(name)

                    for dependent in sorted(graph[name]):
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            dep_priority = self._rules[dependent].priority.value
                            ready[dep_priority].append(dependent)
                    break

        if len(result) != len(self._rules):
            raise ValueError("规则存在循环依赖，无法解析执行顺序")

        return result

    def execute(
        self,
        context: Optional[RuleContext] = None,
        stop_on_error: bool = True,
        tag_filter: Optional[str] = None,
    ) -> RuleContext:
        """执行规则链

        Args:
            context: 规则上下文，为None时创建新上下文
            stop_on_error: 遇到错误时是否停止
            tag_filter: 只执行指定标签的规则

        Returns:
            执行后的上下文
        """
        context = context or RuleContext()
        context.start_time = datetime.now()

        try:
            # 确定执行顺序
            execution_order = self._resolve_dependencies()

            # 筛选规则
            if tag_filter:
                execution_order = [
                    name for name in execution_order if tag_filter in self._rules[name].tags
                ]

            logger.info(f"开始执行规则链，共 {len(execution_order)} 条规则")

            for rule_name in execution_order:
                rule = self._rules[rule_name]

                # 检查条件
                if not rule.should_execute(context):
                    context.add_history(rule_name, RuleStatus.SKIPPED)
                    logger.debug(f"跳过规则: {rule_name}")
                    continue

                # 执行规则
                logger.debug(f"执行规则: {rule_name}")
                status = rule.execute(context)
                context.add_history(rule_name, status)

                # 记录统计
                self._execution_stats[rule_name] = {
                    "status": status.name,
                    "timestamp": datetime.now().isoformat(),
                }

                # 错误处理
                if status == RuleStatus.FAILED and stop_on_error:
                    logger.error(f"规则 {rule_name} 执行失败，停止执行")
                    break

            context.end_time = datetime.now()
            if context.start_time:
                context.execution_time = (context.end_time - context.start_time).total_seconds()

            logger.info(f"规则链执行完成，耗时 {context.execution_time:.3f}s")

        except Exception as e:
            context.add_error(f"规则链执行异常: {e}")
            logger.exception("规则链执行异常")

        return context

    def execute_single(self, rule_name: str, context: RuleContext) -> RuleStatus:
        """执行单个规则

        Args:
            rule_name: 规则名称
            context: 规则上下文

        Returns:
            执行状态
        """
        rule = self._rules.get(rule_name)
        if not rule:
            context.add_error(f"规则不存在: {rule_name}")
            return RuleStatus.FAILED

        if not rule.should_execute(context):
            return RuleStatus.SKIPPED

        return rule.execute(context)

    def get_execution_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取执行统计"""
        return self._execution_stats.copy()

    def create_context(self, metrics: Optional[ESGMetrics] = None, **kwargs) -> RuleContext:
        """创建规则上下文

        Args:
            metrics: ESG指标数据
            **kwargs: 其他原始数据

        Returns:
            规则上下文
        """
        return RuleContext(metrics=metrics, raw_data=kwargs)


# 预定义的ESG规则模板


class ESGRules:
    """ESG常用规则模板"""

    @staticmethod
    def carbon_intensity_rule() -> Rule:
        """碳排放强度计算规则"""
        return (
            RuleBuilder()
            .name("carbon_intensity")
            .description("计算单位营收碳排放强度")
            .with_tags("environment", "calculation")
            .when(lambda ctx: ctx.metrics is not None and ctx.metrics.carbon_emissions is not None)
            .then(
                lambda ctx: ctx.set_result(
                    "carbon_intensity",
                    {
                        "value": ctx.metrics.carbon_emissions / 1000000,  # 转换为吨/百万元
                        "unit": "吨CO2e/百万元",
                        "assessment": (
                            "高"
                            if ctx.metrics.carbon_emissions > 5000000
                            else "中" if ctx.metrics.carbon_emissions > 1000000 else "低"
                        ),
                    },
                )
            )
            .build()
        )

    @staticmethod
    def diversity_score_rule() -> Rule:
        """多元化得分计算规则"""
        return (
            RuleBuilder()
            .name("diversity_score")
            .description("计算员工多元化得分")
            .with_tags("social", "calculation")
            .when(lambda ctx: ctx.metrics is not None and ctx.metrics.female_ratio is not None)
            .then(
                lambda ctx: ctx.set_result(
                    "diversity_score",
                    {
                        "score": min(ctx.metrics.female_ratio * 100, 100),
                        "level": (
                            "优秀"
                            if ctx.metrics.female_ratio >= 0.4
                            else "良好" if ctx.metrics.female_ratio >= 0.3 else "待改进"
                        ),
                    },
                )
            )
            .build()
        )

    @staticmethod
    def governance_compliance_rule() -> Rule:
        """治理合规检查规则"""
        return (
            RuleBuilder()
            .name("governance_compliance")
            .description("检查治理指标合规性")
            .with_tags("governance", "compliance")
            .when(lambda ctx: ctx.metrics is not None)
            .then(lambda ctx: ESGRules._check_governance(ctx))
            .build()
        )

    @staticmethod
    def _check_governance(context: RuleContext) -> None:
        """检查治理合规性"""
        metrics = context.metrics
        issues = []

        if metrics.board_independence_ratio is not None:
            if metrics.board_independence_ratio < 0.3:
                issues.append("董事会独立性低于30%")
        else:
            issues.append("缺少董事会独立性数据")

        if metrics.ethics_training_coverage is not None:
            if metrics.ethics_training_coverage < 0.8:
                issues.append("伦理培训覆盖率低于80%")
        else:
            issues.append("缺少伦理培训数据")

        context.set_result(
            "governance_compliance",
            {
                "compliant": len(issues) == 0,
                "issues": issues,
                "score": max(0, 100 - len(issues) * 20),
            },
        )

    @staticmethod
    def data_quality_check_rule() -> Rule:
        """数据质量检查规则"""
        return (
            RuleBuilder()
            .name("data_quality_check")
            .description("检查ESG数据完整性")
            .priority(RulePriority.HIGH)
            .with_tags("quality", "validation")
            .when(lambda ctx: ctx.metrics is not None)
            .then(lambda ctx: ESGRules._check_data_quality(ctx))
            .build()
        )

    @staticmethod
    def _check_data_quality(context: RuleContext) -> None:
        """检查数据质量"""
        metrics = context.metrics
        missing_fields = []

        # 检查环境数据
        env_fields = ["carbon_emissions", "renewable_energy_ratio", "energy_efficiency"]
        for field in env_fields:
            if getattr(metrics, field) is None:
                missing_fields.append(field)

        # 检查社会数据
        social_fields = ["employee_count", "female_ratio", "training_hours"]
        for field in social_fields:
            if getattr(metrics, field) is None:
                missing_fields.append(field)

        # 检查治理数据
        gov_fields = ["board_independence_ratio", "ethics_training_coverage"]
        for field in gov_fields:
            if getattr(metrics, field) is None:
                missing_fields.append(field)

        completeness = 1 - len(missing_fields) / (
            len(env_fields) + len(social_fields) + len(gov_fields)
        )

        context.set_result(
            "data_quality",
            {
                "completeness": round(completeness, 2),
                "missing_fields": missing_fields,
                "quality_level": (
                    "高" if completeness >= 0.8 else "中" if completeness >= 0.5 else "低"
                ),
            },
        )

        if completeness < 0.5:
            context.add_warning("数据完整度低于50%，分析结果可能不准确")


def create_default_engine() -> RuleEngine:
    """创建默认规则引擎

    预装ESG常用规则。

    Returns:
        配置好的规则引擎
    """
    engine = RuleEngine()
    engine.add_rules(
        ESGRules.data_quality_check_rule(),
        ESGRules.carbon_intensity_rule(),
        ESGRules.diversity_score_rule(),
        ESGRules.governance_compliance_rule(),
    )
    return engine
