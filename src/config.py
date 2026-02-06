"""全局配置

集中管理所有配置项，支持环境变量覆盖。
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 路径配置
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MOCK_DATA_DIR = DATA_DIR / "mock"
DB_DIR = PROJECT_ROOT / "database" / "chroma"

# Ollama配置
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# 模型配置
MODELS = {
    "llm": os.getenv("OLLAMA_LLM_MODEL", "deepseek-r1:7b"),
    "embedding": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
}

# ESG维度定义
ESG_DIMENSIONS = {
    "E": {"name": "环境", "color": "#52c41a"},
    "S": {"name": "社会", "color": "#1890ff"},
    "G": {"name": "治理", "color": "#faad14"}
}

ESG_DIMENSION_NAMES = {k: v["name"] for k, v in ESG_DIMENSIONS.items()}
ESG_COLORS = {k: v["color"] for k, v in ESG_DIMENSIONS.items()}

# 评分阈值
DEFAULT_SCORE = 50.0
GAP_THRESHOLD_HIGH = 15.0
GAP_THRESHOLD_MEDIUM = 8.0
AHP_CONSISTENCY_THRESHOLD = 0.1

# AHP配置
AHP_RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 
                6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

# UI配置
ANALYSIS_YEARS = ["2025", "2024", "2023"]
BENCHMARK_COMPANIES = ["维斯塔斯", "西门子歌美飒", "行业平均"]
