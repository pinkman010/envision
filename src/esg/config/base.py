"""基础配置

路径、版本、数据管理等基础配置项。
"""

import os
from pathlib import Path
from typing import Dict

# 项目根目录 (src/esg/config/base.py -> src/esg/config -> src/esg -> src -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()

# ========== 路径配置 ==========
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "01_raw"
EXTRACTED_DATA_DIR = DATA_DIR / "02_extracted"
FUSED_DATA_DIR = DATA_DIR / "03_fused"
COMPLETED_DATA_DIR = DATA_DIR / "04_completed"
PROCESSED_DATA_DIR = DATA_DIR / "processed"  # 向后兼容
MOCK_DATA_DIR = DATA_DIR / "mock"
UPLOADS_DIR = DATA_DIR / "uploads"
REPORTS_DIR = DATA_DIR / "reports"

# 向量和数据库存储
VECTOR_DIR = PROJECT_ROOT / "storage" / "vector"
DB_DIR = VECTOR_DIR

# ========== Ollama 配置 ==========
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# ========== 模型配置 ==========
MODELS: Dict[str, str] = {
    "llm": os.getenv("OLLAMA_LLM_MODEL", "deepseek-r1:1.5b"),
    "embedding": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
}

# ========== 版本信息 ==========
VERSION = "Demo v1.2.0"
APP_NAME = "ESG智能分析系统"
APP_ICON = "🌿"

# ========== 数据版本控制配置 ==========
DATA_VERSION_CONFIG = {
    "version_format": "{major}.{minor}.{patch}",
    "current_version": "1.0.0",
    "version_history_file": "data/.version_history.json",
    "backup_count": 5,
    "auto_backup": True,
    "compatibility_matrix": {
        "1.0.0": {"compatible_with": ["0.9.x", "1.0.x"], "breaking_changes": []}
    },
}

# ========== 数据血缘追踪配置 ==========
DATA_LINEAGE_CONFIG = {
    "enabled": True,
    "track_sources": True,
    "track_transformations": True,
    "storage_type": "json",  # 可选: json, sqlite
    "lineage_file": "data/.lineage.json",
}
