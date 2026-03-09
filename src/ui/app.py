"""
Streamlit 前端 UI 入口（st.navigation 架构）
功能：全局主题配置、完全自定义导航、无自动导航栏

启动命令: streamlit run src/ui/app.py
"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.config import ensure_all_paths

ensure_all_paths()

# ========== 使用 st.navigation 完全接管页面导航 ==========

# 1. 定义所有页面（按业务流程顺序）
page_01 = st.Page("pages/01_home.py", title="首页概览", icon="🏠", default=True)
page_02 = st.Page("pages/02_corpus.py", title="报告上传", icon="📄")
page_03 = st.Page("pages/03_materiality.py", title="议题识别", icon="🔍")
page_04 = st.Page("pages/04_analysis.py", title="差距分析", icon="⚠️")
page_05 = st.Page("pages/05_review.py", title="人工复核", icon="✅")
page_06 = st.Page("pages/06_benchmarking.py", title="对标分析", icon="📊")
page_07 = st.Page("pages/07_audit.py", title="审计日志", icon="📜")
page_08 = st.Page("pages/08_rules.py", title="规则配置", icon="⚙️")

# 2. 页面分组（按业务流程位置）
pages = {
    "📊 核心业务流程": [page_01, page_02, page_03, page_04, page_05, page_06],
    "⚙️ 系统管理功能": [page_07, page_08],
}

# 3. 全局页面配置
st.set_page_config(
    page_title=settings.PROJECT_NAME,
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"# {settings.PROJECT_NAME}\n{settings.PROJECT_DESCRIPTION}\n版本：v{settings.VERSION}",
    },
)

# 4. 应用主题样式
st.markdown(
    """
    <style>
    :root {
        --primary-color: #00A86B;
        --background-color: #F8F9FA;
        --secondary-background-color: #FFFFFF;
        --text-color: #212529;
        --font: "Microsoft YaHei", "PingFang SC", sans-serif;
    }
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #008F5A;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 5. 初始化导航
pg = st.navigation(pages, position="sidebar")

# 6. 渲染侧边栏附加内容
with st.sidebar:
    st.markdown("### 合规声明")
    st.warning(
        "本系统AI输出仅为辅助参考，不构成任何披露建议。\n"
        "所有对外披露内容需经企业ESG团队人工复核确认。"
    )

# 7. 运行选中的页面
pg.run()
