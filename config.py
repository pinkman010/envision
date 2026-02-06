"""ESG评价专家系统 - 全局配置"""

import os

# 项目根目录（config.py所在目录的上级）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(PROJECT_ROOT, "data")
MOCK_DATA_PATH = os.path.join(DATA_PATH, "mock")

# Ollama配置
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# 模型配置
MODELS = {
    "llm": os.getenv("OLLAMA_LLM_MODEL", "deepseek-r1:7b"),
    "embedding": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
}

# ESG维度定义（向后兼容）
ESG_DIMENSIONS = {
    "E": "环境",
    "S": "社会",
    "G": "治理"
}

# MVP指标定义（向后兼容）
MVP_METRICS = {
    "E": ["carbon_emissions", "renewable_energy_ratio", "energy_efficiency", "water_consumption", "waste_recycling_rate"],
    "S": ["employee_count", "female_ratio", "training_hours", "safety_incidents", "community_investment"],
    "G": ["board_independence_ratio", "ethics_training_coverage", "esg_report_quality"]
}
