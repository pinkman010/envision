"""全局配置

集中管理所有配置项，支持环境变量覆盖。
"""

import os
from pathlib import Path
from typing import Dict, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# ========== 路径配置 ==========
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MOCK_DATA_DIR = DATA_DIR / "mock"
DB_DIR = PROJECT_ROOT / "database" / "chroma"
REPORTS_DIR = PROJECT_ROOT / "reports"

# ========== Ollama 配置 ==========
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# ========== 模型配置 ==========
MODELS: Dict[str, str] = {
    "llm": os.getenv("OLLAMA_LLM_MODEL", "deepseek-r1:7b"),
    "embedding": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
}

# ========== ESG 维度配置 ==========
ESG_DIMENSIONS: Dict[str, Dict[str, str]] = {
    "E": {"name": "环境", "color": "#52c41a", "icon": "🌱"},
    "S": {"name": "社会", "color": "#1890ff", "icon": "👥"},
    "G": {"name": "治理", "color": "#faad14", "icon": "⚖️"},
}

ESG_DIMENSION_NAMES = {k: v["name"] for k, v in ESG_DIMENSIONS.items()}
ESG_COLORS = {k: v["color"] for k, v in ESG_DIMENSIONS.items()}
ESG_ICONS = {k: v["icon"] for k, v in ESG_DIMENSIONS.items()}

# ========== 评分阈值 ==========
DEFAULT_SCORE = 50.0
GAP_THRESHOLD_HIGH = 15.0
GAP_THRESHOLD_MEDIUM = 8.0
AHP_CONSISTENCY_THRESHOLD = 0.1
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.6

# ========== AHP 配置 ==========
AHP_RI_TABLE: Dict[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}

AHP_SCALE_LABELS: Dict[int, str] = {
    1: "同等重要",
    3: "稍微重要",
    5: "明显重要",
    7: "强烈重要",
    9: "极端重要",
}

# ========== UI 配置 ==========
ANALYSIS_YEARS: List[str] = ["2025", "2024", "2023"]
BENCHMARK_COMPANIES: List[str] = ["维斯塔斯", "西门子歌美飒", "行业平均"]

EVALUATION_PERSPECTIVES: Dict[str, Dict] = {
    "financial": {
        "name": "财务稳健性（投资者视角）",
        "weights": {"E": 0.25, "S": 0.30, "G": 0.45},
    },
    "compliance": {
        "name": "合规与风险（监管视角）",
        "weights": {"E": 0.40, "S": 0.25, "G": 0.35},
    },
    "brand": {
        "name": "品牌影响力（公众视角）",
        "weights": {"E": 0.30, "S": 0.45, "G": 0.25},
    },
    "balanced": {
        "name": "均衡配置",
        "weights": {"E": 0.333, "S": 0.333, "G": 0.334},
    },
}

# ========== 数据质量阈值 ==========
DATA_QUALITY_THRESHOLDS = {
    "min_carbon_emissions": 1000,
    "min_employees": 100,
    "min_carbon_per_employee": 50000,
    "max_female_ratio": 1.0,
    "max_board_independence": 1.0,
}

# ========== 版本信息 ==========
VERSION = "1.2.0"
APP_NAME = "ESG智能分析系统"
APP_ICON = "🌿"
