"""Ollama工具"""

import requests
from typing import List, Optional

from src.config import OLLAMA_URL, OLLAMA_TIMEOUT


class OllamaClient:
    """Ollama客户端"""
    
    def __init__(self, model: Optional[str] = None, url: Optional[str] = None):
        self.model = model
        self.url = url or OLLAMA_URL
        self.timeout = OLLAMA_TIMEOUT
    
    def embed(self, text: str) -> List[float]:
        """文本向量化"""
        resp = requests.post(
            f"{self.url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    
    def generate(self, prompt: str, **options) -> str:
        """生成文本"""
        resp = requests.post(
            f"{self.url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": options
            },
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()["response"]
    
    def check(self) -> bool:
        """检查服务状态"""
        try:
            resp = requests.get(self.url, timeout=3)
            return resp.status_code == 200
        except:
            return False
