# /envision/utils/ollama_utils.py
"""Ollama工具函数 - 安全线程版本"""

import requests
import subprocess
import time
import platform
import logging
import threading
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from config import OLLAMA_URL, OLLAMA_TIMEOUT, MODELS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_on_failure(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise e
        return wrapper
    return decorator


class OllamaEmbeddings:
    """线程安全的Embedding客户端
    
    使用线程本地存储确保线程安全，并正确管理Session生命周期。
    """
    
    def __init__(self, model_name=MODELS["embedding"]):
        self.model_name = model_name
        self._thread_local = threading.local()
    
    def __del__(self):
        """析构时关闭Session，防止资源泄漏"""
        self.close()
    
    def close(self):
        """显式关闭Session"""
        if hasattr(self._thread_local, 'session'):
            try:
                self._thread_local.session.close()
            except Exception as e:
                logger.warning(f"关闭Session时出错: {e}")
            finally:
                delattr(self._thread_local, 'session')
    
    def _get_session(self):
        """获取线程本地Session"""
        if not hasattr(self._thread_local, 'session'):
            import requests
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=2, pool_maxsize=4)
            session.mount('http://', adapter)
            self._thread_local.session = session
        return self._thread_local.session
    
    @retry_on_failure()
    def embed_query(self, text: str) -> List[float]:
        """单文本向量化"""
        session = self._get_session()
        response = session.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": self.model_name, "prompt": text},
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        return response.json()["embedding"]


def check_ollama_running() -> bool:
    """检查Ollama服务状态"""
    try:
        resp = requests.get(OLLAMA_URL, timeout=3)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        # 服务未启动或端口未监听
        return False
    except requests.exceptions.Timeout:
        logger.warning("Ollama连接超时")
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama检查异常: {type(e).__name__}: {e}")
        return False


def ensure_ollama_running() -> tuple:
    """确保Ollama运行"""
    if check_ollama_running():
        return True, "Ollama运行中"
    
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        time.sleep(3)
        if check_ollama_running():
            return True, "Ollama已启动"
    except:
        pass
    
    return False, "请手动运行: ollama serve"