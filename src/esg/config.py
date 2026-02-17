"""ESG分析系统配置模块

提供全局配置常量和默认值。
"""

# ============ 应用基本信息 ============
APP_NAME: str = "ESG智能分析系统"
APP_ICON: str = "🌱"
VERSION: str = "2.0.0"

# ============ 分析配置 ============
ANALYSIS_YEARS: list = ["2024", "2023", "2022", "2021", "2020"]

# 行业对标企业列表
BENCHMARK_COMPANIES: list = [
    "行业平均",
    "宁德时代",
    "隆基绿能",
    "金风科技",
    "阳光电源",
    "比亚迪",
    "通威股份",
]

# ============ 颜色配置 ============
ESG_COLORS: dict = {
    "E": "#52c41a",  # 环境 - 绿色
    "S": "#1890ff",  # 社会 - 蓝色
    "G": "#722ed1",  # 治理 - 紫色
}

# 维度名称映射
ESG_DIMENSION_NAMES: dict = {
    "E": "环境",
    "S": "社会",
    "G": "治理",
}

# ============ 评分默认值 ============
DEFAULT_SCORE: float = 50.0

# ============ 数据目录 ============
import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
MOCK_DATA_DIR = PROJECT_ROOT / "data" / "mock"
