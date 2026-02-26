"""
人工复核中心页面（ESG合规核心）
功能：AI输出内容人工复核、复核留痕与签名、复核结果导出
"""

import streamlit as st
import json
import hashlib
from datetime import datetime
from pathlib import Path

from src.core_config import settings, get_logger
from src.core_config.paths import EXPORT_RESULTS_DIR, SQLITE_DB_DIR
from src.utils.audit_utils import write_audit_log
from src.utils.hash_utils import generate_sha256_hash

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("✅ 人工复核中心")
st.divider()

# 合规声明
st.error(
    "⚠️ **人工复核声明**：\n\n"
    "1. 所有用于对外披露的内容，必须经人工复核确认；\n"
    "2. 复核人需对复核内容负责，复核记录永久留存；\n"
    "3. 复核记录包含复核人签名哈希，满足审计追溯要求。"
)

# 初始化复核记录数据库
def init_review_db():
    """初始化人工复核记录数据库"""
    import sqlite3
    review_db_path = SQLITE_DB_DIR / "review_records.db"
    SQLITE_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(review_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_record (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            extract_id INTEGER,
            review_user TEXT NOT NULL,
            review_status TEXT NOT NULL,
            original_content TEXT NOT NULL,
            modified_content TEXT,
            review_opinion TEXT,
            review_time TEXT NOT NULL,
            signature_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    return review_db_path

REVIEW_DB_PATH = init_review_db()

# ==================== 第一部分：待复核内容 ====================
st.markdown("### 📋 待复核内容")

# 检查是否有待复核的内容来源
has_extract_result = "extract_result" in st.session_state and st.session_state.extract_result
has_pending_content = "pending_review_content" in st.session_state and st.session_state.pending_review_content

if not has_extract_result and not has_pending_content:
    st.info("📋 暂无待复核内容，请先完成信息抽取或内容生成")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 前往信息抽取", use_container_width=True):
            st.switch_page("pages/03_materiality.py")
    with col2:
        if st.button("⚠️ 前往披露优化", use_container_width=True):
            st.switch_page("pages/04_disclosure.py")
    st.stop()

# 显示待复核的抽取结果
if has_extract_result:
    extract_result = st.session_state.extract_result
    extraction_results = extract_result.get("extraction_results", [])
    
    # 过滤出需要复核的内容（校验通过的）
    passed_results = [r for r in extraction_results if r.get("validation_status") == "passed"]
    
    if passed_results:
        st.subheader(f"🔍 信息抽取结果复核（共 {len(passed_results)} 条）")
        
        for idx, result in enumerate(passed_results):
            field_name = result["field_name"]
            extracted_content = result["extracted_content"]
            similarity = result.get("similarity", 0)
            
            with st.expander(f"字段: {field_name} | 相似度: {similarity:.2%}"):
                st.markdown(f"**字段名**: {field_name}")
                st.markdown(f"**抽取内容**: {extracted_content}")
                st.markdown(f"**相似度**: {similarity:.2%}")
                
                # 复核状态选择
                review_status = st.selectbox(
                    "复核状态",
                    options=["pending", "passed", "rejected", "modified"],
                    format_func=lambda x: {
                        "pending": "⏳ 待复核",
                        "passed": "✅ 通过",
                        "rejected": "❌ 拒绝",
                        "modified": "✏️ 修改",
                    }.get(x, x),
                    key=f"review_status_{idx}",
                )
                
                # 修改内容（如选择修改）
                modified_content = extracted_content
                if review_status == "modified":
                    modified_content = st.text_area(
                        "修改后的内容",
                        value=extracted_content,
                        key=f"modified_content_{idx}",
                    )
                
                # 复核意见
                review_opinion = st.text_area(
                    "复核意见",
                    placeholder="请输入复核意见...",
                    key=f"review_opinion_{idx}",
                )
                
                # 保存复核结果按钮
                if st.button(f"💾 保存复核结果", key=f"save_review_{idx}"):
                    try:
                        import sqlite3
                        
                        # 生成签名哈希（复核人+时间+内容）
                        review_user = st.session_state.get("review_user", "admin")
                        review_time = datetime.now().isoformat()
                        signature_content = f"{review_user}:{review_time}:{field_name}:{extracted_content}:{review_status}"
                        signature_hash = generate_sha256_hash(signature_content)
                        
                        # 保存到数据库
                        conn = sqlite3.connect(REVIEW_DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO review_record (
                                extract_id, review_user, review_status, original_content,
                                modified_content, review_opinion, review_time, signature_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            idx,
                            review_user,
                            review_status,
                            extracted_content,
                            modified_content if review_status == "modified" else None,
                            review_opinion,
                            review_time,
                            signature_hash,
                        ))
                        conn.commit()
                        conn.close()
                        
                        # 记录审计日志
                        write_audit_log(
                            operation_type="REVIEW_RECORD",
                            operator=review_user,
                            operation_detail={
                                "field_name": field_name,
                                "review_status": review_status,
                                "signature_hash": signature_hash,
                            },
                            status="success",
                        )
                        
                        st.success("✅ 复核结果已保存")
                        logger.info(f"复核结果已保存: {field_name}")
                    
                    except Exception as e:
                        st.error(f"❌ 保存失败: {str(e)}")
                        logger.error(f"保存复核结果失败: {str(e)}", exc_info=True)

# 显示待复核的生成内容
if has_pending_content:
    pending_content = st.session_state.pending_review_content
    
    st.subheader("📝 生成内容复核")
    
    st.markdown(f"**模板类型**: {pending_content.get('template_type', 'N/A')}")
    st.markdown(f"**生成时间**: {pending_content.get('generated_at', 'N/A')}")
    
    generated_text = pending_content.get("generated_content", "")
    
    # 可编辑的文本区域
    reviewed_text = st.text_area(
        "生成内容（可编辑）",
        value=generated_text,
        height=400,
    )
    
    # 复核状态
    content_review_status = st.selectbox(
        "内容复核状态",
        options=["pending", "approved", "rejected"],
        format_func=lambda x: {
            "pending": "⏳ 待复核",
            "approved": "✅ 批准使用",
            "rejected": "❌ 拒绝使用",
        }.get(x, x),
        key="content_review_status",
    )
    
    # 复核意见
    content_review_opinion = st.text_area(
        "复核意见",
        placeholder="请输入对生成内容的复核意见...",
        key="content_review_opinion",
    )
    
    # 复核人签名
    reviewer_name = st.text_input(
        "复核人姓名",
        value=st.session_state.get("review_user", "admin"),
        key="reviewer_name",
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存复核结果", use_container_width=True):
            try:
                # 生成签名哈希
                review_time = datetime.now().isoformat()
                signature_content = f"{reviewer_name}:{review_time}:{content_review_status}:{reviewed_text[:100]}"
                signature_hash = generate_sha256_hash(signature_content)
                
                # 保存到数据库
                import sqlite3
                conn = sqlite3.connect(REVIEW_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO review_record (
                        extract_id, review_user, review_status, original_content,
                        modified_content, review_opinion, review_time, signature_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    0,  # 生成内容用0标识
                    reviewer_name,
                    content_review_status,
                    generated_text,
                    reviewed_text if reviewed_text != generated_text else None,
                    content_review_opinion,
                    review_time,
                    signature_hash,
                ))
                conn.commit()
                conn.close()
                
                # 记录审计日志
                write_audit_log(
                    operation_type="CONTENT_REVIEW",
                    operator=reviewer_name,
                    operation_detail={
                        "review_status": content_review_status,
                        "signature_hash": signature_hash,
                    },
                    status="success",
                )
                
                # 保存复核人名称到session
                st.session_state["review_user"] = reviewer_name
                
                st.success("✅ 复核结果已保存")
                logger.info(f"内容复核结果已保存: {content_review_status}")
            
            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")
                logger.error(f"保存内容复核结果失败: {str(e)}", exc_info=True)
    
    with col2:
        if st.button("📥 导出复核后内容", use_container_width=True):
            export_data = {
                "reviewed_at": datetime.now().isoformat(),
                "reviewer": reviewer_name,
                "review_status": content_review_status,
                "review_opinion": content_review_opinion,
                "reviewed_content": reviewed_text,
            }
            
            st.download_button(
                label="下载JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"reviewed_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

st.divider()

# ==================== 第二部分：复核记录查询 ====================
st.markdown("### 📜 复核记录查询")

if st.button("🔍 查询复核记录", use_container_width=True):
    try:
        import sqlite3
        
        conn = sqlite3.connect(REVIEW_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM review_record 
            ORDER BY review_time DESC 
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            st.session_state.review_records = rows
            st.success(f"✅ 查询成功，共 {len(rows)} 条复核记录")
        else:
            st.info("📋 暂无复核记录")
    
    except Exception as e:
        st.error(f"❌ 查询失败: {str(e)}")
        logger.error(f"查询复核记录失败: {str(e)}", exc_info=True)

if "review_records" in st.session_state and st.session_state.review_records:
    records = st.session_state.review_records
    
    st.subheader(f"📋 复核记录列表（共 {len(records)} 条）")
    
    for record in records:
        review_id = record[0]
        review_user = record[2]
        review_status = record[3]
        review_time = record[7]
        signature_hash = record[8][:16] + "..."
        
        # 根据状态显示不同颜色
        if review_status == "passed" or review_status == "approved":
            status_emoji = "✅"
            status_color = "green"
        elif review_status == "rejected":
            status_emoji = "❌"
            status_color = "red"
        elif review_status == "modified":
            status_emoji = "✏️"
            status_color = "orange"
        else:
            status_emoji = "⏳"
            status_color = "gray"
        
        with st.expander(f"{status_emoji} [{review_time}] {review_user} | 状态: {review_status} | 签名: {signature_hash}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**记录ID**: {review_id}")
                st.markdown(f"**复核人**: {review_user}")
                st.markdown(f"**复核时间**: {review_time}")
                st.markdown(f"**复核状态**: <span style='color:{status_color};'>{review_status}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**签名哈希**: `{record[8]}`")
            
            st.markdown("**原始内容**:")
            st.text(record[4][:500] + "..." if len(record[4]) > 500 else record[4])
            
            if record[5]:  # modified_content
                st.markdown("**修改后内容**:")
                st.text(record[5][:500] + "..." if len(record[5]) > 500 else record[5])
            
            if record[6]:  # review_opinion
                st.markdown("**复核意见**:")
                st.info(record[6])

st.divider()

# ==================== 第三部分：复核统计 ====================
st.markdown("### 📊 复核统计")

if st.button("📈 生成复核统计", use_container_width=True):
    try:
        import sqlite3
        
        conn = sqlite3.connect(REVIEW_DB_PATH)
        cursor = conn.cursor()
        
        # 按状态统计
        cursor.execute("""
            SELECT review_status, COUNT(*) as count 
            FROM review_record 
            GROUP BY review_status
        """)
        status_stats = cursor.fetchall()
        
        # 按复核人统计
        cursor.execute("""
            SELECT review_user, COUNT(*) as count 
            FROM review_record 
            GROUP BY review_user
        """)
        user_stats = cursor.fetchall()
        
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**按状态统计**:")
            if status_stats:
                for status, count in status_stats:
                    st.markdown(f"- {status}: {count} 条")
            else:
                st.caption("暂无数据")
        
        with col2:
            st.markdown("**按复核人统计**:")
            if user_stats:
                for user, count in user_stats:
                    st.markdown(f"- {user}: {count} 条")
            else:
                st.caption("暂无数据")
    
    except Exception as e:
        st.error(f"❌ 统计生成失败: {str(e)}")
        logger.error(f"复核统计生成失败: {str(e)}", exc_info=True)

st.divider()

# ==================== 第四部分：复核记录导出 ====================
st.markdown("### 📤 复核记录导出")

if st.button("📥 导出所有复核记录", use_container_width=True):
    try:
        import sqlite3
        
        conn = sqlite3.connect(REVIEW_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM review_record ORDER BY review_time DESC")
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            columns = ["review_id", "extract_id", "review_user", "review_status", 
                      "original_content", "modified_content", "review_opinion", 
                      "review_time", "signature_hash", "created_at"]
            
            export_data = {
                "export_time": datetime.now().isoformat(),
                "total_count": len(rows),
                "records": [dict(zip(columns, row)) for row in rows],
            }
            
            st.download_button(
                label="📥 下载JSON格式",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"review_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
            
            st.success("✅ 复核记录导出成功")
        else:
            st.info("📋 暂无复核记录可导出")
    
    except Exception as e:
        st.error(f"❌ 导出失败: {str(e)}")
        logger.error(f"复核记录导出失败: {str(e)}", exc_info=True)
