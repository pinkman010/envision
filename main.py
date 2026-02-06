# /envision/main.py
"""项目入口 - 增强版，包含RAG问答功能"""

import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.esg_engine import ESGAnalysisEngine
from extractor.pdf_extractor import PDFTextExtractor
from extractor.metric_extractor import MetricExtractor
from completion.data_completion import SimpleCompletionEngine
from completion.report_generator import ReportGenerator
from utils.file_utils import save_uploaded_file

# RAG相关导入
try:
    from core.rag_engine import RAGEngine, get_rag_engine
    from vector_db.chroma_store import get_db_store, load_and_index_documents
    HAS_RAG = True
except ImportError as e:
    HAS_RAG = False
    print(f"RAG功能不可用: {e}")


def init_rag():
    """初始化RAG系统"""
    if not HAS_RAG:
        return False
    
    try:
        db_store = get_db_store()
        # 如果数据库为空，自动索引文档
        doc_count = db_store.collection.count()
        if doc_count == 0:
            with st.spinner("正在构建知识库向量索引..."):
                data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
                if os.path.exists(data_dir):
                    count = load_and_index_documents(data_dir, db_store)
                    st.success(f"知识库构建完成，索引了 {count} 个文档片段")
                else:
                    st.warning(f"数据目录不存在: {data_dir}")
        return True
    except ImportError as e:
        st.error(f"RAG依赖缺失: {e}")
        return False
    except Exception as e:
        st.error(f"RAG初始化失败: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False


def render_rag_chat():
    """渲染RAG问答对话框"""
    st.markdown("---")
    st.markdown("### 🤖 ESG智能问答助手")
    st.caption("基于本地大模型(deepseek-r1:7b) + RAG检索增强")
    
    # 初始化RAG
    if not HAS_RAG:
        st.warning("""
        ⚠️ **RAG功能不可用**
        
        请安装以下依赖：
        ```bash
        pip install chromadb
        ```
        """)
        return
    
    if 'rag_initialized' not in st.session_state:
        with st.spinner("正在初始化RAG系统..."):
            st.session_state.rag_initialized = init_rag()
    
    if not st.session_state.rag_initialized:
        st.error("""
        ❌ **RAG初始化失败**
        
        可能的原因：
        1. ChromaDB版本不兼容 - 尝试删除 `chroma_db` 文件夹后重启
        2. Ollama服务未启动 - 运行 `ollama serve`
        3. 依赖缺失 - 运行 `pip install chromadb>=0.4.0`
        
        请检查错误信息并修复后刷新页面。
        """)
        return
    
    # 显示知识库状态
    try:
        db_store = get_db_store()
        stats = db_store.get_stats()
        if stats.get('status') == '正常':
            st.success(f"📚 知识库状态: {stats['total_documents']} 个文档片段")
        else:
            st.warning(f"📚 知识库状态: {stats.get('status', '未知')} - {stats.get('error', '')}")
    except Exception as e:
        st.error(f"获取知识库状态失败: {e}")
    
    # 初始化聊天历史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 显示聊天历史
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            if msg['role'] == 'assistant':
                # 显示思维过程（可折叠）
                if msg.get('reasoning'):
                    with st.expander("🧠 查看深度思考过程", expanded=False):
                        st.markdown(msg['reasoning'])
                
                # 显示答案
                st.markdown(msg['content'])
                
                # 显示参考来源
                if msg.get('sources'):
                    with st.expander("📚 查看参考来源", expanded=False):
                        for i, source in enumerate(msg['sources'], 1):
                            meta = source.get('metadata', {})
                            score = source.get('score', 0)
                            st.markdown(f"""
                            **来源{i}**: `{meta.get('source', '未知')}`  
                            **位置**: {meta.get('position', '未知')}  
                            **相关度**: {score:.2%}
                            """
                            )
                            with st.code(source.get('text', '')[:300] + "...", language='text'):
                                pass
                            st.markdown("---")
                
                # 显示置信度
                if 'confidence' in msg:
                    confidence_color = "green" if msg['confidence'] > 0.7 else "orange" if msg['confidence'] > 0.4 else "red"
                    st.caption(f"置信度: :{confidence_color}[{msg['confidence']:.0%}]")
            else:
                st.markdown(msg['content'])
    
    # 用户输入
    if prompt := st.chat_input("请输入您关于ESG的问题..."):
        # 添加用户消息
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt
        })
        
        with st.chat_message('user'):
            st.markdown(prompt)
        
        # 生成回答
        with st.chat_message('assistant'):
            with st.spinner("正在检索知识库并生成回答..."):
                try:
                    rag_engine = get_rag_engine()
                    response = rag_engine.query(prompt, top_k=5)
                    
                    # 显示思维过程
                    if response.reasoning:
                        with st.expander("🧠 查看深度思考过程", expanded=True):
                            st.markdown(response.reasoning)
                    
                    # 显示答案
                    st.markdown(response.answer)
                    
                    # 显示参考来源
                    if response.sources:
                        with st.expander("📚 查看参考来源", expanded=False):
                            for i, source in enumerate(response.sources, 1):
                                meta = source.get('metadata', {})
                                score = source.get('score', 0)
                                st.markdown(f"""
                                **来源{i}**: `{meta.get('source', '未知')}`  
                                **位置**: {meta.get('position', '未知')}  
                                **相关度**: {score:.2%}
                                """
                                )
                                with st.code(source.get('text', '')[:300] + "...", language='text'):
                                    pass
                                st.markdown("---")
                    
                    # 显示置信度
                    confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.4 else "red"
                    st.caption(f"置信度: :{confidence_color}[{response.confidence:.0%}]")
                    
                    # 保存到历史
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response.answer,
                        'reasoning': response.reasoning,
                        'sources': response.sources,
                        'confidence': response.confidence
                    })
                    
                except Exception as e:
                    error_msg = f"生成回答时出错: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': error_msg
                    })


def main():
    st.set_page_config(page_title="ESG评价专家系统", page_icon="🌿", layout="wide")
    
    st.title("🌿 ESG评价专家系统 v1.2")
    st.caption("集成RAG智能问答功能")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["📊 ESG分析", "💬 智能问答"])
    
    with tab1:
        render_analysis_tab()
    
    with tab2:
        render_chat_tab()


def render_analysis_tab():
    """渲染ESG分析标签页"""
    # 上传
    uploaded_file = st.file_uploader("上传ESG报告PDF", type=['pdf'])
    
    if uploaded_file:
        # 保存
        file_path = save_uploaded_file(uploaded_file)
        st.success(f"✓ 已保存: {uploaded_file.name}")
        
        # 提取文本
        with st.spinner("提取文本..."):
            pdf_extractor = PDFTextExtractor()
            result = pdf_extractor.extract_with_metadata(file_path)
            text = result['text']
            st.info(f"共提取 {len(text)} 字符")
        
        # 提取指标
        if st.button("提取ESG指标", type="primary"):
            with st.spinner("提取中..."):
                extractor = MetricExtractor()
                metrics = extractor.extract(text, result['company_name'], result['year'])
                
                # 补全
                completion = SimpleCompletionEngine()
                metrics, log = completion.complete(metrics)
                
                st.session_state.metrics = metrics
                
                # 显示结果
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("员工数", metrics.employee_count or "N/A")
                with col2:
                    st.metric("碳排放", f"{metrics.carbon_emissions:,.0f}吨" if metrics.carbon_emissions else "N/A")
                with col3:
                    st.metric("置信度", metrics.calculate_overall_confidence())
                
                # 警告
                if metrics.carbon_emissions and metrics.carbon_emissions < 10000:
                    st.error("⚠️ 碳排放数值过小，请检查单位是否为'吨'")
        
        # 分析
        if st.session_state.get('metrics') and st.button("执行分析"):
            metrics = st.session_state.metrics
            
            with st.spinner("分析中..."):
                engine = ESGAnalysisEngine()
                result = engine.analyze(metrics)
                st.session_state.result = result
            st.rerun()  # 重新运行以显示结果
        
        # 显示分析结果（在分析完成后显示）
        if st.session_state.get('result'):
            result = st.session_state.result
            metrics = st.session_state.metrics
            
            # 显示结果
            st.metric("ESG总分", f"{result.overall_score}/100")
            
            # 警告
            if result.data_quality_warnings:
                st.warning("数据质量警告:")
                for w in result.data_quality_warnings:
                    st.write(f"- {w}")
            
            # 雷达图
            import plotly.graph_objects as go
            scores = [metrics.get_dimension_score(d) for d in ['E', 'S', 'G']]
            
            fig = go.Figure(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=['环境', '社会', '治理', '环境'],
                fill='toself'
            ))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])))
            st.plotly_chart(fig)
            
            # 生成报告按钮
            if st.button("生成报告"):
                st.session_state.show_report = True
                st.rerun()
        
        # 显示报告下载（独立代码块，避免嵌套问题）
        if st.session_state.get('show_report') and st.session_state.get('result'):
            result = st.session_state.result
            metrics = st.session_state.metrics
            
            report_gen = ReportGenerator()
            md_path = report_gen.save_markdown(result)
            
            with open(md_path, 'r', encoding='utf-8') as f:
                st.download_button(
                    "📥 下载报告",
                    f.read(),
                    file_name=f"{metrics.company_name}_ESG报告.md",
                    mime="text/markdown"
                )
            
            st.markdown("### 报告预览")
            st.markdown(report_gen.generate_markdown(result))


def render_chat_tab():
    """渲染智能问答标签页"""
    st.markdown("### 💬 ESG智能问答助手")
    st.info("""
    基于 **deepseek-r1:7b** 本地大模型 + ChromaDB向量数据库实现RAG检索增强生成。
    
    **功能特点：**
    - 🔍 自动检索知识库中的相关文档
    - 🧠 展示深度思考过程（COT）
    - 📚 显示参考来源（文件名、位置、相关度）
    - ✨ 支持中文自然语言问答
    """)
    
    render_rag_chat()


if __name__ == "__main__":
    main()
