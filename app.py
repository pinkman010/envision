"""ESG智能分析系统 - 主应用"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st

from src.config import ESG_COLORS, ESG_DIMENSION_NAMES
from src.models.esg import ESGMetrics
from src.services.esg_analysis import ESGAnalysisService
from src.services.rag import RAGEngine
from src.extractors.pdf import PDFExtractor
from src.extractors.metrics import MetricsExtractor
from src.generators.report import ReportGenerator
from src.utils.file import save_uploaded_file

# 页面配置
st.set_page_config(page_title="ESG智能分析系统", page_icon="🌿", layout="wide")


def init_session():
    """初始化会话状态"""
    defaults = {
        "metrics": None,
        "result": None,
        "chat_history": [],
        "rag_ready": False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_analysis_tab():
    """分析标签页"""
    st.header("📊 ESG分析")
    
    uploaded = st.file_uploader("上传ESG报告PDF", type=["pdf"])
    
    if uploaded:
        path = save_uploaded_file(uploaded)
        st.success(f"已上传: {uploaded.name}")
        
        # 提取文本
        with st.spinner("提取文本中..."):
            extractor = PDFExtractor()
            result = extractor.extract_with_meta(path)
            st.info(f"提取了 {len(result['text'])} 字符")
        
        # 提取指标
        if st.button("🔍 提取ESG指标", type="primary"):
            with st.spinner("分析中..."):
                metrics_ext = MetricsExtractor()
                metrics = metrics_ext.extract(
                    result["text"], 
                    result["company"], 
                    result["year"]
                )
                st.session_state.metrics = metrics
        
        # 显示指标
        if st.session_state.metrics:
            metrics = st.session_state.metrics
            cols = st.columns(3)
            with cols[0]:
                st.metric("员工数", metrics.employee_count or "N/A")
            with cols[1]:
                val = f"{metrics.carbon_emissions:,.0f}吨" if metrics.carbon_emissions else "N/A"
                st.metric("碳排放", val)
            with cols[2]:
                st.metric("置信度", metrics.calculate_overall_confidence())
        
        # 执行分析
        if st.session_state.metrics and st.button("📈 执行分析"):
            with st.spinner("分析中..."):
                service = ESGAnalysisService()
                result = service.analyze(st.session_state.metrics)
                st.session_state.result = result
        
        # 显示结果
        if st.session_state.result:
            result = st.session_state.result
            
            st.metric("ESG总分", f"{result.overall_score}/100")
            
            # 警告
            if result.data_quality_warnings:
                for w in result.data_quality_warnings:
                    st.warning(w)
            
            # 雷达图
            import plotly.graph_objects as go
            scores = [result.metrics.get_dimension_score(d) for d in ["E", "S", "G"]]
            fig = go.Figure(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=["环境", "社会", "治理", "环境"],
                fill="toself"
            ))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])))
            st.plotly_chart(fig)
            
            # 下载报告
            if st.button("📄 生成报告"):
                gen = ReportGenerator()
                content = gen.generate(result)
                st.download_button(
                    "下载Markdown报告",
                    content,
                    file_name=f"{result.metrics.company_name}_ESG报告.md"
                )


def render_chat_tab():
    """问答标签页"""
    st.header("💬 智能问答")
    st.caption("基于 deepseek-r1:7b + RAG检索")
    
    # 初始化RAG
    if not st.session_state.rag_ready:
        try:
            from src.services.vector_store import VectorStore
            store = VectorStore()
            if store.count() == 0:
                st.info("知识库为空，请先上传文档进行分析")
            st.session_state.rag_ready = True
        except Exception as e:
            st.error(f"RAG初始化失败: {e}")
            return
    
    # 显示历史
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                if msg.get("reasoning"):
                    with st.expander("🧠 思考过程"):
                        st.markdown(msg["reasoning"])
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("📚 参考来源"):
                        for s in msg["sources"][:3]:
                            st.caption(f"{s['metadata'].get('source', '未知')} | 相关度: {s['score']:.1%}")
            else:
                st.markdown(msg["content"])
    
    # 输入
    if prompt := st.chat_input("请输入ESG相关问题..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("检索中..."):
                try:
                    engine = RAGEngine()
                    resp = engine.query(prompt, top_k=3)
                    
                    if resp.reasoning:
                        with st.expander("🧠 思考过程", expanded=True):
                            st.markdown(resp.reasoning)
                    
                    st.markdown(resp.answer)
                    
                    if resp.sources:
                        with st.expander("📚 参考来源"):
                            for s in resp.sources:
                                st.caption(f"**{s['metadata'].get('source', '未知')}** | "
                                         f"位置: {s['metadata'].get('position', '未知')} | "
                                         f"相关度: {s['score']:.1%}")
                    
                    st.caption(f"置信度: {resp.confidence:.0%}")
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": resp.answer,
                        "reasoning": resp.reasoning,
                        "sources": resp.sources,
                        "confidence": resp.confidence
                    })
                    
                except Exception as e:
                    st.error(f"生成失败: {e}")


def main():
    """主函数"""
    init_session()
    
    st.title("🌿 ESG智能分析系统 v1.2")
    
    tab1, tab2 = st.tabs(["📊 ESG分析", "💬 智能问答"])
    
    with tab1:
        render_analysis_tab()
    
    with tab2:
        render_chat_tab()


if __name__ == "__main__":
    main()
