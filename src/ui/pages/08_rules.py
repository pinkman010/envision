"""
规则配置中心页面（零代码可视化配置）
功能：零代码修改实质性议题规则、可视化配置披露标准、规则版本管理
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from src.core_config import settings, get_logger
from src.core_config.paths import RULE_TEMPLATES_DIR, EXPORT_RESULTS_DIR
from src.utils.config_utils import load_topic_rules, load_esg_standards, load_match_rules
from src.utils.audit_utils import write_audit_log

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("⚙️ 规则配置中心")
st.divider()

# 合规声明
st.warning(
    "⚠️ **规则修改声明**：\n\n"
    "1. 规则修改会直接影响信息抽取和合规提示结果；\n"
    "2. 修改规则前建议先备份当前配置；\n"
    "3. 所有规则修改操作将被记录在审计日志中。"
)

# ==================== 第一部分：实质性议题规则配置 ====================
st.markdown("### 📝 实质性议题规则配置")

# 加载当前规则
try:
    topic_rules = load_topic_rules()
except Exception as e:
    st.error(f"❌ 加载规则配置失败: {str(e)}")
    topic_rules = {"topics": [], "supported_industries": ["新能源"]}

# 显示现有议题
st.subheader("📋 现有议题列表")

topics = topic_rules.get("topics", [])
if topics:
    for idx, topic in enumerate(topics):
        with st.expander(f"{topic.get('name', '未命名议题')} (ID: {topic.get('id', 'N/A')})"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**议题ID**: {topic.get('id', 'N/A')}")
                st.markdown(f"**议题名称**: {topic.get('name', 'N/A')}")
                st.markdown(f"**优先级**: {topic.get('priority', 'N/A')}")
            with col2:
                st.markdown(f"**关键词**: {', '.join(topic.get('keywords', []))}")
                st.markdown(f"**正则模式**: `{', '.join(topic.get('regex_patterns', []))}`")
else:
    st.info("📋 暂无配置议题")

# 添加新议题
st.subheader("➕ 添加新议题")

with st.form("add_topic_form"):
    new_topic_id = st.text_input("议题ID", placeholder="例如: carbon_emission")
    new_topic_name = st.text_input("议题名称", placeholder="例如: 碳排放管理")
    new_topic_priority = st.number_input("优先级", min_value=1, max_value=100, value=50)
    new_topic_keywords = st.text_area("关键词（逗号分隔）", placeholder="例如: 碳排放,温室气体,CO2")
    new_topic_patterns = st.text_area("正则表达式模式（逗号分隔）", placeholder="例如: (\\d+[\\.\\d]*)\\s*吨CO2e")
    
    submit_topic = st.form_submit_button("✅ 添加议题", use_container_width=True)

if submit_topic:
    if not new_topic_id or not new_topic_name:
        st.error("❌ 议题ID和名称不能为空")
    else:
        try:
            # 构建新议题
            new_topic = {
                "id": new_topic_id,
                "name": new_topic_name,
                "priority": new_topic_priority,
                "keywords": [k.strip() for k in new_topic_keywords.split(",") if k.strip()],
                "regex_patterns": [p.strip() for p in new_topic_patterns.split(",") if p.strip()],
            }
            
            # 添加到规则
            topic_rules["topics"].append(new_topic)
            
            # 保存到文件
            rules_file = RULE_TEMPLATES_DIR / "topic_rules.json"
            rules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(rules_file, "w", encoding="utf-8") as f:
                json.dump(topic_rules, f, ensure_ascii=False, indent=2)
            
            # 记录审计日志
            write_audit_log(
                operation_type="RULE_CONFIG_UPDATE",
                operator="admin",
                operation_detail={
                    "action": "add_topic",
                    "topic_id": new_topic_id,
                    "topic_name": new_topic_name,
                },
                status="success",
            )
            
            st.success(f"✅ 议题 '{new_topic_name}' 添加成功")
            logger.info(f"添加新议题: {new_topic_id}")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ 添加议题失败: {str(e)}")
            logger.error(f"添加议题失败: {str(e)}", exc_info=True)

st.divider()

# ==================== 第二部分：ESG披露标准配置 ====================
st.markdown("### 📚 ESG披露标准配置")

# 加载当前标准配置
try:
    esg_standards = load_esg_standards()
except Exception as e:
    st.error(f"❌ 加载披露标准失败: {str(e)}")
    esg_standards = {"core_standards": []}

# 显示现有标准
st.subheader("📋 现有披露标准")

core_standards = esg_standards.get("core_standards", [])
if core_standards:
    for idx, standard in enumerate(core_standards):
        with st.expander(f"{standard.get('name', '未命名标准')} (ID: {standard.get('id', 'N/A')})"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**标准ID**: {standard.get('id', 'N/A')}")
                st.markdown(f"**标准名称**: {standard.get('name', 'N/A')}")
                st.markdown(f"**适用行业**: {', '.join(standard.get('applicable_industries', []))}")
            with col2:
                st.markdown(f"**披露要求**: {standard.get('requirement', 'N/A')}")
                st.markdown(f"**参考条款**: {standard.get('reference_clause', 'N/A')}")
else:
    st.info("📋 暂无配置披露标准")

# 添加新标准
st.subheader("➕ 添加新披露标准")

with st.form("add_standard_form"):
    new_standard_id = st.text_input("标准ID", placeholder="例如: ISSB_S2_GHG")
    new_standard_name = st.text_input("标准名称", placeholder="例如: ISSB S2 温室气体排放披露")
    new_standard_industries = st.text_input("适用行业（逗号分隔）", placeholder="例如: 新能源,制造业")
    new_standard_requirement = st.text_area("披露要求", placeholder="描述该标准的披露要求...")
    new_standard_reference = st.text_input("参考条款", placeholder="例如: IFRS S2 第23-28段")
    
    submit_standard = st.form_submit_button("✅ 添加标准", use_container_width=True)

if submit_standard:
    if not new_standard_id or not new_standard_name:
        st.error("❌ 标准ID和名称不能为空")
    else:
        try:
            # 构建新标准
            new_standard = {
                "id": new_standard_id,
                "name": new_standard_name,
                "applicable_industries": [i.strip() for i in new_standard_industries.split(",") if i.strip()],
                "requirement": new_standard_requirement,
                "reference_clause": new_standard_reference,
            }
            
            # 添加到标准
            esg_standards["core_standards"].append(new_standard)
            
            # 保存到文件
            standards_file = RULE_TEMPLATES_DIR / "esg_standards.json"
            standards_file.parent.mkdir(parents=True, exist_ok=True)
            with open(standards_file, "w", encoding="utf-8") as f:
                json.dump(esg_standards, f, ensure_ascii=False, indent=2)
            
            # 记录审计日志
            write_audit_log(
                operation_type="RULE_CONFIG_UPDATE",
                operator="admin",
                operation_detail={
                    "action": "add_standard",
                    "standard_id": new_standard_id,
                    "standard_name": new_standard_name,
                },
                status="success",
            )
            
            st.success(f"✅ 披露标准 '{new_standard_name}' 添加成功")
            logger.info(f"添加新标准: {new_standard_id}")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ 添加标准失败: {str(e)}")
            logger.error(f"添加标准失败: {str(e)}", exc_info=True)

st.divider()

# ==================== 第三部分：抽取字段配置 ====================
st.markdown("### 🔍 信息抽取字段配置")

st.info("📋 配置信息抽取Agent需要提取的固定字段清单")

# 显示当前字段
fixed_fields = topic_rules.get("fixed_extraction_fields", [
    "company_name", "report_year", "scope1_emission", "scope2_emission", "green_energy_usage"
])

st.markdown("**当前抽取字段**:")
for field in fixed_fields:
    st.markdown(f"- `{field}`")

# 添加新字段
st.subheader("➕ 添加新抽取字段")

new_field = st.text_input("字段名称", placeholder="例如: water_consumption")
if st.button("✅ 添加字段", use_container_width=True):
    if new_field and new_field not in fixed_fields:
        try:
            topic_rules["fixed_extraction_fields"].append(new_field)
            
            # 保存到文件
            rules_file = RULE_TEMPLATES_DIR / "topic_rules.json"
            with open(rules_file, "w", encoding="utf-8") as f:
                json.dump(topic_rules, f, ensure_ascii=False, indent=2)
            
            # 记录审计日志
            write_audit_log(
                operation_type="RULE_CONFIG_UPDATE",
                operator="admin",
                operation_detail={
                    "action": "add_extraction_field",
                    "field_name": new_field,
                },
                status="success",
            )
            
            st.success(f"✅ 抽取字段 '{new_field}' 添加成功")
            logger.info(f"添加新抽取字段: {new_field}")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ 添加字段失败: {str(e)}")
            logger.error(f"添加字段失败: {str(e)}", exc_info=True)
    elif new_field in fixed_fields:
        st.warning("⚠️ 该字段已存在")
    else:
        st.error("❌ 字段名称不能为空")

st.divider()

# ==================== 第四部分：规则备份与恢复 ====================
st.markdown("### 💾 规则备份与恢复")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 备份规则")
    if st.button("导出当前规则配置", use_container_width=True):
        try:
            backup_data = {
                "backup_time": datetime.now().isoformat(),
                "topic_rules": topic_rules,
                "esg_standards": esg_standards,
            }
            
            backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 下载备份文件",
                data=backup_json,
                file_name=f"esg_rules_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
            
            # 记录审计日志
            write_audit_log(
                operation_type="RULE_CONFIG_BACKUP",
                operator="admin",
                operation_detail={"action": "export_rules"},
                status="success",
            )
            
            st.success("✅ 规则备份成功")
        
        except Exception as e:
            st.error(f"❌ 备份失败: {str(e)}")
            logger.error(f"规则备份失败: {str(e)}", exc_info=True)

with col2:
    st.subheader("📥 恢复规则")
    uploaded_backup = st.file_uploader("选择备份文件", type=["json"])
    if uploaded_backup is not None:
        if st.button("恢复规则配置", use_container_width=True, type="primary"):
            try:
                backup_data = json.loads(uploaded_backup.getvalue().decode("utf-8"))
                
                # 恢复规则
                if "topic_rules" in backup_data:
                    rules_file = RULE_TEMPLATES_DIR / "topic_rules.json"
                    with open(rules_file, "w", encoding="utf-8") as f:
                        json.dump(backup_data["topic_rules"], f, ensure_ascii=False, indent=2)
                
                if "esg_standards" in backup_data:
                    standards_file = RULE_TEMPLATES_DIR / "esg_standards.json"
                    with open(standards_file, "w", encoding="utf-8") as f:
                        json.dump(backup_data["esg_standards"], f, ensure_ascii=False, indent=2)
                
                # 记录审计日志
                write_audit_log(
                    operation_type="RULE_CONFIG_RESTORE",
                    operator="admin",
                    operation_detail={
                        "action": "import_rules",
                        "backup_time": backup_data.get("backup_time", "unknown"),
                    },
                    status="success",
                )
                
                st.success("✅ 规则恢复成功")
                logger.info("规则配置已恢复")
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ 恢复失败: {str(e)}")
                logger.error(f"规则恢复失败: {str(e)}", exc_info=True)

st.divider()

# ==================== 第五部分：规则版本信息 ====================
st.markdown("### ℹ️ 规则版本信息")

st.markdown(f"**规则文件路径**: `{RULE_TEMPLATES_DIR}`")
st.markdown(f"**议题数量**: {len(topics)}")
st.markdown(f"**披露标准数量**: {len(core_standards)}")
st.markdown(f"**抽取字段数量**: {len(fixed_fields)}")
