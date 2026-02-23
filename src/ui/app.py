"""
Streamlit前端UI入口
功能：全局主题配置、多页面应用初始化、首页概览

启动命令: streamlit run src/ui/app.py
"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core_config.settings import settings
from src.core_config.paths import UI_PAGES_DIR
from src.core_config import ensure_all_paths, init_logging

# 确保目录存在
ensure_all_paths()

# 初始化日志（仅控制台输出，Streamlit环境下不使用文件日志）
# init_logging()  # Streamlit环境下注释掉，避免文件日志冲突

# 1. 全局页面配置（必须放在最前面，否则无效）
st.set_page_config(
    page_title=settings.PROJECT_NAME,
    page_icon="🌱",  # 新能源/ESG主题图标
    layout="wide",  # 宽屏布局，适合展示数据、报告
    initial_sidebar_state="expanded",  # 默认展开侧边栏导航
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"# {settings.PROJECT_NAME}\n{settings.PROJECT_DESCRIPTION}\n版本：v{settings.VERSION}",
    },
)

# 2. 全局主题配置（可选，也可以用Streamlit的设置面板）
# 这里用远景能源的品牌色做示例（可根据实际情况修改）
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

# 3. 侧边栏全局信息（所有页面都显示）
with st.sidebar:
    st.title("🌱 " + settings.PROJECT_NAME)
    st.caption(f"版本：v{settings.VERSION}")
    st.divider()
    
    st.markdown("### 核心功能导航")
    st.page_link("pages/01_首页_概览看板.py", label="🏠 首页概览")
    st.page_link("pages/02_ESG语料管理中心.py", label="📄 语料管理")
    st.page_link("pages/03_实质性议题分析中心.py", label="🔍 实质性议题")
    st.page_link("pages/04_ESG对标分析中心.py", label="📊 对标分析")
    st.page_link("pages/05_披露优化与策略助手.py", label="⚠️ 披露优化")
    st.page_link("pages/06_审计日志中心.py", label="📜 审计日志")
    st.page_link("pages/07_规则配置中心.py", label="⚙️ 规则配置")
    st.page_link("pages/08_人工复核中心.py", label="✅ 人工复核")
    
    st.divider()
    st.markdown("### 合规声明")
    st.warning(
        "⚠️ 本系统AI输出仅为辅助参考，不构成任何披露建议。\n"
        "所有对外披露内容需经企业ESG团队人工复核确认。"
    )

# 4. 首页概览（仅当用户在根路径时显示，其他页面由pages/目录自动加载）
# 注意：Streamlit的多页面应用会自动加载pages/目录下的.py文件，无需手动注册
# 这里的首页是根路径的默认内容
st.header("🌱 新能源行业ESG披露与沟通智能分析系统")
st.subheader("规则驱动为主、AI辅助为辅的强合规分析工具")
st.divider()

# 首页核心数据看板（MVP阶段用静态数据演示，后期对接总控Agent的状态数据）
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="已接入语料库", value="120+", delta="TOP100新能源企业")
with col2:
    st.metric(label="覆盖披露标准", value="3套", delta="ISSB/SASB/HKEX")
with col3:
    st.metric(label="核心实质性议题", value="15个", delta="新能源行业专属")
with col4:
    st.metric(label="合规审计覆盖率", value="100%", delta="字符级双向溯源")

st.divider()

# 首页快速操作入口
st.subheader("🚀 快速开始")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📄 导入ESG语料", use_container_width=True):
        st.switch_page("pages/02_ESG语料管理中心.py")
with col2:
    if st.button("🔍 分析实质性议题", use_container_width=True):
        st.switch_page("pages/03_实质性议题分析中心.py")
with col3:
    if st.button("📊 做企业对标分析", use_container_width=True):
        st.switch_page("pages/04_ESG对标分析中心.py")
