"""性能监控模块

提供性能指标收集、慢查询日志、性能分析等功能。
"""

import functools
import logging
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

# 配置日志
logger = logging.getLogger(__name__)

# 指标注册表
REGISTRY = CollectorRegistry()

# 定义Prometheus指标
REQUEST_COUNT = Counter(
    "esg_request_total", "Total requests", ["method", "endpoint", "status"], registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    "esg_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY,
)

PDF_EXTRACTION_DURATION = Histogram(
    "esg_pdf_extraction_duration_seconds",
    "PDF extraction duration",
    ["backend"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=REGISTRY,
)

VECTOR_SEARCH_DURATION = Histogram(
    "esg_vector_search_duration_seconds",
    "Vector search duration",
    ["index_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY,
)

LLM_REQUEST_DURATION = Histogram(
    "esg_llm_request_duration_seconds",
    "LLM request duration",
    ["model", "operation"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=REGISTRY,
)

ACTIVE_REQUESTS = Gauge(
    "esg_active_requests", "Number of active requests", ["endpoint"], registry=REGISTRY
)

CACHE_HIT_COUNTER = Counter(
    "esg_cache_hit_total", "Cache hit count", ["cache_type"], registry=REGISTRY
)

CACHE_MISS_COUNTER = Counter(
    "esg_cache_miss_total", "Cache miss count", ["cache_type"], registry=REGISTRY
)

MEMORY_USAGE = Gauge("esg_memory_usage_bytes", "Memory usage in bytes", ["type"], registry=REGISTRY)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error: Optional[str] = None):
        """结束性能测量"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.success = success
        self.error_message = error


class PerformanceMonitor:
    """性能监控器

    用于监控函数执行性能和收集性能指标。

    Example:
        >>> monitor = PerformanceMonitor()
        >>>
        >>> @monitor.timeit("pdf_extraction")
        ... def extract_pdf(file_path):
        ...     return pdf_extractor.extract(file_path)
        >>>
        >>> # 使用上下文管理器
        >>> with monitor.track("vector_search"):
        ...     results = vector_store.search(query)
    """

    # 慢查询阈值（毫秒）
    SLOW_QUERY_THRESHOLD = 1000

    def __init__(self, slow_threshold_ms: float = 1000.0):
        """初始化性能监控器

        Args:
            slow_threshold_ms: 慢查询阈值（毫秒）
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000

    def timeit(
        self, operation: str, log_slow: bool = True, track_metrics: bool = True
    ) -> Callable[[F], F]:
        """函数执行时间装饰器

        Args:
            operation: 操作名称
            log_slow: 是否记录慢查询
            track_metrics: 是否跟踪指标

        Returns:
            装饰器函数
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                metric = PerformanceMetrics(
                    operation=operation,
                    start_time=datetime.now(),
                    metadata={"function": func.__name__, "module": func.__module__},
                )

                try:
                    start = time.perf_counter()
                    result = func(*args, **kwargs)
                    duration = (time.perf_counter() - start) * 1000

                    metric.finish(success=True)
                    metric.duration_ms = duration

                    if track_metrics:
                        self._record_metric(metric)

                    if log_slow and duration > self.slow_threshold_ms:
                        self._log_slow_query(metric)

                    return result

                except Exception as e:
                    duration = (time.perf_counter() - start) * 1000 if "start" in locals() else 0
                    metric.finish(success=False, error=str(e))
                    metric.duration_ms = duration

                    if track_metrics:
                        self._record_metric(metric)

                    raise

            return wrapper  # type: ignore

        return decorator

    @contextmanager
    def track(self, operation: str, log_slow: bool = True, **metadata):
        """上下文管理器用于跟踪代码块性能

        Args:
            operation: 操作名称
            log_slow: 是否记录慢查询
            **metadata: 额外的元数据

        Yields:
            PerformanceMetrics: 性能指标对象
        """
        metric = PerformanceMetrics(
            operation=operation, start_time=datetime.now(), metadata=metadata
        )

        try:
            start = time.perf_counter()
            yield metric
            duration = (time.perf_counter() - start) * 1000

            metric.finish(success=True)
            metric.duration_ms = duration
            self._record_metric(metric)

            if log_slow and duration > self.slow_threshold_ms:
                self._log_slow_query(metric)

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000 if "start" in locals() else 0
            metric.finish(success=False, error=str(e))
            metric.duration_ms = duration
            self._record_metric(metric)
            raise

    def _record_metric(self, metric: PerformanceMetrics):
        """记录性能指标"""
        self.metrics_history.append(metric)

        # 限制历史记录大小
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

    def _log_slow_query(self, metric: PerformanceMetrics):
        """记录慢查询日志"""
        logger.warning(
            f"慢查询检测: {metric.operation}\n"
            f"  耗时: {metric.duration_ms:.2f}ms\n"
            f"  阈值: {self.slow_threshold_ms}ms\n"
            f"  元数据: {metric.metadata}"
        )

    def get_slow_queries(
        self, operation: Optional[str] = None, limit: int = 100
    ) -> List[PerformanceMetrics]:
        """获取慢查询列表

        Args:
            operation: 可选的操作名称过滤
            limit: 返回的最大数量

        Returns:
            慢查询列表
        """
        slow_queries = [
            m
            for m in self.metrics_history
            if m.duration_ms and m.duration_ms > self.slow_threshold_ms
        ]

        if operation:
            slow_queries = [q for q in slow_queries if q.operation == operation]

        # 按耗时降序排序
        slow_queries.sort(key=lambda x: x.duration_ms or 0, reverse=True)

        return slow_queries[:limit]

    def get_statistics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计信息

        Args:
            operation: 可选的操作名称过滤

        Returns:
            统计信息字典
        """
        metrics = self.metrics_history
        if operation:
            metrics = [m for m in metrics if m.operation == operation]

        if not metrics:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "min_duration_ms": 0,
                "success_rate": 0,
            }

        durations = [m.duration_ms for m in metrics if m.duration_ms is not None]
        success_count = sum(1 for m in metrics if m.success)

        return {
            "count": len(metrics),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "success_rate": success_count / len(metrics),
            "slow_query_count": sum(1 for d in durations if d > self.slow_threshold_ms),
        }

    def clear_history(self):
        """清除历史记录"""
        self.metrics_history.clear()


# 全局性能监控器实例
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return _global_monitor


def timeit(operation: str, slow_threshold_ms: float = 1000.0, log_slow: bool = True):
    """便捷的函数计时装饰器

    Args:
        operation: 操作名称
        slow_threshold_ms: 慢查询阈值
        log_slow: 是否记录慢查询

    Returns:
        装饰器函数
    """
    monitor = PerformanceMonitor(slow_threshold_ms)
    return monitor.timeit(operation, log_slow)


@contextmanager
def track_operation(
    operation: str, slow_threshold_ms: float = 1000.0, log_slow: bool = True, **metadata
):
    """便捷的上下文管理器

    Args:
        operation: 操作名称
        slow_threshold_ms: 慢查询阈值
        log_slow: 是否记录慢查询
        **metadata: 额外的元数据

    Yields:
        PerformanceMetrics: 性能指标对象
    """
    monitor = PerformanceMonitor(slow_threshold_ms)
    with monitor.track(operation, log_slow, **metadata) as metric:
        yield metric


def get_prometheus_metrics() -> bytes:
    """获取Prometheus格式的指标数据"""
    return generate_latest(REGISTRY)


def update_memory_metrics():
    """更新内存使用指标"""
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        MEMORY_USAGE.labels(type="rss").set(memory_info.rss)
        MEMORY_USAGE.labels(type="vms").set(memory_info.vms)
    except ImportError:
        logger.debug("psutil not available, skipping memory metrics")
    except Exception as e:
        logger.error(f"Failed to update memory metrics: {e}")
