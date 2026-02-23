"""
披露优化与策略助手页面（合规提示+内容生成）
"""

import streamlit as st
import requests

from src.core_config import settings, get_logger

logger = get_logger(__name__)

st.title("⚠️ 披露优化与策略助手")
st.divider()

# 检查是否有信息抽取结果
if "extract_result" not in st.session_state or not st.session_state.extract_result:
    st.warning("⚠️ 请先在「实质性议题分析中心」完成信息抽取")
    if st.button("🔍 前往信息抽取", use_container_width=True):
        st.switch_page("page/03_实质性议题分析中心.py")
    st.stop()

st.info("🚧 该功能正在完善中，当前仅显示合规提示框架")
st.markdown("### 合规提示（仅为参考，无决策权限）")
st.warning("⚠️ 本页面内容仅为合规风险提示，不构成任何合规决策，最终决策权100%在人工手里")

# 调用合规提示接口
if st.button("🔍 获取合规提示", use_container_width=True):
    with st.spinner("正在生成合规提示，请稍候..."):
        try:
            extract_result = st.session_state.extract_result
            request_data = {"extract_result": extract_result}
            response = requests.post(
                f"http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}/compliance/hint",
                json=request_data,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            
            if result["code"] == 200:
                compliance_data = result["data"]
                compliance_notes = compliance_data.get("compliance_notes", [])
                
                if compliance_notes:
                    st.subheader("📋 合规风险提示")
                    for note in compliance_notes:
                        with st.expander(f"⚠️ {note.get('field_name', '未知字段')}"):
                            st.markdown(f"**标准**: {note.get('standard_id', 'N/A')}")
                            st.markdown(f"**风险等级**: {note.get('risk_level', 'N/A')}")
                            st.markdown(f"**提示内容**: {note.get('note', 'N/A')}")
                else:
                    st.success("✅ 未发现明显合规风险")
            else:
                st.error(f"❌ 合规提示生成失败: {result['message']}")
        
        except Exception as e:
            st.error(f"❌ 系统错误: {str(e)}")
            logger.error(f"合规提示请求失败: {str(e)}", exc_info=True)
