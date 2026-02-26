"""
披露优化与策略助手页面（合规提示+内容生成）
功能：基于ISSB/SASB/HKEX标准的合规风险提示、标准化披露文本生成
"""

import streamlit as st
import requests
import json
from datetime import datetime

from src.core_config import settings, get_logger

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("⚠️ 披露优化与策略助手")
st.divider()

# 检查是否有信息抽取结果
if "extract_result" not in st.session_state or not st.session_state.extract_result:
    st.warning("⚠️ 请先在「实质性议题分析中心」完成信息抽取")
    if st.button("🔍 前往信息抽取", use_container_width=True):
        st.switch_page("pages/03_materiality.py")
    st.stop()

# 合规声明
st.error(
    "⚠️ **重要提示**：\n\n"
    "1. 本页面内容仅为合规风险提示，不构成任何合规决策；\n"
    "2. 最终决策权100%在企业ESG团队手里；\n"
    "3. 所有用于对外披露的内容，必须经人工复核确认。"
)

extract_result = st.session_state.extract_result

# 初始化session_state
if "compliance_result" not in st.session_state:
    st.session_state.compliance_result = None
if "generated_content" not in st.session_state:
    st.session_state.generated_content = None

# ==================== 第一部分：合规风险提示 ====================
st.markdown("### 📋 合规风险提示")

if st.button("🔍 获取合规提示", use_container_width=True, type="primary"):
    with st.spinner("正在生成合规提示，请稍候..."):
        try:
            logger.info("用户请求合规提示")
            request_data = {"extract_result": extract_result}
            response = requests.post(
                f"{settings.API_BASE_URL}{settings.API_PREFIX}/compliance/hint",
                json=request_data,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            
            if result["code"] == 200:
                st.session_state.compliance_result = result["data"]
                st.success("✅ 合规提示生成成功！")
                logger.info("合规提示生成成功")
            else:
                st.error(f"❌ 合规提示生成失败: {result['message']}")
                logger.error(f"合规提示生成失败: {result['message']}")
        
        except Exception as e:
            st.error(f"❌ 系统错误: {str(e)}")
            logger.error(f"合规提示请求失败: {str(e)}", exc_info=True)

# 显示合规提示结果
if st.session_state.compliance_result:
    compliance_data = st.session_state.compliance_result
    compliance_notes = compliance_data.get("compliance_notes", [])
    
    if compliance_notes:
        st.subheader("⚠️ 风险详情")
        
        # 按风险等级分组
        risk_levels = {"high": [], "medium": [], "low": []}
        for note in compliance_notes:
            level = note.get("risk_level", "low").lower()
            if level in risk_levels:
                risk_levels[level].append(note)
            else:
                risk_levels["low"].append(note)
        
        # 显示高风险
        if risk_levels["high"]:
            st.markdown("**🔴 高风险**")
            for note in risk_levels["high"]:
                with st.expander(f"{note.get('field_name', '未知字段')} - {note.get('standard_id', 'N/A')}"):
                    st.markdown(f"**标准**: {note.get('standard_id', 'N/A')}")
                    st.markdown(f"**风险等级**: 🔴 高")
                    st.markdown(f"**提示内容**: {note.get('note', 'N/A')}")
                    if note.get("recommendation"):
                        st.markdown(f"**改进建议**: {note['recommendation']}")
        
        # 显示中风险
        if risk_levels["medium"]:
            st.markdown("**🟡 中风险**")
            for note in risk_levels["medium"]:
                with st.expander(f"{note.get('field_name', '未知字段')} - {note.get('standard_id', 'N/A')}"):
                    st.markdown(f"**标准**: {note.get('standard_id', 'N/A')}")
                    st.markdown(f"**风险等级**: 🟡 中")
                    st.markdown(f"**提示内容**: {note.get('note', 'N/A')}")
                    if note.get("recommendation"):
                        st.markdown(f"**改进建议**: {note['recommendation']}")
        
        # 显示低风险
        if risk_levels["low"]:
            st.markdown("**🟢 低风险/提示**")
            for note in risk_levels["low"]:
                with st.expander(f"{note.get('field_name', '未知字段')} - {note.get('standard_id', 'N/A')}"):
                    st.markdown(f"**标准**: {note.get('standard_id', 'N/A')}")
                    st.markdown(f"**风险等级**: 🟢 低")
                    st.markdown(f"**提示内容**: {note.get('note', 'N/A')}")
    else:
        st.success("✅ 未发现明显合规风险")

st.divider()

# ==================== 第二部分：内容生成 ====================
st.markdown("### 📝 标准化披露文本生成")
st.caption("基于人工确认后的结构化数据，按固定模板生成标准化分析文本")

# 准备确认数据
extraction_results = extract_result.get("extraction_results", [])
passed_results = [r for r in extraction_results if r.get("validation_status") == "passed"]

if not passed_results:
    st.warning("⚠️ 没有校验通过的抽取结果，无法生成披露文本")
else:
    st.markdown(f"**可用数据**: {len(passed_results)} 条校验通过的抽取结果")
    
    # 选择模板类型
    template_type = st.selectbox(
        "选择生成模板",
        options=["analysis_report", "benchmark_report", "disclosure_summary"],
        format_func=lambda x: {
            "analysis_report": "📊 议题分析报告",
            "benchmark_report": "📈 对标分析报告",
            "disclosure_summary": "📄 披露要点摘要",
        }.get(x, x),
    )
    
    # 构建确认数据
    confirmed_data = {
        "company_name": extract_result.get("corpus_metadata", {}).get("file_name", "未知企业"),
        "report_year": extract_result.get("corpus_metadata", {}).get("report_year", datetime.now().year),
        "extraction_results": [
            {
                "field_name": r["field_name"],
                "extracted_content": r["extracted_content"],
                "similarity": r.get("similarity"),
            }
            for r in passed_results
        ],
    }
    
    if st.button("🚀 生成披露文本", use_container_width=True, type="primary"):
        with st.spinner("正在生成标准化文本，请稍候..."):
            try:
                logger.info(f"用户请求内容生成，模板: {template_type}")
                request_data = {
                    "confirmed_data": confirmed_data,
                    "template_type": template_type,
                }
                response = requests.post(
                    f"{settings.API_BASE_URL}{settings.API_PREFIX}/content/generate",
                    json=request_data,
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
                
                if result["code"] == 200:
                    st.session_state.generated_content = result["data"]
                    st.success("✅ 披露文本生成成功！")
                    logger.info("内容生成成功")
                else:
                    st.error(f"❌ 内容生成失败: {result['message']}")
                    logger.error(f"内容生成失败: {result['message']}")
            
            except Exception as e:
                st.error(f"❌ 系统错误: {str(e)}")
                logger.error(f"内容生成请求失败: {str(e)}", exc_info=True)
    
    # 显示生成的内容
    if st.session_state.generated_content:
        content_data = st.session_state.generated_content
        generated_text = content_data.get("generated_content", "")
        
        st.subheader("📄 生成的披露文本")
        st.text_area(
            "披露文本内容（可编辑）",
            value=generated_text,
            height=400,
        )
        
        # 导出选项
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 下载文本",
                data=generated_text,
                file_name=f"ESG_disclosure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            if st.button("✅ 确认并进入人工复核", use_container_width=True):
                # 保存到session_state供复核页面使用
                st.session_state.pending_review_content = {
                    "template_type": template_type,
                    "generated_content": generated_text,
                    "confirmed_data": confirmed_data,
                    "generated_at": datetime.now().isoformat(),
                }
                st.switch_page("pages/05_review.py")

st.divider()

# ==================== 第三部分：披露标准参考 ====================
st.markdown("### 📚 披露标准参考")

with st.expander("ISSB IFRS S1/S2 核心要求"):
    st.markdown("""
    **IFRS S1 - 可持续发展相关财务信息披露一般要求**
    - 治理：监督可持续发展相关风险和机遇的治理流程、控制措施和程序
    - 战略：披露可持续发展相关风险和机遇如何影响企业战略和决策
    - 风险管理：披露识别、评估和管理可持续发展相关风险的流程
    - 指标和目标：披露用于衡量和管理可持续发展相关风险和机遇的指标和目标
    
    **IFRS S2 - 气候相关披露**
    - 气候相关风险和机遇的治理
    - 气候相关风险和机遇的战略
    - 气候相关风险管理
    - 气候相关指标和目标（包括范围1/2/3温室气体排放）
    """)

with st.expander("SASB 可再生能源行业标准"):
    st.markdown("""
    **环境维度**
    - 温室气体排放（范围1/2/3）
    - 能源管理（可再生能源使用比例）
    - 水资源管理
    - 废弃物管理
    
    **社会维度**
    - 员工健康与安全
    - 员工多元化与包容性
    - 社区关系
    - 供应链劳工标准
    
    **治理维度**
    - 董事会独立性
    - 商业道德
    - 政治支出透明度
    """)

with st.expander("HKEX ESG报告指引"):
    st.markdown("""
    **强制披露要求**
    - 董事会声明
    - 汇报原则（重要性、量化、一致性、平衡）
    - 汇报范围
    
    **环境范畴（不遵守就解释）**
    - A1: 排放物
    - A2: 资源使用
    - A3: 环境及天然资源
    - A4: 气候变化
    
    **社会范畴（不遵守就解释）**
    - B1: 雇佣
    - B2: 健康与安全
    - B3: 发展及培训
    - B4: 劳工准则
    - B5: 供应链管理
    - B6: 产品责任
    - B7: 反贪污
    - B8: 社区投资
    """)

st.divider()

# 下一步操作
st.subheader("➡️ 下一步操作")
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ 进入人工复核", use_container_width=True):
        st.switch_page("pages/05_review.py")
with col2:
    if st.button("📊 查看对标分析", use_container_width=True):
        st.switch_page("pages/06_benchmarking.py")
