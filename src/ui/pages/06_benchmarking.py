"""
ESG对标分析中心页面
功能：多企业ESG指标横向对比、行业趋势可视化、差异化策略分析
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta

from src.core_config import settings, get_logger
from src.utils.chroma_utils import get_corpus_list, get_esg_metrics

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("📊 ESG对标分析中心")
st.divider()

# 主内容区
st.markdown("### 多企业ESG指标横向对比")

# 1. 获取已处理的语料列表
corpus_list = []
try:
    corpus_list = get_corpus_list(limit=50)
except Exception as e:
    logger.warning(f"获取语料列表失败: {str(e)}")

if not corpus_list:
    st.info("📋 暂无可用语料数据，请先上传ESG报告")
    if st.button("📄 前往语料管理中心", use_container_width=True):
        st.switch_page("pages/02_corpus.py")
    st.stop()

# 2. 选择对比企业
st.subheader("🏢 选择对比企业")
st.caption(f"系统已收录 {len(corpus_list)} 份ESG报告")

# 默认选中所有企业
selected_corpus_ids = st.multiselect(
    "选择要对比的企业（建议2-5家）",
    options=[c["corpus_id"] for c in corpus_list],
    default=[c["corpus_id"] for c in corpus_list[:min(3, len(corpus_list))]],
    format_func=lambda x: next((c["file_name"] for c in corpus_list if c["corpus_id"] == x), x),
)

if len(selected_corpus_ids) < 2:
    st.warning("⚠️ 请至少选择2家企业进行对比")
    st.stop()

# 3. 获取选中企业的ESG指标
st.subheader("📈 核心ESG指标对比")

comparison_data = []
metrics_keys = set()

for corpus_id in selected_corpus_ids:
    try:
        metrics = get_esg_metrics(corpus_id)
        corpus_info = next((c for c in corpus_list if c["corpus_id"] == corpus_id), None)
        
        company_data = {
            "corpus_id": corpus_id,
            "company_name": corpus_info["file_name"].replace(".pdf", "").replace(".docx", "") if corpus_info else corpus_id,
            "metrics": {}
        }
        
        for metric in metrics:
            key = metric.get("metric_key", "")
            if key:
                metrics_keys.add(key)
                company_data["metrics"][key] = {
                    "value": metric.get("normalized_value") or metric.get("original_value"),
                    "unit": metric.get("normalized_unit") or metric.get("original_unit"),
                    "name": metric.get("metric_name", key),
                }
        
        comparison_data.append(company_data)
    except Exception as e:
        logger.error(f"获取企业指标失败 {corpus_id}: {str(e)}")

if not comparison_data:
    st.warning("⚠️ 未能获取到任何ESG指标数据，请先完成信息抽取")
    st.stop()

# 4. 显示对比表格
if metrics_keys:
    st.markdown("#### 指标数据对比表")
    
    # 构建对比表格数据
    table_data = []
    for metric_key in sorted(metrics_keys):
        # 获取指标名称
        metric_name = metric_key
        for company in comparison_data:
            if metric_key in company["metrics"]:
                metric_name = company["metrics"][metric_key]["name"]
                break
        
        row = {"指标": metric_name}
        for company in comparison_data:
            if metric_key in company["metrics"]:
                value = company["metrics"][metric_key]["value"]
                unit = company["metrics"][metric_key]["unit"]
                row[company["company_name"]] = f"{value} {unit}" if value is not None else "N/A"
            else:
                row[company["company_name"]] = "未披露"
        
        table_data.append(row)
    
    st.dataframe(table_data, use_container_width=True, hide_index=True)

# 5. 可视化对比图表
st.markdown("#### 可视化对比")

# 环境指标对比
env_metrics = ["scope1_emission", "scope2_emission", "scope3_emission", "renewable_energy_ratio"]
available_env_metrics = [m for m in env_metrics if m in metrics_keys]

if available_env_metrics:
    st.markdown("**🌱 环境指标对比**")
    
    for metric_key in available_env_metrics:
        chart_data = []
        metric_name = metric_key
        
        for company in comparison_data:
            if metric_key in company["metrics"]:
                metric_info = company["metrics"][metric_key]
                chart_data.append({
                    "企业": company["company_name"][:15] + "..." if len(company["company_name"]) > 15 else company["company_name"],
                    "数值": metric_info["value"] or 0,
                })
                metric_name = metric_info["name"]
        
        if chart_data:
            st.markdown(f"*{metric_name}*")
            st.bar_chart(chart_data, x="企业", y="数值", use_container_width=True)

# 社会指标对比
social_metrics = ["total_employees", "female_ratio", "trir", "ltir"]
available_social_metrics = [m for m in social_metrics if m in metrics_keys]

if available_social_metrics:
    st.markdown("**👥 社会指标对比**")
    
    for metric_key in available_social_metrics:
        chart_data = []
        metric_name = metric_key
        
        for company in comparison_data:
            if metric_key in company["metrics"]:
                metric_info = company["metrics"][metric_key]
                chart_data.append({
                    "企业": company["company_name"][:15] + "..." if len(company["company_name"]) > 15 else company["company_name"],
                    "数值": metric_info["value"] or 0,
                })
                metric_name = metric_info["name"]
        
        if chart_data:
            st.markdown(f"*{metric_name}*")
            st.bar_chart(chart_data, x="企业", y="数值", use_container_width=True)

# 6. 行业基准分析
st.markdown("### 📊 行业基准分析")

if metrics_keys:
    st.info("📋 基于已收录的企业数据计算行业基准值")
    
    benchmark_data = []
    for metric_key in sorted(metrics_keys):
        values = []
        metric_name = metric_key
        unit = ""
        
        for company in comparison_data:
            if metric_key in company["metrics"]:
                value = company["metrics"][metric_key]["value"]
                if value is not None:
                    values.append(value)
                    metric_name = company["metrics"][metric_key]["name"]
                    unit = company["metrics"][metric_key]["unit"]
        
        if values:
            import statistics
            benchmark_data.append({
                "指标": metric_name,
                "单位": unit,
                "样本数": len(values),
                "平均值": round(statistics.mean(values), 2),
                "中位数": round(statistics.median(values), 2),
                "最小值": round(min(values), 2),
                "最大值": round(max(values), 2),
            })
    
    if benchmark_data:
        st.dataframe(benchmark_data, use_container_width=True, hide_index=True)
    else:
        st.caption("暂无足够数据进行基准分析")

# 7. 差异化策略建议（基于白盒规则）
st.markdown("### 💡 差异化策略建议")
st.caption("基于ISSB/SASB/HKEX标准的新能源行业ESG披露要求")

with st.expander("点击查看策略建议框架"):
    st.markdown("""
    **环境维度（E）**
    - 范围1/2/3温室气体排放披露完整性
    - 可再生能源使用比例与行业对标
    - 碳减排目标设定与进展追踪
    
    **社会维度（S）**
    - 员工多元化与包容性指标
    - 职业健康与安全绩效（TRIR/LTIR）
    - 供应链劳工标准管理
    
    **治理维度（G）**
    - ESG治理架构与董事会监督
    - 气候相关风险识别与披露（TCFD）
    - 利益相关方沟通机制
    """)

st.divider()

# 8. 导出对比报告
st.subheader("📤 导出对比报告")
if st.button("生成对标分析报告", use_container_width=True):
    try:
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "compared_companies": [c["company_name"] for c in comparison_data],
            "comparison_table": table_data if metrics_keys else [],
            "benchmark_analysis": benchmark_data if metrics_keys else [],
        }
        
        st.download_button(
            label="下载JSON格式报告",
            data=json.dumps(report_data, ensure_ascii=False, indent=2),
            file_name=f"ESG_benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )
        st.success("✅ 报告生成成功")
    except Exception as e:
        st.error(f"❌ 报告生成失败: {str(e)}")
        logger.error(f"报告生成失败: {str(e)}", exc_info=True)
