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
- 嵌入模型：Ollama 本地部署（见 `OLLAMA_BASE_URL` + `EMBEDDING_MODEL`）
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
├── ui/             # Streamlit前端（8页）
└── utils/          # ChromaDB、LLM、审计、相似度等工具
data/
└── knowledge_base/
    ├── standards/      # 披露标准条文（已建：standards_kb.xlsx）
    ├── peer_reports/   # 同行ESG报告语料（对接第1组）
    └── topic_taxonomy/ # 议题分类标签体系（对接第2组）
templates/
└── rule_templates/ # Agent运行时规则配置（代码读取，不参与向量化）
    ├── topic_rules.json      # 议题定义：id/关键词/正则，必须与standards_kb.xlsx的topic_id对齐
    ├── esg_standards.json    # 标准元数据：ISSB/HKEX/SASB要求摘要，差距判断参考
    ├── match_rules.json      # 匹配策略：关键词/正则/语义权重和开关
    ├── esg_indicators.json   # 指标名称和单位定义，报告展示用
    └── unit_conversions.json # 单位换算表（万吨→吨、GWh→MWh等），数值归一化用
scripts/            # 运维脚本
```

## 关键文件路径
- Agent基类：`src/agent/base_agent.py`
- 总控Agent：`src/agent/orchestrator_agent.py`
- 配置入口：`src/config/settings.py`（从`.env`读取，无默认值）
- 向量库工具：`src/utils/chroma_utils.py`（含 `search_standards()`、`search_peer_reports()`）
- LLM工具：`src/utils/llm_utils.py`
- 主入口：`src/main.py`
- 知识库导入脚本：`scripts/import_standards.py`（已修复，已运行）
- 标准条款Excel：`data/knowledge_base/standards/standards_kb.xlsx`
- 议题规则配置：`templates/rule_templates/topic_rules.json`（topic_id必须与Excel对齐）
- 标准元数据配置：`templates/rule_templates/esg_standards.json`
- 匹配策略配置：`templates/rule_templates/match_rules.json`

---

# 知识库结构（对接三组）

**核心标准**：ISSB S1/S2、HKEX 2024新版ESG指引（A类环境为重点）

**重点议题**（新能源行业）：温室气体排放（含Scope3）、供应链可持续、废弃物管理（叶片回收）、气候风险治理、生物多样性

**字段规范**（standards_kb.xlsx各Sheet通用）：
- `clause_id`：条款编号，ChromaDB的metadata key（如 `A1-KPI1`、`S2-29`）
- `standard_name`：`HKEX_2024` 或 `ISSB_S2` 或 `ISSB_S1`
- `topic_id`：严格对应 `templates/rule_templates/topic_rules.json` 里的 `id` 字段
- `topic_taxonomy_id`：第2组议题分类ID，对齐前留空
- `requirement_text`：条款原文，向量化主体
- `industry_applicability`：极高/高/中/低
- `notes_gap`：新能源行业披露差距（AdvisorAgent差距建议的数据源）
- `notes_peer`：同行披露案例（AdvisorAgent同行对比的数据源）

---

# 编码规范

- 注释语言：中文
- 编码风格：Vibe coding（描述需求→生成→调整迭代）
- 所有配置从 `.env` 读取，不硬编码任何密钥或路径
- Agent状态统一用 `AgentState` 枚举管理
- 异常统一用 `BaseESGException`

---

# 约束（不要做的事）

- 不使用 Dify / Coze 等无代码平台
- 不做模型 Fine-tuning（数据量不足，周期太长）
- 不过度工程化，保持最小可用原则
- AI输出仅为辅助参考，所有披露建议需人工复核后使用
- 不动态路由，OrchestratorAgent只走预设固定流程

---

# 当前重点任务

1. ~~建立 `standards/` 知识库~~ **已完成**：`data/knowledge_base/standards/standards_kb.xlsx` 已创建
2. ~~运行 `scripts/import_standards.py`，将Excel导入ChromaDB `standards` 集合（脚本已修复，可直接运行）~~ **已完成**
3. ~~与第1组对齐 `peer_reports/` 数据格式~~ **无需协商**：让他们提供 txt+CSV 格式即可（见下方说明）
4. ~~与第2组对齐 `topic_taxonomy/` 议题分类标签~~ **无需协商**：等他们给出 ID 后填入 `topic_taxonomy_id` 列即可（见下方说明）
5. 4月中期前完成单报告分析Demo（输入ESG文本→识别议题→差距分析→优化建议）

---

# 三组对齐说明

## 与第二组（议题分类标签）

**第二组负责**：核心实质性议题的数据标注和预测，会产出一套议题分类标签 ID 体系。

**只需要做一件事**：等他们给出议题分类 ID 列表后，填入 `standards_kb.xlsx` 的 `topic_taxonomy_id` 列，重跑 `import_standards.py` 即可。

- `topic_id`（系统内部用，已在跑）**不需要改**
- `topic_taxonomy_id` 只是附加的元数据字段，没有 Agent 代码依赖它做检索，填入备查即可
- **无需协商，单向接收数据后填表重建索引**

---

## 与第一组（同行报告语料库）

**第一组负责**：构建新能源行业ESG语料库，`peer_reports/` 目录里已有部分 PDF（远景/金风/Vestas/Siemens Gamesa）。

**对接方式：不能让他们直接给外部 RAG API**，原因：`RetrievalAgent` 直接调用本地 `chroma_utils.search_peer_reports()`，没有调用外部 API 的逻辑，接入外部 API 需大改代码。

**正确对接方式**：
- 让第一组提供 **txt + metadata.csv** 格式（不要 PDF，不要 JSON）
  - 每份报告一个 `.txt` 文件（UTF-8 编码）
  - 一个 `metadata.csv`，字段：`file_name, company, year, industry, language`
- 放入 `data/knowledge_base/peer_reports/`
- 自己写 `scripts/import_peer_reports.py`（参考 `import_standards.py`），读 CSV 拿元数据，读 txt 分块，`topic` 由本地 `RuleMatcher` 自动打标，向量化导入本地 ChromaDB `peer_reports` 集合
- **无需与第一组协商任何其他格式**

---

## 待办

- [ ] 等第二组给出议题分类 ID → 填入 `standards_kb.xlsx` 的 `topic_taxonomy_id` 列 → 重跑 `import_standards.py`
- [ ] 编写 `scripts/import_peer_reports.py` 向量化导入 peer_reports
- [ ] 验证 `search_peer_reports()` 可正常检索

---

# 开发协作规范

## Claude + MiniMax 分工

**原则**：Claude 只出方案和做事后检查，不自己写文件；MiniMax 只执行写文件，不自行决策。

**详细工作流与调用命令**：见 `~/.claude/projects/.../memory/minimax_workflow.md`
