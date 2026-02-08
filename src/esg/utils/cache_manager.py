"""缓存管理模块

提供多级缓存支持，包括内存缓存、本地文件缓存和分布式缓存。
支持异步操作和缓存预热。
"""

import asyncio
import functools
import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

# 配置日志
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""

    key: str
    value: T
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = 0.0


class CacheBackend:
    """缓存后端基类"""

    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    async def clear(self) -> bool:
        raise NotImplementedError

    async def keys(self, pattern: str = "*") -> List[str]:
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = 3600):
        """初始化内存缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            # 检查过期
            if entry.expires_at and time.time() > entry.expires_at:
                del self._cache[key]
                return None

            # 更新访问统计
            entry.access_count += 1
            entry.last_accessed = time.time()

            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            # 检查是否需要清理
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl if ttl else None

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                access_count=0,
                last_accessed=0.0,
            )

            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            if entry.expires_at and time.time() > entry.expires_at:
                del self._cache[key]
                return False

            return True

    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
            return True

    async def keys(self, pattern: str = "*") -> List[str]:
        async with self._lock:
            import fnmatch

            return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]

    def _evict_oldest(self):
        """清理最久未使用的条目"""
        if not self._cache:
            return

        # 使用LRU策略
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed or self._cache[k].created_at,
        )
        del self._cache[oldest_key]

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        async with self._lock:
            total = len(self._cache)
            expired = sum(
                1 for e in self._cache.values() if e.expires_at and time.time() > e.expires_at
            )

            return {
                "total_entries": total,
                "expired_entries": expired,
                "max_size": self.max_size,
                "usage_ratio": total / self.max_size if self.max_size > 0 else 0,
            }


class FileCacheBackend(CacheBackend):
    """文件缓存后端"""

    def __init__(self, cache_dir: Union[str, Path], default_ttl: Optional[int] = 86400):
        """初始化文件缓存

        Args:
            cache_dir: 缓存目录
            default_ttl: 默认TTL（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希作为文件名，避免特殊字符问题
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    async def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)

        async with self._lock:
            if not cache_path.exists():
                return None

            try:
                with open(cache_path, "rb") as f:
                    entry: CacheEntry = pickle.load(f)

                # 检查过期
                if entry.expires_at and time.time() > entry.expires_at:
                    cache_path.unlink(missing_ok=True)
                    return None

                return entry.value

            except Exception as e:
                logger.warning(f"Failed to read cache file: {e}")
                cache_path.unlink(missing_ok=True)
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        cache_path = self._get_cache_path(key)

        async with self._lock:
            try:
                ttl = ttl or self.default_ttl
                expires_at = time.time() + ttl if ttl else None

                entry = CacheEntry(
                    key=key, value=value, created_at=time.time(), expires_at=expires_at
                )

                with open(cache_path, "wb") as f:
                    pickle.dump(entry, f)

                return True

            except Exception as e:
                logger.error(f"Failed to write cache file: {e}")
                return False

    async def delete(self, key: str) -> bool:
        cache_path = self._get_cache_path(key)
        async with self._lock:
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False

    async def exists(self, key: str) -> bool:
        cache_path = self._get_cache_path(key)

        async with self._lock:
            if not cache_path.exists():
                return False

            try:
                with open(cache_path, "rb") as f:
                    entry: CacheEntry = pickle.load(f)

                if entry.expires_at and time.time() > entry.expires_at:
                    cache_path.unlink(missing_ok=True)
                    return False

                return True

            except Exception:
                return False

    async def clear(self) -> bool:
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            return True

    async def keys(self, pattern: str = "*") -> List[str]:
        """获取所有缓存键（注意：此方法需要读取所有缓存文件）"""
        keys = []
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, "rb") as f:
                        entry: CacheEntry = pickle.load(f)
                        keys.append(entry.key)
                except Exception:
                    pass
        return keys


class CacheManager:
    """缓存管理器

    提供多级缓存支持，包括内存缓存和文件缓存。

    Example:
        >>> cache = CacheManager()
        >>>
        >>> # 基本用法
        >>> await cache.set("key", "value", ttl=3600)
        >>> value = await cache.get("key")
        >>>
        >>> # 使用装饰器
        >>> @cache.cached(ttl=3600)
        ... async def expensive_operation(param):
        ...     return await compute(param)
        >>>
        >>> # 缓存预热
        >>> await cache.warm_up([
        ...     ("key1", lambda: fetch_data1()),
        ...     ("key2", lambda: fetch_data2())
        ... ])
    """

    def __init__(
        self,
        memory_cache_size: int = 1000,
        cache_dir: Optional[Union[str, Path]] = None,
        default_ttl: int = 3600,
    ):
        """初始化缓存管理器

        Args:
            memory_cache_size: 内存缓存最大条目数
            cache_dir: 文件缓存目录，None则禁用文件缓存
            default_ttl: 默认缓存时间（秒）
        """
        self.memory_cache = MemoryCacheBackend(max_size=memory_cache_size, default_ttl=default_ttl)

        self.file_cache: Optional[FileCacheBackend] = None
        if cache_dir:
            self.file_cache = FileCacheBackend(
                cache_dir=cache_dir, default_ttl=default_ttl * 24  # 文件缓存默认24倍TTL
            )

        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        先查内存缓存，再查文件缓存。

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        # 先查内存缓存
        value = await self.memory_cache.get(key)
        if value is not None:
            logger.debug(f"Memory cache hit: {key}")
            return value

        # 再查文件缓存
        if self.file_cache:
            value = await self.file_cache.get(key)
            if value is not None:
                # 回填到内存缓存
                await self.memory_cache.set(key, value)
                logger.debug(f"File cache hit: {key}")
                return value

        logger.debug(f"Cache miss: {key}")
        return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, backend: str = "both"
    ) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），None使用默认值
            backend: 缓存后端，可选"memory", "file", "both"

        Returns:
            是否成功
        """
        ttl = ttl or self.default_ttl

        success = True

        if backend in ("memory", "both"):
            success = await self.memory_cache.set(key, value, ttl) and success

        if backend in ("file", "both") and self.file_cache:
            success = await self.file_cache.set(key, value, ttl) and success

        return success

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        success = await self.memory_cache.delete(key)
        if self.file_cache:
            success = await self.file_cache.delete(key) or success
        return success

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if await self.memory_cache.exists(key):
            return True
        if self.file_cache and await self.file_cache.exists(key):
            return True
        return False

    async def clear(self) -> bool:
        """清空所有缓存"""
        success = await self.memory_cache.clear()
        if self.file_cache:
            success = await self.file_cache.clear() and success
        return success

    def cached(self, ttl: Optional[int] = None, key_prefix: str = "", backend: str = "both"):
        """缓存装饰器

        Args:
            ttl: 缓存时间（秒）
            key_prefix: 缓存键前缀
            backend: 缓存后端

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_key(key_prefix, func, args, kwargs)

                # 尝试从缓存获取
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = await func(*args, **kwargs)

                # 存入缓存
                await self.set(cache_key, result, ttl, backend)

                return result

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 同步函数包装
                return asyncio.run(async_wrapper(*args, **kwargs))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def _generate_key(self, prefix: str, func: Callable, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 序列化参数
        key_data = {"func": func.__qualname__, "args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return f"{prefix}:{key_hash}" if prefix else key_hash

    async def warm_up(self, warm_up_tasks: List[tuple]):
        """缓存预热

        Args:
            warm_up_tasks: 预热任务列表，每项为(key, factory)元组
        """
        for key, factory in warm_up_tasks:
            try:
                if not await self.exists(key):
                    value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
                    await self.set(key, value)
                    logger.info(f"Cache warmed up: {key}")
            except Exception as e:
                logger.error(f"Failed to warm up cache for {key}: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {"memory": await self.memory_cache.get_stats()}

        if self.file_cache:
            # 文件缓存统计需要额外计算
            file_keys = await self.file_cache.keys()
            stats["file"] = {"total_entries": len(file_keys)}

        return stats


# 全局缓存管理器实例
_global_cache: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def init_cache_manager(
    memory_cache_size: int = 1000,
    cache_dir: Optional[Union[str, Path]] = None,
    default_ttl: int = 3600,
):
    """初始化全局缓存管理器"""
    global _global_cache
    _global_cache = CacheManager(
        memory_cache_size=memory_cache_size, cache_dir=cache_dir, default_ttl=default_ttl
    )
