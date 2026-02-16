"""ESG UI 页面模块

包含各个功能页面的渲染函数。
"""

from src.esg.ui.pages.competitor import render_competitor_page
from src.esg.ui.pages.gap import render_gap_page
from src.esg.ui.pages.home import render_home_page
from src.esg.ui.pages.materiality import render_materiality_page
from src.esg.ui.pages.rag import render_rag_page
from src.esg.ui.pages.strategies import render_strategies_page
from src.esg.ui.pages.timing import render_timing_page
from src.esg.ui.pages.topics import render_topics_page
from src.esg.ui.pages.weights import render_weights_page

__all__ = [
    "render_home_page",
    "render_topics_page",
    "render_weights_page",
    "render_gap_page",
    "render_strategies_page",
    "render_timing_page",
    "render_rag_page",
    "render_materiality_page",
    "render_competitor_page",
]
