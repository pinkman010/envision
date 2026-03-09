"""
审计日志中心页面（ESG合规核心）
功能：全链路操作日志查询、日志哈希校验、审计报告导出
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.config import settings, get_logger
from src.config.paths import EXPORT_RESULTS_DIR
from src.utils.audit_utils import (
    query_audit_logs,
    verify_log_integrity,
    export_audit_logs_to_json,
    get_operation_type_stats,
    get_all_operation_types,
    get_all_operators,
)
from src.utils.hash_utils import generate_sha256_hash

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("📜 审计日志中心")
st.divider()

# 合规声明
st.error(
    "⚠️ **审计日志合规声明**：\n\n"
    "1. 所有操作日志永久留存，不可删除、不可篡改；\n"
    "2. 每条日志均带有SHA-256哈希值，用于完整性校验；\n"
    "3. 日志内容满足上市公司ESG披露审计追溯要求。"
)

# ==================== 第一部分：日志查询 ====================
st.markdown("### 🔍 审计日志查询")

# 查询条件
with st.expander("查询条件", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 获取所有操作类型
        try:
            all_operation_types = get_all_operation_types()
        except Exception as e:
            all_operation_types = []
            logger.warning(f"获取操作类型失败: {str(e)}")
        
        operation_type = st.selectbox(
            "操作类型",
            options=["全部"] + all_operation_types,
            index=0,
        )
    
    with col2:
        # 获取所有操作人
        try:
            all_operators = get_all_operators()
        except Exception as e:
            all_operators = []
            logger.warning(f"获取操作人失败: {str(e)}")
        
        operator = st.selectbox(
            "操作人",
            options=["全部"] + all_operators,
            index=0,
        )
    
    with col3:
        limit = st.number_input("返回数量", min_value=10, max_value=1000, value=100, step=10)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=30),
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now(),
        )

# 执行查询
if st.button("🔍 查询日志", use_container_width=True, type="primary"):
    with st.spinner("正在查询审计日志..."):
        try:
            # 构建查询参数
            op_type = None if operation_type == "全部" else operation_type
            op = None if operator == "全部" else operator
            start_time = datetime.combine(start_date, datetime.min.time()).isoformat()
            end_time = datetime.combine(end_date, datetime.max.time()).isoformat()
            
            logs = query_audit_logs(
                operation_type=op_type,
                operator=op,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
            
            st.session_state.audit_logs = logs
            st.success(f"✅ 查询成功，共 {len(logs)} 条日志")
            logger.info(f"审计日志查询成功: {len(logs)} 条")
        
        except Exception as e:
            st.error(f"❌ 查询失败: {str(e)}")
            logger.error(f"审计日志查询失败: {str(e)}", exc_info=True)

# 显示查询结果
if "audit_logs" in st.session_state and st.session_state.audit_logs:
    logs = st.session_state.audit_logs
    
    st.subheader(f"📋 查询结果（共 {len(logs)} 条）")
    
    # 日志统计
    success_count = len([l for l in logs if l.get("status") == "success"])
    failed_count = len([l for l in logs if l.get("status") == "failed"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总日志数", len(logs))
    with col2:
        st.metric("成功操作", success_count)
    with col3:
        st.metric("失败操作", failed_count)
    
    # 显示日志列表
    for idx, log in enumerate(logs):
        log_id = log.get("id", idx)
        timestamp = log.get("timestamp", "N/A")
        op_type = log.get("operation_type", "N/A")
        op = log.get("operator", "N/A")
        status = log.get("status", "N/A")
        log_hash = log.get("log_hash", "N/A")[:16] + "..."
        
        # 根据状态显示不同颜色
        if status == "success":
            status_emoji = "✅"
            status_color = "green"
        elif status == "failed":
            status_emoji = "❌"
            status_color = "red"
        else:
            status_emoji = "⏳"
            status_color = "orange"
        
        with st.expander(f"{status_emoji} [{timestamp}] {op_type} | 操作人: {op} | 哈希: {log_hash}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**日志ID**: {log_id}")
                st.markdown(f"**操作时间**: {timestamp}")
                st.markdown(f"**操作类型**: {op_type}")
                st.markdown(f"**操作人**: {op}")
            with col2:
                st.markdown(f"**状态**: <span style='color:{status_color};'>{status}</span>", unsafe_allow_html=True)
                st.markdown(f"**哈希值**: `{log.get('log_hash', 'N/A')}`")
            
            # 操作详情
            st.markdown("**操作详情**:")
            operation_detail = log.get("operation_detail", {})
            st.json(operation_detail)
            
            # 错误信息
            if log.get("error_info"):
                st.markdown("**错误信息**:")
                st.error(log["error_info"])
            
            # 哈希校验按钮
            if st.button(f"🔐 校验日志完整性", key=f"verify_{log_id}"):
                try:
                    is_valid = verify_log_integrity(log)
                    if is_valid:
                        st.success("✅ 日志完整性校验通过，未被篡改")
                    else:
                        st.error("❌ 日志完整性校验失败，可能存在篡改")
                except Exception as e:
                    st.error(f"❌ 校验过程出错: {str(e)}")

st.divider()

# ==================== 第二部分：日志统计 ====================
st.markdown("### 📊 操作统计")

if st.button("📈 生成操作统计", use_container_width=True):
    with st.spinner("正在生成统计..."):
        try:
            start_time = datetime.combine(start_date, datetime.min.time()).isoformat()
            end_time = datetime.combine(end_date, datetime.max.time()).isoformat()
            
            stats = get_operation_type_stats(start_time=start_time, end_time=end_time)
            
            if stats:
                st.session_state.operation_stats = stats
                st.success(f"✅ 统计生成成功，共 {len(stats)} 个操作类型")
            else:
                st.info("📋 暂无统计数据")
        
        except Exception as e:
            st.error(f"❌ 统计生成失败: {str(e)}")
            logger.error(f"操作统计生成失败: {str(e)}", exc_info=True)

if "operation_stats" in st.session_state and st.session_state.operation_stats:
    stats = st.session_state.operation_stats
    
    # 转换为表格数据
    stats_data = []
    for stat in stats:
        stats_data.append({
            "操作类型": stat["operation_type"],
            "状态": stat["status"],
            "次数": stat["count"],
        })
    
    st.dataframe(stats_data, use_container_width=True, hide_index=True)
    
    # 可视化
    import pandas as pd
    df = pd.DataFrame(stats_data)
    if not df.empty:
        st.bar_chart(df, x="操作类型", y="次数", color="状态", use_container_width=True)

st.divider()

# ==================== 第三部分：日志导出 ====================
st.markdown("### 📤 日志导出")

export_format = st.selectbox(
    "导出格式",
    options=["JSON", "CSV"],
    format_func=lambda x: {"JSON": "📄 JSON格式", "CSV": "📊 CSV格式"}.get(x, x),
)

if st.button("📥 导出日志", use_container_width=True):
    with st.spinner("正在导出日志..."):
        try:
            # 构建查询参数
            op_type = None if operation_type == "全部" else operation_type
            op = None if operator == "全部" else operator
            start_time = datetime.combine(start_date, datetime.min.time()).isoformat()
            end_time = datetime.combine(end_date, datetime.max.time()).isoformat()
            
            if export_format == "JSON":
                # JSON格式导出
                output_path = EXPORT_RESULTS_DIR / f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                export_path = export_audit_logs_to_json(
                    output_path=output_path,
                    operation_type=op_type,
                    operator=op,
                    start_time=start_time,
                    end_time=end_time,
                )
                
                # 读取文件内容供下载
                with open(export_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                st.download_button(
                    label="📥 下载JSON文件",
                    data=file_content,
                    file_name=export_path.name,
                    mime="application/json",
                    use_container_width=True,
                )
            
            else:
                # CSV格式导出
                logs = query_audit_logs(
                    operation_type=op_type,
                    operator=op,
                    start_time=start_time,
                    end_time=end_time,
                    limit=10000,
                )
                
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # 写入表头
                writer.writerow(["ID", "时间戳", "操作类型", "操作人", "状态", "哈希值", "操作详情", "错误信息"])
                
                # 写入数据
                for log in logs:
                    writer.writerow([
                        log.get("id", ""),
                        log.get("timestamp", ""),
                        log.get("operation_type", ""),
                        log.get("operator", ""),
                        log.get("status", ""),
                        log.get("log_hash", ""),
                        json.dumps(log.get("operation_detail", {}), ensure_ascii=False),
                        log.get("error_info", ""),
                    ])
                
                st.download_button(
                    label="📥 下载CSV文件",
                    data=output.getvalue(),
                    file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            
            st.success("✅ 日志导出成功")
        
        except Exception as e:
            st.error(f"❌ 导出失败: {str(e)}")
            logger.error(f"日志导出失败: {str(e)}", exc_info=True)

st.divider()

# ==================== 第四部分：哈希工具 ====================
st.markdown("### 🔐 哈希校验工具")
st.caption("手动计算SHA-256哈希值，用于内容完整性校验")

hash_input = st.text_area("输入内容", height=100)
if st.button("🔐 计算哈希值", use_container_width=True):
    if hash_input:
        hash_value = generate_sha256_hash(hash_input)
        st.code(hash_value, language="text")
        st.caption(f"哈希长度: {len(hash_value)} 字符")
    else:
        st.warning("⚠️ 请输入内容")
