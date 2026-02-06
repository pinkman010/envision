# -*- coding: utf-8 -*-
"""
【工具模块】Ollama 服务与模型管理（优化版）
修改内容：
1. [新增] 类型注解 - 提升代码可读性和IDE支持
2. [新增] 重试装饰器 - 网络请求更健壮
3. [优化] 批量 Embedding 并行化 - 使用线程池加速
4. [修复] 替换 bare except 为具体异常类型
5. [新增] 引用配置中心
6. [SECURITY FIX] 使用线程本地存储解决 Session 线程安全问题
"""
import requests
import subprocess
import time
import platform
import logging
import threading  # [ADDED] 线程本地存储
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from langchain.embeddings.base import Embeddings

# 引入配置（修改点：集中管理配置）
from scripts.config import (
    OLLAMA_URL, OLLAMA_TIMEOUT, OLLAMA_PULL_TIMEOUT,
    MODELS, EMBEDDING_DIM, EMBEDDING_MAX_WORKERS, 
    MAX_RETRIES, RETRY_DELAY
)

# 配置日志（修改点：替代 print，便于生产环境调试）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 重试装饰器（新增）====================
def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """
    通用重试装饰器
    修改原因：网络请求可能因临时故障失败，重试机制提升稳定性
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, requests.Timeout) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 失败，第 {attempt + 1} 次重试: {e}")
                        time.sleep(delay * (attempt + 1))  # 指数退避
            raise last_exception
        return wrapper
    return decorator


# ==================== Embedding 客户端（优化版）====================
class OllamaEmbeddings(Embeddings):
    """
    自定义 Embedding 客户端
    修改内容：
    1. embed_documents 改为并行处理
    2. 添加类型注解
    3. 错误日志替代 print
    4. [SECURITY FIX] 使用线程本地存储替代全局 Session，避免线程安全问题
    """
    def __init__(self, model_name: str = MODELS["embedding"]):
        self.model_name = model_name
        # [FIXED] 使用线程本地存储，每个线程拥有独立的 Session
        self._thread_local = threading.local()
    
    def _get_session(self) -> requests.Session:
        """
        [ADDED] 获取当前线程的 Session，如果不存在则创建
        确保每个线程使用独立的连接池，避免线程安全问题
        """
        if not hasattr(self._thread_local, 'session'):
            session = requests.Session()
            # 配置连接池（限制连接数避免资源耗尽）
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=2,  # 每个线程独立连接池
                pool_maxsize=4
            )
            session.mount('http://', adapter)
            self._thread_local.session = session
        return self._thread_local.session
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化（并行优化版）
        修改原因：原版串行处理，100个文档需100次请求；
                 现改为线程池并行，显著提升ETL速度
        """
        results = [None] * len(texts)
        
        def embed_single(index: int, text: str) -> Tuple[int, List[float]]:
            return index, self.embed_query(text)
        
        with ThreadPoolExecutor(max_workers=EMBEDDING_MAX_WORKERS) as executor:
            futures = {
                executor.submit(embed_single, i, text): i 
                for i, text in enumerate(texts)
            }
            for future in as_completed(futures):
                try:
                    idx, embedding = future.result()
                    results[idx] = embedding
                except Exception as e:
                    idx = futures[future]
                    logger.error(f"Embedding 失败 (index={idx}): {e}")
                    results[idx] = [0.0] * EMBEDDING_DIM
        
        return results
    
    @retry_on_failure()  # 新增：自动重试
    def embed_query(self, text: str) -> List[float]:
        """单文本向量化"""
        # [FIXED] 使用线程本地存储的 Session，而非全局 Session
        session = self._get_session()
        response = session.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": self.model_name, "prompt": text},
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()  # 修改点：主动抛出HTTP错误
        return response.json()["embedding"]


# ==================== 服务管理（优化版）====================
def check_ollama_running() -> bool:
    """健康检查"""
    try:
        resp = requests.get(OLLAMA_URL, timeout=3)
        return resp.status_code == 200
    except requests.RequestException:  # 修改点：具体异常类型
        return False


def start_ollama() -> bool:
    """后台启动 Ollama 服务"""
    try:
        popen_kwargs = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL
        }
        if platform.system() == "Windows":
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
        subprocess.Popen(["ollama", "serve"], **popen_kwargs)
        
        for _ in range(10):
            time.sleep(1)
            if check_ollama_running():
                logger.info("Ollama 服务启动成功")
                return True
        return False
    except FileNotFoundError:
        logger.error("未找到 ollama 命令，请确认已安装")
        return False
    except OSError as e:
        logger.error(f"启动 Ollama 失败: {e}")
        return False


def ensure_ollama_running() -> Tuple[bool, str]:
    """服务保障入口"""
    if check_ollama_running():
        return True, "Ollama 服务运行中"
    if start_ollama():
        return True, "Ollama 已自动启动"
    return False, "无法启动 Ollama，请手动运行 'ollama serve'"


def get_missing_models() -> List[str]:
    """检查缺失的模型"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        installed = [m["name"] for m in response.json().get("models", [])]
        
        missing = []
        for model in MODELS.values():
            if not any(model in m for m in installed):
                missing.append(model)
        return missing
    except requests.RequestException as e:
        logger.warning(f"检查模型失败: {e}")
        return list(MODELS.values())


@retry_on_failure(max_retries=1)  # 下载只重试1次
def pull_model(model_name: str) -> bool:
    """拉取模型"""
    response = requests.post(
        f"{OLLAMA_URL}/api/pull",
        json={"name": model_name},
        timeout=OLLAMA_PULL_TIMEOUT
    )
    response.raise_for_status()
    return True