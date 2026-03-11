"""
ESG对标分析中心页面（规划中）
功能展示：多企业ESG指标横向对比、行业趋势可视化、差异化策略分析
"""

import streamlit as st
from src.config import get_logger

logger = get_logger(__name__)

st.title("📊 ESG对标分析中心")
st.divider()

# 状态标注
st.info(
    "🚧 **本模块正在开发中**\n\n"
    "当前版本优先实现单报告分析（语料解析 → 议题识别 → 差距分析 → 披露建议）。\n"
    "多企业对标功能将在项目后期（7月交付版本）中实现。"
)

st.divider()

# 功能架构展示
st.markdown("### 🏗️ 功能架构设计")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 数据输入")
    st.markdown("""
    - 支持同时导入 **2~10 家**企业 ESG 报告
    - 自动识别企业名称、报告年份
    - 统一单位换算（万吨→吨、GWh→MWh）
    - 对接第一组语料库（peer_reports 集合）
    """)

    st.markdown("#### 对标维度")
    st.markdown("""
    **🌱 环境（E）**
    - Scope 1 / 2 / 3 温室气体排放强度
    - 可再生能源使用比例
    - 废弃物（叶片）回收处置率
    - 单位发电量碳排放

    **👥 社会（S）**
    - 员工多元化指标（女性比例）
    - 职业健康安全（TRIR / LTIR）
    - 供应链劳工标准覆盖率

    **🏛️ 治理（G）**
    - ESG 治理架构完整性
    - 气候相关风险披露（TCFD 对齐度）
    - 董事会 ESG 监督机制
    """)

with col2:
    st.markdown("#### 分析输出")
    st.markdown("""
    - **雷达图**：多企业 ESG 综合得分可视化
    - **柱状图**：核心指标横向对比
    - **差距矩阵**：对照 ISSB / HKEX 标准的覆盖热力图
    - **对标报告**：可导出 JSON / PDF
    """)

    st.markdown("#### 参考标准")
    st.markdown("""
    | 标准 | 对标内容 |
    |---|---|
    | ISSB S1 | 一般可持续披露要求 |
    | ISSB S2 | 气候相关披露 |
    | HKEX 2024 | A 类环境强制披露 |
    | SASB EX-NF | 新能源行业专项指标 |
    """)

st.divider()

# 系统工作流说明
st.markdown("### 🔄 规划工作流：`multi_company_benchmark`")

st.markdown("""
```
输入：多份 ESG 报告
    ↓
CorpusAgent × N    # 并行解析所有报告
    ↓
RetrievalAgent × N # 并行议题识别
    ↓
AnalystAgent       # 跨企业差距对比（对照同一套标准）
    ↓
输出：对标矩阵 + 雷达图 + 行业基准报告
```
""")

st.divider()

# 开发进度
st.markdown("### 📅 开发进度")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("单报告分析", "✅ 已完成", "4月中期Demo")
with col2:
    st.metric("多企业对标", "🚧 规划中", "7月交付版本")
with col3:
    st.metric("批量处理", "📋 待启动", "7月交付版本")
