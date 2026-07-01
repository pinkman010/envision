# 远景能源 ESG 披露证据核验与沟通智能分析系统

上海财经大学整合实践项目
合作企业：远景能源有限公司（Envision Energy）
课题名称：AI 驱动的新能源行业 ESG 披露与沟通智能分析框架研究

## 1. 项目概览

本仓库实现一个面向单份 ESG 报告的 P0 MVP，用于对远景能源 2024 中文 ESG 报告进行 GRI 参照披露证据核验和披露支持充分性分析。系统以报告原文、GRI requirement、证据页码、AI 辅助判断、人工复核记录和审计留痕为核心，支持条款级查看、复核保存和导出。

项目的第一性原理：

- ESG 披露判断的最小可信单元是“具体 requirement + 报告正文证据 + 页码 + 判断理由”，不是 GRI 索引命中。
- AI 的价值在于加速检索、归纳、缺口识别和建议草拟，不能替代人工对边界样本、商业保密、省略理由和不适用说明的判断。
- P0 的目标是打通一个可追溯、可复核、可审计的单报告样例，避免过早扩展到多公司对标、舆情或复杂 Dashboard。
- 所有阶段产物必须能回答：输入是什么、标准版本是什么、模型和 prompt 是什么、证据来自哪里、人工有没有复核、最终状态是否仍待确认。

当前 P0 交付状态：

| 模块 | 当前状态 | 说明 |
|---|---|---|
| 固定报告 artifact-backed 条款复核 | 已完成闭环 | 基于 Stage E accepted artifacts，不重新触发全量 LLM |
| current disclosure assessment | 143 条 | 114 条 ordinary current disclosure + 29 条 GRI 3-3 index-row instances |
| Advisor coverage | 143 条 | 141 条建议 + 2 条 disclosed/no-action coverage |
| E4 SQLite/API/Streamlit 工作台 | 已完成 | 支持查看、筛选、保存人工复核、导出 CSV/JSON |
| 最终状态口径 | pending review | `review_status=pending`，`final_evaluation_status=pending_human_evaluation` |

重要限制：

- AI 输出只作为分析辅助，不能作为正式披露结论或对外披露建议。
- 页面和导出中的 Advisor 内容应理解为 `AI-assisted recommendation pending human review`。
- 当前 P0 不覆盖多公司对标、批量报告处理、舆情监测、登录、多用户权限、友商仪表盘和完整生产部署。

当前最重要的用户场景：

1. 项目成员打开固定报告的 143 条核验单元。
2. 查看每条 GRI disclosure 的 AI verdict、requirement checks、证据页码和 source text。
3. 对 AI 判断进行人工复核，写入 human verdict、错误类型、修正说明。
4. 导出 assessment、Advisor coverage 和 review decisions，形成后续汇报、论文实验或企业复核材料。

## 2. 背景、问题和设计取舍

### 2.1 背景

新能源企业 ESG 报告通常存在三类现实问题：

- 披露标准复杂：GRI disclosure 往往包含 a/b/c、i/ii/iii 等多层 requirement。
- 报告证据分散：同一 disclosure 可能在董事长致辞、专题章节、绩效表和 GRI 索引中同时出现。
- 人工核验成本高：人工逐项找证据、判充分性、写缺口建议耗时且容易遗漏。

本项目选择从远景能源 2024 中文 ESG 报告切入，优先验证“单报告条款级证据核验”是否能够稳定落地。

### 2.2 核心问题

早期实现容易出现的错误是：GRI 索引命中某个 disclosure 后，系统直接把该 disclosure 判断为充分披露。这个逻辑不成立，原因是：

- GRI 索引主要提供披露位置，不能替代正文披露内容。
- 索引页可能存在页码偏移、页码错误、串列抽取、指向不充分等问题。
- 某些索引说明是“从略披露”“不适用”或“因商业保密限制”，这些需要人工审查理由充分性。
- 对多子要求 disclosure，仅命中一个证据片段不能代表所有 requirement 已满足。

因此当前系统采用 requirement-level 核验，再汇总 disclosure-level verdict。

### 2.3 关键设计取舍

| 取舍 | 当前选择 | 理由 |
|---|---|---|
| 分析粒度 | requirement 级判断 + disclosure 级汇总 | 支撑可追溯、可复核和缺口解释 |
| GRI 索引用途 | 定位线索 | 索引不能单独支持 positive disclosure |
| 3-3 处理 | 按报告 GRI 索引逐行实例化 | `3-3_generic` 无法代表不同实质性议题 |
| 不适用判断 | 默认需要人工确认 | GRI 对不适用和省略披露要求解释理由 |
| Advisor 生成 | 晚于核验结论 | 避免先生成建议再反向寻找证据 |
| 产品闭环 | E4 pending-review 工作台 | 当前重点是固定报告结果查看、复核和导出 |

## 3. README 覆盖

本 README 按交付和协作视角组织，包括：

1. 项目目标和适用边界：说明系统解决什么问题、服务谁、当前做到哪一步。
2. 当前状态和关键结论：列出已完成、待完成、不能误用的能力。
3. 架构说明：解释 UI、API、Agent、数据层和外部模型服务如何协作。
4. 数据与来源：明确原始报告、标准资料、运行产物和审计文件的位置。
5. 安装与启动：给出可复制的环境准备、`.env` 配置、后端和前端启动命令。
6. 使用流程：说明用户如何加载数据、查看条款、保存复核、导出结果。
7. API 和脚本入口：列出主要接口、批处理脚本、验证脚本。
8. 验证方法：提供最小可重复测试命令和当前通过的 smoke 结果。
9. 风险和限制：避免把规划中能力、静态演示、未人工确认内容写成已实现。
10. 文档索引和开发约束：指向用户手册、模型说明、开发日志和阶段计划。

## 4. P0 范围

### 4.1 已实现范围

P0 聚焦“单报告 + GRI current disclosure + 条款级证据核验”的验证样例。

已实现能力：

- 固定报告：`data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf`
- 固定标准 profile：`gri_p0_2024_current_disclosure_v1`
- 条款级 assessment 展示：143 条 current disclosure units
- Advisor coverage 展示：143 条 coverage items
- evidence 查看：支持 `source_page`、`report_page_label`、`source_text`、`evidence_kind`、requirement checks
- 人工复核保存：写入 SQLite `p0_review_decisions`
- 导出：assessment、Advisor、review decisions 的 CSV/JSON
- 审计留痕：Stage E/E3.5/E4/F 运行产物均保留在 `data/runs/`

### 4.2 143 条 current assessment unit 的口径

当前 README、页面和交付口径统一使用 143 条 current disclosure assessment units。

来源：

| 类型 | 数量 | 说明 |
|---|---:|---|
| ordinary current disclosure | 114 | 不含 `3-3_generic` 的普通 current disclosure 单元 |
| GRI 3-3 index-row instances | 29 | 按远景报告 GRI 索引逐行展开的 3-3 管理方针实例 |
| 合计 | 143 | E4 工作台和 final Advisor coverage 的统一范围 |

相关澄清：

- `118` 是早期 manifest 中的全部技术记录口径，包含未来标准记录，不能写作当前全量分析范围。
- `115` 是 current disclosure 规范化记录口径，其中包含尚未展开的 `3-3_generic`。
- 最终 E4 展示和复核使用 `114 + 29 = 143` 的 accepted assessment set。
- 2026 readiness 和 2027 watchlist 不进入 2024 current disclosure 统计。

### 4.3 五分类 verdict

系统保留五类 disclosure-level verdict：

| verdict | 含义 | 典型条件 |
|---|---|---|
| `disclosed` | 已披露 | 所有适用 mandatory requirements 均有充分正文证据 |
| `partially_disclosed` | 部分披露 | 至少部分 mandatory requirements 有正文证据，仍存在缺口 |
| `not_disclosed` | 未披露 | 合理检索后未发现有效正文证据，且无省略/不适用理由需要审查 |
| `not_applicable` | 不适用 | 有明确且充分的不适用理由，通常仍需人工确认 |
| `manual_review` | 待人工复核 | 适用性、省略理由、证据冲突、页码异常或文本质量导致不能可靠自动判断 |

汇总规则：

- `disclosed` / `partially_disclosed` 不得只由 `index_evidence` 支撑。
- `partially_disclosed` 必须有 `missing_requirements` 或 `partial_requirements`。
- `manual_review` 必须有 `manual_review_reason_codes`。
- 无正文证据、无省略说明、无适用性争议且检索覆盖合理时，判 `not_disclosed`，避免过度 `manual_review`。

### 4.4 暂不属于 P0 的范围

以下能力保留为 P1/P2 或后续阶段：

- 多公司 ESG 对标分析
- 批量 ESG 报告处理
- 友商 Dashboard 或资本市场对标
- Claw 舆情监测、第三方数据库接入、供应链风险监测
- 登录、多用户权限、任务队列、生产级部署
- 重新上传任意报告后自动生成 143 条完整结果的产品化链路

## 5. 技术架构

### 5.1 总体架构

```text
--------------------+      +--------------------+      +-------------------------+
| Streamlit UI       | ---> | FastAPI API         | ---> | Agent / Service Layer   |
| 首页 / 上传 / 复核 |      | /api/v1/*           |      | Corpus/Retrieval/...    |
+--------------------+      +--------------------+      +-------------------------+
                                                                  |
                                                                  v
                         +---------------------+      +--------------------------+
                         | SQLite / ChromaDB   |      | LLM / Embedding Service  |
                         | 复核 / 向量 / 审计  |      | DeepSeek / SiliconFlow   |
                         +---------------------+      +--------------------------+
```

### 5.2 Agent 链路

当前主流程为 `single_report_analysis`：

```text
CorpusAgent -> RetrievalAgent -> AnalystAgent -> AdvisorAgent
```

职责说明：

| 组件 | 职责 |
|---|---|
| `CorpusAgent` | 文件解析、文本清洗、分块、入库 |
| `RetrievalAgent` | 议题识别、RAG 检索、标准与报告证据定位 |
| `AnalystAgent` | requirement 级核验、五分类判断、缺口归因 |
| `AdvisorAgent` | 基于核验结论生成披露优化建议 |
| `P0 review store/service` | 将 accepted artifacts 写入 SQLite，支持 E4 工作台查看和导出 |

### 5.3 1+4 Agents 分析链路

项目采用 `1 + 4` Agents 架构：

```text
OrchestratorAgent
├── CorpusAgent
├── RetrievalAgent
├── AnalystAgent
└── AdvisorAgent
```

其中 `OrchestratorAgent` 是总控调度层，4 个执行 Agent 负责单报告分析链路中的不同阶段。

#### 5.3.1 OrchestratorAgent

职责：

- 接收 `workflow_type=single_report_analysis`。
- 校验输入文件路径和工作流类型。
- 按固定顺序调用 4 个执行 Agent。
- 聚合各阶段输出。
- 对未实现的工作流返回明确错误。

典型输入：

```json
{
  "workflow_type": "single_report_analysis",
  "file_path": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf"
}
```

典型输出：

```json
{
  "corpus_result": {},
  "retrieval_result": {},
  "analyst_result": {},
  "advisor_result": {},
  "workflow_status": "completed"
}
```

边界：

- Orchestrator 不直接做 ESG 判断。
- Orchestrator 不直接生成建议。
- Orchestrator 负责流程编排、状态聚合和异常上抛。

#### 5.3.2 CorpusAgent

职责：

- 读取 PDF、Word、Excel 等报告文件。
- 提取原始文本。
- 必要时进行文本清洗和修复。
- 按 chunk 参数分块。
- 写入 ChromaDB 或本地语料记录。
- 生成 `corpus_id`、文件 metadata 和分块结果。

核心输入：

```json
{
  "file_path": "..."
}
```

核心输出：

```json
{
  "metadata": {
    "file_name": "...",
    "file_suffix": ".pdf",
    "file_size": 12345,
    "text_length": 67890,
    "chunk_count": 120,
    "corpus_id": "..."
  },
  "raw_text": "...",
  "fixed_text": "...",
  "chunks": [],
  "corpus_id": "..."
}
```

P0 追问口径：

- CorpusAgent 解决“报告内容如何进入系统”的问题。
- 对 PDF 表格、页码和索引抽取存在天然误差，因此后续 E2.1/E3 引入了 evidence contract、页码校验和人工 smoke review。

#### 5.3.3 RetrievalAgent

职责：

- 基于报告分块、GRI 索引、标准条款和规则进行检索。
- 识别 ESG 议题和相关 disclosure。
- 找到候选证据页和候选文本片段。
- 将 `index_evidence` 与 `substantive_report_evidence` 区分开。

核心输入：

```json
{
  "corpus_result": {},
  "topic_rules": {},
  "standards_context": {}
}
```

核心输出：

```json
{
  "identified_topics": [],
  "retrieved_standards": [],
  "retrieved_report_evidence": [],
  "candidate_pages": []
}
```

P0 追问口径：

- RetrievalAgent 不能把 GRI 索引命中直接转成“已披露”。
- 索引只作为定位线索，必须继续补取正文证据。
- E2.1-D 之后的规则要求全文/正文补证，避免过度依赖索引。

#### 5.3.4 AnalystAgent

职责：

- 对每个 disclosure 或 3-3 instance 做 requirement-level 核验。
- 判断每个 requirement 的支持程度。
- 形成 disclosure-level 五分类 verdict。
- 输出 evidence、missing requirements、partial requirements 和 manual review reason。

核心输入：

```json
{
  "retrieval_result": {},
  "requirement_checklist": [],
  "standard_profile_id": "gri_p0_2024_current_disclosure_v1"
}
```

核心输出：

```json
{
  "manifest_item_id": "current_gap:GRI302:302-4",
  "verdict": "partially_disclosed",
  "requirement_checks": [],
  "evidence": [],
  "missing_requirements": [],
  "partial_requirements": [],
  "manual_review_reason_codes": []
}
```

P0 追问口径：

- AnalystAgent 是当前项目质量控制的核心。
- E2.1 的主要目标就是让 AnalystAgent 先逐项 requirement 核验，再形成 disclosure-level 结论。
- `manual_review` 是风险控制机制，不能简单算作错误。

#### 5.3.5 AdvisorAgent

职责：

- 基于 AnalystAgent 的核验结论生成披露优化建议。
- 区分报告内容优化建议和需要内部数据确认的条件性建议。
- 对 `disclosed` 且无需行动的条目保留 no-action coverage。
- 避免基于公开报告推断企业内部不存在某项管理活动。

核心输入：

```json
{
  "assessment": {},
  "requirement_gaps": [],
  "evidence_summary": []
}
```

核心输出：

```json
{
  "manifest_item_id": "current_gap:GRI302:302-4",
  "recommendation_type": "report_content_improvement",
  "recommendation": "...",
  "requires_internal_data": true,
  "linked_requirement_ids": []
}
```

P0 追问口径：

- AdvisorAgent 只能在核验结论之后运行。
- 当前 E4 页面展示的是 `AI-assisted recommendation pending human review`。
- final Advisor 已基于 143 条 accepted assessment set 重新生成，但仍需人工复核后才能作为正式建议。

#### 5.3.6 1+4 链路与 E4 工作台的关系

完整分析链路和当前产品工作台的关系如下：

```text
single_report_analysis
  OrchestratorAgent
    -> CorpusAgent
    -> RetrievalAgent
    -> AnalystAgent
    -> AdvisorAgent
       |
       v
Stage E accepted artifacts
  final_current_effective_assessment_set.json
  analysis_run.json
  final_advisor_result_corrected.json
       |
       v
scripts/seed_stage_e4_pending_review.py
       |
       v
SQLite p0_review_* tables
       |
       v
FastAPI /api/v1/p0-review
       |
       v
Streamlit 条款复核页面
```

需要特别说明：

- 1+4 Agents 是分析生成链路。
- E4 pending-review 工作台是产品展示、复核和导出链路。
- 当前 E4 工作台使用已接受的 Stage E artifacts，不会在用户打开页面时重新调用 4 个分析 Agent。
- 后续要做“任意报告上传后自动生成完整 143 条核验”，需要把 1+4 Agents 的真实运行结果稳定接回 E4 工作台，这是 P0 之后的工程化方向。

### 5.4 E4 pending-review 产品链路

E4 工作台不重新触发 143 条 LLM 分析，使用 Stage E accepted artifacts：

```text
Stage E final accepted artifacts
    -> scripts/seed_stage_e4_pending_review.py
    -> SQLite p0_review_* tables
    -> FastAPI /api/v1/p0-review
    -> Streamlit 条款复核页面
```

该链路的状态口径固定为：

```text
review_status = pending
final_evaluation_status = pending_human_evaluation
recommendation_status = ai_assisted_pending_human_review
```

### 5.5 数据对象关系

```text
AnalysisRun
  ├── DisclosureAssessment[143]
  │     ├── RequirementCheck[]
  │     ├── Evidence[]
  │     ├── missing_requirements[]
  │     ├── partial_requirements[]
  │     └── manual_review_reason_codes[]
  ├── AdvisorCoverage[143]
  └── ReviewDecision[]
```

核心对象：

| 对象 | 作用 |
|---|---|
| `AnalysisRun` | 一次分析运行的元数据、标准 profile、输入哈希、状态和 assessment 集合 |
| `DisclosureAssessment` | 单个 disclosure 或 3-3 instance 的 AI 核验结论 |
| `RequirementCheck` | requirement 级支持判断、缺口和理由 |
| `Evidence` | 证据类型、页码、source text、chunk 或 evidence id |
| `AdvisorCoverage` | 针对 assessment 的建议或 no-action coverage |
| `ReviewDecision` | 人工复核结果，保存到 SQLite，不覆盖 AI 原始结果 |

## 6. 方法论与证据契约

### 6.1 Requirement 结构化

P0 使用 `p0_gri_requirement_checklist.json` 作为 requirement 级核验基础。每个核验对象至少包含：

```json
{
  "requirement_id": "302-4:a",
  "parent_requirement_id": "302-4",
  "requirement_text": "...",
  "requirement_type": "requirement",
  "conditional": false,
  "condition_text": null,
  "official_pdf_page": 123,
  "is_mandatory": true,
  "extraction_review_status": "reviewed"
}
```

硬性评分依据：

- Requirements
- 适用的 Compilation requirements

不进入硬性评分：

- Guidance
- Recommendations
- 示例
- 背景说明
- parent/intro compilation node，除非该节点本身包含实质性披露要求

### 6.2 Evidence 类型

系统至少区分四类证据：

| evidence kind | 用途 |
|---|---|
| `index_evidence` | 说明企业在 GRI 索引中引用了该 disclosure，只能作为定位线索 |
| `substantive_report_evidence` | 报告正文、专题章节、绩效表等可支撑 requirement 的证据 |
| `omission_or_not_applicable_evidence` | 企业明确说明从略披露、不适用或商业保密限制 |
| `external_reference_evidence` | 报告索引指向的外部网站、年报或鉴证报告等 |

证据字段要求：

```json
{
  "evidence_id": "evidence_001",
  "evidence_kind": "substantive_report_evidence",
  "source_page": 63,
  "report_page_label": "62",
  "source_text": "...",
  "chunk_id": "envision_2024_pdf_p63_chunk_01",
  "supports_requirement_ids": ["302-4:a"]
}
```

页码口径：

- `source_page` 指 PDF 物理页码。
- `report_page_label` 指报告印刷页码或页面标签。
- 当前远景报告常见偏移为 `source_page = report_page_label + 1`，但不能无条件套用，仍需逐项核验。

### 6.3 Advisor 生成规则

Advisor 必须晚于 requirement 核验结论生成。每条建议需要回答：

- 对应哪个 GRI requirement 或 disclosure。
- 报告已经披露了什么。
- 还缺少什么。
- 下一期报告可以补充什么。
- 是否需要企业内部数据才能完成。

建议类型：

| 类型 | 说明 |
|---|---|
| 报告内容优化建议 | 公开报告证据可直接支持的披露改进 |
| 内部管理改进建议 | 需要企业内部数据或管理事实确认，只能作为条件性建议 |
| no-action coverage | 对 `disclosed` 且无需建议的条目保留 coverage，保证 143 条范围完整 |

禁止表述：

- 根据公开报告直接推断企业内部不存在制度、流程或管理活动。
- 把 AI 生成建议写成已由企业确认的正式披露建议。
- 把 pending-review 数据写成人工验证通过。

## 7. 目录结构

```text
src/
├── agent/                 # Corpus/Retrieval/Analyst/Advisor/Orchestrator
├── api/                   # FastAPI 路由
├── config/                # 配置、路径、日志
├── models/                # AnalysisRun、Evidence、DisclosureAssessment 等契约
├── services/              # P0 导出等服务
├── storage/               # E4 pending-review SQLite 持久化
├── ui/                    # Streamlit 应用和页面
└── utils/                 # LLM、Chroma、PDF、哈希、校验工具

scripts/
├── run_api.py                                      # 后端启动入口
├── seed_stage_e4_pending_review.py                 # E4 pending-review 数据写入
├── import_f_human_review_results.py                # F 人工复核行导入
├── validate_stage_e2_1_evidence_contract.py        # E2.1 证据契约校验
├── validate_stage_e3_batch_outputs.py              # E3 批次输出校验
└── archive_stage_e/                                # Stage E/E3/E3.5 历史构建与真实运行脚本归档

data/
├── knowledge_base/
│   ├── peer_reports/       # 远景能源 2024 报告等原始材料
│   └── standards/          # GRI 原始标准、manifest、requirement checklist
├── chroma_db/              # ChromaDB 持久化目录
├── sqlite_db/              # SQLite 数据库
└── runs/                   # 各阶段运行产物与审计留痕

docs/
├── 用户操作手册.md
├── 项目模型说明文档.md
├── DEV_LOG.md
├── P0-P1-P2需求对齐表.md
├── stage_e*/
└── stage_f/

tests/
└── test_stage_*.py         # E2.1/E3/E3.5/E4 相关回归测试
```

## 8. 关键数据与运行产物

### 8.1 原始输入

| 类型 | 路径 | 说明 |
|---|---|---|
| 2024 报告 | `data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf` | P0 固定分析报告 |
| GRI 合订本 | `data/knowledge_base/standards/gri_reference/GRI_Standards_Official_Consolidated_Set_en.pdf` | 原始标准参考 |
| requirement checklist | `data/knowledge_base/standards/p0_gri_requirement_checklist.json` | requirement 级核验对象 |
| standard manifest | `data/knowledge_base/standards/p0_gri_manifest.json` | 标准版本和范围管理 |

### 8.2 P0 accepted artifacts

| 产物 | 路径 |
|---|---|
| 143 条 final assessments | `data/runs/stage_e_final_assessment_set/20260630T113930Z_e3_final_current_effective_set_accepted/final_current_effective_assessment_set.json` |
| 143 条 AnalysisRun | `data/runs/stage_e_final_assessment_set/20260630T113930Z_e3_final_current_effective_set_accepted/analysis_run.json` |
| 143 条 Advisor coverage | `data/runs/stage_e_final_advisor/20260630T114005Z_e3_143_unified_final_advisor/final_advisor_result_corrected.json` |
| traceability cleanup maps | `data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup/` |

### 8.3 E4 SQLite 数据

默认 SQLite 数据库位置由 `.env` 中 `SQLITE_DB_NAME` 和路径配置决定。E4 pending-review 写入以下核心表：

| 表 | 说明 |
|---|---|
| `p0_review_runs` | run 元数据、范围、状态、source manifest |
| `p0_assessments` | 143 条 AI assessment |
| `p0_advisor_items` | 143 条 Advisor coverage |
| `p0_review_decisions` | 人工复核记录 |

数据写入规则：

- seed 脚本可重复执行，采用 upsert 逻辑。
- 人工复核记录可以追加或更新。
- AI 原始 assessment 与 Advisor coverage 不被人工复核覆盖。

### 8.4 交付 smoke 结果

| 检查 | 路径 | 状态 |
|---|---|---|
| P0 project closure final smoke | `data/runs/stage_e4/20260701T032000Z_p0_project_closure_final_smoke/p0_project_closure_result.json` | passed |
| P0 delivery live API smoke | `data/runs/stage_e4/20260701T034420Z_p0_delivery_live_api_smoke/live_api_smoke_result.json` | passed |

### 8.5 阶段产物阅读顺序

追溯项目进展时建议按以下顺序阅读：

1. `docs/DEV_LOG.md`
2. `docs/stage_e3/e3_current_scope_acceptance_result.json`
3. `docs/stage_e3_5/e3_5_gri_3_3_execution_notes.md`
4. `docs/stage_e3_cleanup/e3_traceability_cleanup_acceptance_gate.json`
5. `data/runs/stage_e_final_assessment_set/.../final_current_effective_assessment_set.json`
6. `data/runs/stage_e4/.../p0_project_closure_result.json`
7. `data/runs/stage_e4/.../live_api_smoke_result.json`

## 9. 环境准备

### 9.1 Python 环境

项目依赖的唯一声明来源是 `pyproject.toml`。当前仓库没有维护第二份手工依赖清单。

推荐使用项目 conda 环境：

```powershell
conda activate envision
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

项目验证应使用项目专用 Python 或 Conda 环境。激活环境后，后续命令统一使用 `python`。

### 9.2 项目内 runtime bridge

如 Conda 环境目录无写权限，项目支持从 `vendor/python_runtime/` 加载 API 启动所需依赖。该目录已加入 `.gitignore`，不进入版本库。

缺失时可重建：

```powershell
python -m pip install --target vendor/python_runtime "anyio>=4.0.0" "uvicorn[standard]>=0.24.0"
```

说明：

- 这是项目内运行补丁，用于保证 API 启动。
- 不代表全局 conda 环境已被修复。
- `src/main.py` 和 `scripts/run_api.py` 会优先加载该目录。

### 9.3 环境变量

复制示例配置：

```powershell
Copy-Item .env.example .env
```

至少确认以下变量：

```text
PROJECT_NAME
PROJECT_DESCRIPTION
VERSION
API_PREFIX
ENVIRONMENT
HOST
PORT
API_BASE_URL
ALLOWED_ORIGINS
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
LLM_MAX_TOKENS
SILICONFLOW_API_KEY
EMBEDDING_MODEL
SQLITE_DB_NAME
CHROMA_DB_PERSIST_DIR
```

注意：

- `.env` 不得提交。
- 外部 LLM 调用需要单独授权。
- P0 E4 工作台查看 accepted artifacts 时不需要重新运行 143 条 LLM。

### 9.4 依赖和版本注意事项

当前 `pyproject.toml` 声明 `requires-python >=3.10`。项目已在 Python 3.13 环境下完成验证，文档和工具配置仍兼容 Python 3.10/3.11。

注意：

- `environment.yml` 当前不作为依赖事实来源。
- 不要为了修复全局 `pip check` 中的非项目依赖冲突而改动本项目依赖。
- `PyPDF2` 和 `pypdf` 在解析器统一前均保留，分别服务于不同脚本和解析链路。

## 10. 快速启动

### 10.1 写入 E4 pending-review 数据

首次使用 P0 条款复核工作台前，先把 accepted artifacts 写入 SQLite：

```powershell
python scripts/seed_stage_e4_pending_review.py
```

脚本默认读取 143 条 accepted assessments 和 143 条 Advisor coverage。

### 10.2 启动后端

```powershell
python scripts/run_api.py
```

默认地址：

```text
http://127.0.0.1:8000
```

常用入口：

```text
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/api/docs
GET http://127.0.0.1:8000/api/redoc
```

### 10.3 启动前端

```powershell
streamlit run src/ui/app.py
```

默认地址：

```text
http://127.0.0.1:8501
```

当前 Streamlit 导航包含：

- 首页概览
- 报告上传
- 条款复核
- 审计日志

### 10.4 API 快速检查

PowerShell 示例：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/p0-review/runs
Invoke-RestMethod http://127.0.0.1:8000/api/v1/p0-review/runs/20260630T113930Z_e3_final_current_effective_set_accepted/summary
```

预期摘要包含：

```json
{
  "assessment_count": 143,
  "advisor_coverage_count": 143,
  "review_status": "pending",
  "final_evaluation_status": "pending_human_evaluation"
}
```

## 11. P0 条款复核工作台使用流程

1. 启动后端：`python scripts/run_api.py`
2. 启动前端：`streamlit run src/ui/app.py`
3. 打开“条款复核”页面。
4. 选择 run：`20260630T113930Z_e3_final_current_effective_set_accepted`。
5. 查看页面摘要，确认：
   - assessments = 143
   - Advisor coverage = 143
   - `final_evaluation_status=pending_human_evaluation`
6. 按 AI verdict、GRI standard、disclosure、review status 或关键词筛选。
7. 打开条款详情，检查 requirement checks、evidence、页码、source text 和 Advisor coverage。
8. 填写人工复核字段并保存。
9. 导出 assessment、Advisor 或 review decisions 的 CSV/JSON。

保存规则：

- 人工复核只写入 `p0_review_decisions`。
- AI 原始 assessment 和 Advisor 原始建议不被覆盖。
- 导出文件保留 AI 原始字段和人工复核字段。

## 12. API 概览

统一前缀：

```text
/api/v1
```

核心接口：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/health` | 后端健康检查 |
| `POST` | `/api/v1/corpus/process` | 上传并解析报告 |
| `GET` | `/api/v1/corpus/list` | 查询历史语料 |
| `POST` | `/api/v1/retrieval/run` | 执行议题识别与检索 |
| `POST` | `/api/v1/analyst/analyze` | 执行差距分析 |
| `POST` | `/api/v1/advisor/recommend` | 生成优化建议 |
| `GET` | `/api/v1/p0-review/runs` | 查询 E4 review runs |
| `GET` | `/api/v1/p0-review/runs/{run_id}/summary` | 查询 run 摘要 |
| `GET` | `/api/v1/p0-review/runs/{run_id}/assessments` | 查询 assessment 列表 |
| `GET` | `/api/v1/p0-review/runs/{run_id}/assessments/{assessment_id}` | 查询单条 assessment 详情 |
| `GET` | `/api/v1/p0-review/runs/{run_id}/advisor-items` | 查询 Advisor coverage |
| `POST` | `/api/v1/p0-review/runs/{run_id}/review-decisions` | 保存人工复核记录 |
| `GET` | `/api/v1/p0-review/runs/{run_id}/exports/assessments.csv` | 导出 assessment CSV |
| `GET` | `/api/v1/p0-review/runs/{run_id}/exports/advisor-items.csv` | 导出 Advisor CSV |
| `GET` | `/api/v1/p0-review/runs/{run_id}/exports/review-decisions.csv` | 导出复核记录 CSV |
| `GET` | `/api/v1/p0-review/runs/{run_id}/exports/assessments.json` | 导出 assessment JSON |
| `GET` | `/api/v1/p0-review/runs/{run_id}/exports/advisor-items.json` | 导出 Advisor JSON |
| `GET` | `/api/v1/p0-review/runs/{run_id}/exports/review-decisions.json` | 导出复核记录 JSON |

### 12.1 保存人工复核记录示例

```powershell
$body = @{
  manifest_item_id = "current_gap:GRI302:302-4"
  assessment_id = "current_gap:GRI302:302-4"
  reviewer = "reviewer_name"
  human_verdict = "partially_disclosed"
  evidence_page_check = "ok"
  requirement_gap_check = "ok"
  error_type = ""
  correction_note = ""
  review_comment = "人工复核备注"
  source = "streamlit_or_api"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/p0-review/runs/20260630T113930Z_e3_final_current_effective_set_accepted/review-decisions" `
  -ContentType "application/json" `
  -Body $body
```

## 13. 验证命令

### 13.1 最小导入验证

```powershell
python -m py_compile src\main.py scripts\run_api.py sitecustomize.py
python -c "from src.main import app; print(app.title)"
```

预期输出包含：

```text
ESG AI System
```

### 13.2 E4/API/Streamlit 回归

```powershell
$env:PYTHONPATH='vendor/python_runtime'
python -m pytest `
  tests\test_stage_e4_p0_review_store.py `
  tests\test_stage_e4_seed_pending_review.py `
  tests\test_stage_e4_p0_review_api.py `
  tests\test_stage_e4_p0_review_export.py `
  tests\test_stage_e4_import_f_review_results.py `
  tests\test_stage_e4_streamlit_workbench_static.py `
  -q -p no:cacheprovider --basetemp tmp\pytest-p0-delivery-runtime
```

当前通过记录：

```text
20 passed
```

### 13.3 运行产物断言

```powershell
python -c "import json; from pathlib import Path; d=json.loads(Path('data/runs/stage_e4/20260701T034420Z_p0_delivery_live_api_smoke/live_api_smoke_result.json').read_text(encoding='utf-8')); c=d['checks']; assert d['status']=='p0_delivery_live_api_smoke_passed'; assert c['health']['status']==200; assert c['p0_review_summary']['assessment_count']==143; assert c['p0_review_summary']['advisor_coverage_count']==143; assert c['p0_review_summary']['final_evaluation_status']=='pending_human_evaluation'; print('live_api_smoke_ok')"
```

### 13.4 Git 空白检查

```powershell
git diff --check
```

当前可能出现 CRLF/LF 提示；只要没有 whitespace error，即不影响功能验证。

## 14. 验收口径

### 14.1 P0 产品闭环验收

P0 fixed-report artifact-backed 产品闭环可视为通过的条件：

| 检查项 | 期望 |
|---|---|
| E4 seed | SQLite 中 run、assessment、advisor item 写入成功 |
| assessment count | 143 |
| Advisor coverage count | 143 |
| 状态口径 | `pending_human_evaluation` |
| 条款详情 | 可查看 requirement checks、evidence、页码、source text |
| 人工复核 | 可保存 review decision |
| 导出 | assessment、Advisor、review decisions CSV/JSON 可导出 |
| 禁止表述 | 页面和文档不宣称最终人工验证通过 |

### 14.2 当前已通过的验收记录

| 验收 | 结果 |
|---|---|
| P0 project closure final smoke | `p0_project_closure_final_smoke_passed` |
| P0 delivery live API smoke | `p0_delivery_live_api_smoke_passed` |
| E4 回归测试 | `20 passed` |
| `git diff --check` | 无 whitespace error |

### 14.3 不应作为当前验收条件的事项

- F 阶段人工评测指标。
- 论文最终实验结论。
- 重新上传任意 ESG 报告后的自动全流程 143 条核验。
- 多公司对标或供应链风险分析。

## 15. 常用脚本

| 脚本 | 作用 |
|---|---|
| `scripts/run_api.py` | 启动 FastAPI，自动加载本地 runtime bridge |
| `scripts/seed_stage_e4_pending_review.py` | 将 Stage E accepted artifacts 写入 SQLite |
| `scripts/import_f_human_review_results.py` | 导入人工复核行到 E4 review decisions |
| `scripts/check_llm_config.py` | 检查 LLM 配置 |
| `scripts/validate_p0_requirement_checklist.py` | 校验 requirement checklist |
| `scripts/validate_stage_e2_1_evidence_contract.py` | 校验证据契约 |
| `scripts/validate_stage_e3_batch_outputs.py` | 校验 E3 batch 输出 |
| `scripts/archive_stage_e/` | 归档 Stage E/E3/E3.5 构建、真实运行和字段修正脚本，用于复现审计，不作为日常运行入口 |

外部 LLM 相关脚本在正式调用前需要确认授权、输入范围、模型配置和成本风险。

## 16. 数据与审计原则

项目对数据和证据有以下硬约束：

- 原始 PDF 和 GRI 标准文件不得覆盖或删改。
- GRI 索引只能用于定位，不能单独支撑 positive disclosure。
- 每条 `disclosed` 或 `partially_disclosed` 必须有正文实质证据。
- `manual_review` 必须说明 reason code。
- `not_applicable` 默认需要解释来源，不因报告缺少内容直接判定。
- GRI 3-3 按报告 GRI 索引逐行展开为 topic-level instances，不以 `3-3_generic` 进入普通评分。
- 2024 current disclosure、2026 readiness、2027 watchlist 分开管理。
- Advisor 建议必须基于核验结论，不推断企业内部不存在某项制度或管理活动。

## 17. 常见问题与排障

### 17.1 后端启动时报 `No module named uvicorn`

原因通常是 conda 环境不可写或依赖安装到了 user site，当前环境没有加载。处理方式：

```powershell
python -m pip install --target vendor/python_runtime "anyio>=4.0.0" "uvicorn[standard]>=0.24.0"
python scripts/run_api.py
```

### 17.2 后端启动时报 `.env` 变量缺失

确认已复制 `.env.example`：

```powershell
Copy-Item .env.example .env
```

然后检查 `src/config/settings.py` 中所有 `get_required_env()` 对应变量是否都存在。

### 17.3 P0 条款复核页面没有 run

先执行 seed：

```powershell
python scripts/seed_stage_e4_pending_review.py
```

再刷新 Streamlit 页面。

### 17.4 页面显示 143 条 assessment，但 Advisor 数量不是 143

检查 seed 输入：

- `final_current_effective_assessment_set.json`
- `analysis_run.json`
- `final_advisor_result_corrected.json`
- `advisor_review_sheet.json`

`seed_stage_e4_pending_review.py` 会校验数量，若 mismatch 会直接抛错。

### 17.5 `git diff --check` 只有 CRLF/LF warning

这类提示来自 Windows 换行转换。只要没有 `trailing whitespace`、`space before tab`、`new blank line at EOF` 等错误，不影响当前功能验证。

### 17.6 Streamlit 端口被占用

指定新端口：

```powershell
streamlit run src/ui/app.py --server.port 8521
```

### 17.7 不想调用外部 LLM，只想看 P0 工作台

可以。E4 工作台使用已接受的 Stage E artifacts，启动 API/UI 和 seed SQLite 不需要重新调用 LLM。

## 18. 开发约束

- 依赖声明以 `pyproject.toml` 为准。
- `.env`、密钥、外部模型响应中的非公开数据不得提交。
- 临时文件优先放在 `tmp/`。
- 大型运行产物放在 `data/runs/`，保留 run id、输入哈希、标准 profile、prompt/model 参数和验证记录。
- 当前仓库已有历史运行产物，修改时应保留 raw artifacts，不覆盖审计留痕。
- 新增逻辑应补充最小可重复测试。
- 文档中的已实现能力必须与代码、数据和 smoke 结果一致。

## 19. 当前风险与后续建议

当前适合继续推进 Stage G：

- 交付包整理
- 演示脚本
- 汇报材料
- 使用说明和答辩口径
- 面试或项目陈述材料

仍需避免的表述：

- 不写“最终人工验证通过”
- 不写“已完成最终准确率评估”
- 不写“完整多公司 ESG 智能分析平台”
- 不写“对外披露建议已经确认”

后续工程化方向：

1. 将固定报告 artifact-backed 链路扩展为任意报告上传后的完整重跑链路。
2. 将 evidence binding 全面统一到 `evidence_id`。
3. 在 E4 页面补充更严格的 evidence traceability 展示。
4. 生产化 SQLite/ChromaDB 路径管理和任务队列。
5. 将 P1/P2 能力拆成独立阶段门，避免影响 P0 稳定性。

## 20. 面向追问的回答口径

### 20.1 这个系统到底完成了什么？

完成了一个固定报告的 P0 产品闭环：基于远景能源 2024 ESG 报告和 GRI current disclosure profile，形成 143 条 accepted assessment，接入 SQLite/API/Streamlit 工作台，支持条款级证据查看、人工复核保存和 CSV/JSON 导出。

### 20.2 为什么说是 pending-review？

因为 AI 辅助结果已经形成并通过阶段 smoke，但每条结论仍需人工最终确认。当前页面展示的是可复核工作台，不宣称最终人工验证通过。

### 20.3 为什么不是 118 条？

118 是早期 manifest 技术记录口径，混有未来标准记录。当前 2024 current disclosure 的最终核验范围使用 143 条：114 条 ordinary current disclosure + 29 条 GRI 3-3 instances。

### 20.4 为什么要把 GRI 3-3 展开？

GRI 3-3 是“重大议题管理方针”披露，不同议题的管理动作、影响、指标和利益相关方参与不同。用 `3-3_generic` 单条评分会掩盖实际差异，因此按报告 GRI 索引逐行展开。

### 20.5 为什么不直接用 GRI 索引判断披露？

索引只能说明企业声称某处对应某个 disclosure。实际披露充分性需要正文证据支持，尤其是定量指标、方法、边界、拆分维度和省略理由。

### 20.6 这个项目和论文实验是什么关系？

项目产物可以支撑论文实验，但产品闭环不依赖论文指标完成。F 阶段人工评测数据当前已归档，后续可用于时间、准确性、证据可追溯性和人工修正量比较。

### 20.7 当前最适合展示什么？

适合展示 E4 P0 条款复核工作台：143 条 assessment、143 条 Advisor coverage、证据页码、requirement checks、人工复核保存和导出。

## 21. 相关文档

| 文档 | 说明 |
|---|---|
| `docs/用户操作手册.md` | 面向使用者的页面和流程说明 |
| `docs/项目模型说明文档.md` | 当前架构、模型、Agent 和数据结构说明 |
| `docs/DEV_LOG.md` | 阶段运行记录、验证结果和决策留痕 |
| `docs/P0-P1-P2需求对齐表.md` | 需求来源、P0 落点和 P1/P2 保留项 |
| `docs/stage_e/stage_e_runbook.md` | Stage E 运行手册 |
| `docs/stage_e3/e3_current_scope_acceptance_result.json` | E3 current scope acceptance 记录 |
| `docs/stage_e3_5/e3_5_gri_3_3_execution_notes.md` | GRI 3-3 展开执行记录 |
| `docs/stage_e3_cleanup/e3_traceability_cleanup_acceptance_gate.json` | traceability cleanup 接受记录 |
| `docs/stage_f/f_human_evaluation_guide.md` | F 阶段人工评测说明 |
