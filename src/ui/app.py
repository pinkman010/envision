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

from src.core_config.settings import settings
from src.core_config import ensure_all_paths

ensure_all_paths()

# ========== 使用 st.navigation 完全接管页面导航 ==========

# 1. 定义所有页面
page_01 = st.Page(
    "pages/01_首页_概览看板.py",
    title="首页概览",
    icon="🏠",
    default=True  # 设为默认首页
)
page_02 = st.Page(
    "pages/02_ESG语料管理中心.py",
    title="报告上传",
    icon="📄"
)
page_03 = st.Page(
    "pages/03_实质性议题分析中心.py",
    title="议题识别",
    icon="🔍"
)
page_04 = st.Page(
    "pages/04_ESG对标分析中心.py",
    title="对标分析",
    icon="📊"
)
page_05 = st.Page(
    "pages/05_披露优化与策略助手.py",
    title="披露优化",
    icon="⚠️"
)
page_06 = st.Page(
    "pages/06_审计日志中心.py",
    title="审计日志",
    icon="📜"
)
page_07 = st.Page(
    "pages/07_规则配置中心.py",
    title="规则配置",
    icon="⚙️"
)
page_08 = st.Page(
    "pages/08_人工复核中心.py",
    title="人工复核",
    icon="✅"
)

# 2. 页面分组（用于侧边栏分组显示）
pages = {
    "🧭核心功能导航": [page_01, page_02, page_03, page_04, page_05, page_06, page_07, page_08],
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
        --primary-color: #00A86B;  /* 远景能源绿色 */
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

# 5. 初始化导航（position="sidebar" 会自动在侧边栏渲染导航）
pg = st.navigation(pages, position="sidebar")

# 6. 渲染侧边栏附加内容（合规声明）
with st.sidebar:
    st.markdown("### 合规声明")
    st.warning(
        "⚠️ 本系统AI输出仅为辅助参考，不构成任何披露建议。\n"
        "所有对外披露内容需经企业ESG团队人工复核确认。"
    )

# 7. 运行选中的页面
pg.run()