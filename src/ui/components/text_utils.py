"""
通用文本UI组件：字符级高亮、原文跳转
ESG合规核心组件：支持点击抽取内容直接跳转到原文对应位置
"""

import streamlit as st


def highlight_text(
    original_text: str,
    char_start: int,
    char_end: int,
    color: str = "#00A86B",  # 远景能源绿色
) -> str:
    """
    生成带高亮的HTML文本
    :param original_text: 完整原文
    :param char_start: 高亮起始位置
    :param char_end: 高亮结束位置
    :param color: 高亮颜色
    :return: HTML格式的高亮文本
    """
    if char_start < 0 or char_end > len(original_text) or char_start >= char_end:
        return original_text
    before = original_text[:char_start]
    highlight = original_text[char_start:char_end]
    after = original_text[char_end:]
    return f"{before}<mark style='background-color:{color};color:white;'>{highlight}</mark>{after}"


def jump_to_anchor(
    anchor_id: str,
    button_text: str = "📄 跳转到原文",
) -> None:
    """
    生成跳转到原文锚点的按钮（Streamlit组件）
    
    TODO[P2]: 当前未在项目中使用，作为预留UI组件保留
    - 设计用途：在分析结果页面提供"跳转到原文"快捷按钮
    - 使用场景：当用户查看AI提取的要点时，可一键定位到原文出处
    - 依赖要求：需要与语料解析模块的锚点标记功能配合使用
    
    Issue: 当前为预留组件，待原文锚点标记功能实现后启用
    预计启用时间：v1.5 版本
    
    :param anchor_id: 锚点ID
    :param button_text: 按钮文本
    """
    st.markdown(
        f"<a href='#{anchor_id}' style='text-decoration:none;'>"
        f"<button style='background-color:#00A86B;color:white;border:none;border-radius:4px;padding:0.3rem 0.8rem;cursor:pointer;'>"
        f"{button_text}"
        f"</button></a>",
        unsafe_allow_html=True,
    )
