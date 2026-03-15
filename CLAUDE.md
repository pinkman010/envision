# 项目背景

上海财经大学MBA整合实践项目，合作企业：远景能源有限公司（Envision Energy）。

**课题**：AI驱动的新能源行业ESG披露与沟通智能分析框架研究

我是第三组成员，负责构建ESG信息披露与核心议题识别的AI专家模型。
其余两组分别为：①构建新能源行业ESG的语料库；②识别核心实质性议题-数据标注和预测

**关键时间节点**：3月建库 → 4月中期Demo → 7月结题交付完整报告

---

# 系统架构

## 技术栈
- 语言：Python 3.13.11
- LLM：通过 `LLM_BASE_URL` + `LLM_API_KEY` 配置（见 `.env`），当前支持多模型切换
- 向量数据库：ChromaDB（持久化路径见 `CHROMA_DB_PERSIST_DIR`）
- 嵌入模型：硅基流动 `BAAI/bge-m3`（见 `SILICONFLOW_API_KEY` + `EMBEDDING_MODEL`）
- 后端：FastAPI
- 前端：Streamlit
- 数据库：SQLite

## Agent架构（1+4）

```
OrchestratorAgent（总控调度，固定流程状态机）
├── CorpusAgent      # 语料解析与向量化
├── RetrievalAgent   # RAG检索 + LLM议题识别（检索standards/和peer_reports/集合）
├── AnalystAgent     # 差距分析（对照标准+同行对比，输出gap_analysis+peer_comparison）
└── AdvisorAgent     # 披露建议生成（消费notes_gap和notes_peer字段）
```

**固定工作流（3条，写死不动态路由）**：
1. `single_report_analysis`：单报告分析（语料→议题检索→差距分析→优化建议→人工复核）
2. `multi_company_benchmark`：多企业对标（预留，未实现）
3. `batch_corpus_processing`：批量处理（预留，未实现）

## 目录结构

```
src/
├── agent/          # 所有Agent实现
├── api/            # FastAPI路由
├── config/         # 配置、日志、路径
├── ui/             # Streamlit前端
└── utils/          # ChromaDB、LLM、规则匹配等工具
data/
└── knowledge_base/
    ├── standards/      # 披露标准条文（standards_kb.xlsx）
    └── peer_reports/   # 同行ESG报告语料（对接第一组）
templates/
└── rule_templates/ # Agent运行时规则配置
    ├── topic_rules.json      # 议题关键词和正则匹配规则
    ├── esg_standards.json    # 标准元数据参考
    ├── esg_indicators.json   # ESG指标定义
    └── unit_conversions.json # 单位换算表
scripts/            # 运维脚本（import_standards.py等）
```

## 关键文件路径
- Agent基类：`src/agent/base_agent.py`
- 总控Agent：`src/agent/orchestrator_agent.py`
- 配置入口：`src/config/settings.py`（从`.env`读取）
- 向量库工具：`src/utils/chroma_utils.py`（`search_standards()`、`search_peer_reports()`）
- 规则匹配：`src/utils/rule_match.py`（`RuleMatcher` 议题自动打标）
- 知识库导入：`scripts/import_standards.py`（已运行）
- 标准条款：`data/knowledge_base/standards/standards_kb.xlsx`
- 议题规则：`templates/rule_templates/topic_rules.json`

---

# 核心约束

- 所有配置从 `.env` 读取，不硬编码密钥或路径
- Agent状态统一用 `AgentState` 枚举管理
- 异常统一用 `BaseESGException`
- 不过度工程化，保持最小可用原则
- AI输出仅为辅助参考，所有建议需人工复核

---

# 核心任务（4月中期Demo前）

- 与第一/二组确认五项技术参数，完成 ChromaDB 对接
- 验证 `search_peer_reports()` 可正常检索
- 完成单报告分析流程演示（输入ESG文本 → 议题识别 → 差距分析 → 披露建议）

# 与第一/二组对接指南

**对接目标**：获取第一组 ChromaDB 的 `peer_reports` 集合数据，直接挂载到本地使用。

**对接前需确认五项技术参数**：
1. 向量库：必须是 ChromaDB
2. 嵌入模型：必须是 `BAAI/bge-m3`（不同模型的语义空间不兼容）
3. chunk_size：建议 500~1000 字符范围
4. metadata 字段名：必须包含 `company`、`year`、`industry`、`topic`（`RetrievalAgent` 代码依赖这些字段）
5. 集合名称：必须是 `peer_reports`（与 `chroma_utils.py` 中 `get_or_create_collection()` 的集合名对齐）

**最优对接方式**（五项全部兼容）**：
- 直接复制他们的 ChromaDB 数据目录到本地 `chroma_db/`
- 无需重新向量化，无需编写 `import_peer_reports.py`

**备选对接方式**（五项不完全兼容）**：
- 要求他们提供原始 txt 文件 + metadata.csv（字段：`company, year, industry, language`）
- 自己编写 `scripts/import_peer_reports.py`（参考 `import_standards.py`），通过 `RuleMatcher` 自动打标议题，向量化导入

**topic_taxonomy_id**：
- 第二组给出议题分类 ID 列表后，填入 `standards_kb.xlsx` 的 `topic_taxonomy_id` 列
- 这是备查字段，不影响 4 月中期 Demo，可延后处理

---

## 待办

- [ ] 与第一/二组确认五项技术参数
- [ ] 完成 ChromaDB 对接并验证 `search_peer_reports()`

---

