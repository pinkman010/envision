"""可视化配置

UI样式配置，包含图表主题、颜色方案等可视化相关配置。
"""

from typing import Dict, List

# ========== 图表颜色配置 ==========
# ESG各维度的默认颜色
ESG_CHART_COLORS: Dict[str, str] = {
    "E": "#2E7D32",  # 环境 - 绿色
    "S": "#1565C0",  # 社会 - 蓝色
    "G": "#6A1B9A",  # 治理 - 紫色
}

# 优先级颜色
PRIORITY_COLORS: Dict[str, str] = {
    "高": "#d32f2f",
    "中": "#f57c00",
    "低": "#388e3c",
}

# 状态颜色
STATUS_COLORS: Dict[str, str] = {
    "compliant": "#4caf50",
    "partial": "#ff9800",
    "non_compliant": "#f44336",
}

# ========== 图表样式配置 ==========
CHART_THEME: str = "plotly_white"

CHART_HEIGHT: int = 400

# 词云配色方案
WORDCLOUD_COLORS: List[str] = [
    "#2E7D32",
    "#1565C0",
    "#6A1B9A",
    "#00838F",
    "#C62828",
    "#EF6C00",
]

# ========== 页面布局配置 ==========
SIDEBAR_WIDTH: str = "300px"

CONTENT_MAX_WIDTH: str = "1200px"

# 卡片样式
CARD_BORDER_RADIUS: int = 10
CARD_PADDING: int = 16
