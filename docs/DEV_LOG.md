# 开发日志（DEV_LOG）

## 2026-06-27｜P0 阶段 E0 计划入口

E0 用于收敛真实运行前缺口，优先处理 AdvisorAgent P0 分支、evidence chunk metadata、verdict 映射、dry-run 输出保存和人工复核模板。

AnalysisRun 持久化、API、Streamlit 重写、全量中文译文和 ChromaDB 重建记录为后续阶段事项，不作为 E0 阻塞。

## 2026-06-27｜P0 阶段 D：Agent 合约对齐验收

### 已完成

- P0 Agent context 已可构造 118 条 requirement contexts。
- RetrievalAgent 已返回 `p0_requirement_contexts`、`p0_contract_version` 和 `retrieval_summary.p0_requirement_count`。
- `analyst_prompt.j2` 已支持 P0 `disclosure_assessments` 分支，并保留旧 `gap_analysis + peer_comparison` 分支。
- AnalystAgent 已支持 P0 分支，将 LLM JSON 输出校验为 `DisclosureAssessment` 兼容结构。
- OrchestratorAgent 已在 `disclosure_assessments` 非空时汇总 `AnalysisRun`。
- 新增 `scripts/validate_stage_d_agent_contract.py`，用于验证 118 条上下文、5 条人工 locator 页码和 Agent 高置信字段消费规则。

### 验证结果

```text
py_compile: passed
validate_p0_evidence_layer.py: status=ok, requirements=118, manual_locator_review_count=5, errors=[]
validate_stage_d_agent_contract.py: status=ok, context_count=118, manual_locator_context_count=5, errors=[]
stub verification: analyst_assessments=1, analysis_run_manifest_version=0.1, analysis_run_assessments=1, analysis_run_sources=2
```

### 已知非阻塞风险

- AdvisorAgent 仍为旧逻辑；P0 下可能返回 `skipped`。
- 尚未执行真实外部 LLM 端到端运行。
- CRLF/LF warning 暂不处理，提交前再单独评估。
- `audit metadata/sections` 暂未强一致校验。
- `manual_locator_review.confirmed_title/review_reason` 暂未全文锁定。
- `build CLI` 暂未暴露 `--rebuild-report-index`。

### 下一阶段入口

阶段 E 应进入真实运行、人工复核和误差复盘，目标是证明 P0 链路能产出可信的单报告 ESG 分析结果。
## 2026-03-26 当前状态快照

本文件记录当前仓库的实现状态，不再沿用早期的旧模块命名。

## 1. 当前已落地能力

### 1.1 单报告分析主链路

已实现并可从前端串起来的主流程：

`CorpusAgent -> RetrievalAgent -> AnalystAgent -> AdvisorAgent`

对应能力：

- 报告解析与分块
- 议题识别与知识库检索
- 差距分析
- 优化建议生成
- 人工复核导出

### 1.2 审计与规则管理

当前已经具备：

- 审计日志写入、查询、导出、哈希校验
- 规则页面可视化编辑
- 规则备份与恢复

### 1.3 知识库导入

当前仓库中可用的导入脚本：

- `scripts/import_standards.py`
- `scripts/import_peer_reports.py`

## 2. 当前架构结论

### 2.1 Agent 架构

当前架构是 `1 + 4`：

```text
OrchestratorAgent
├── CorpusAgent
├── RetrievalAgent
├── AnalystAgent
└── AdvisorAgent
```

### 2.2 已废弃的旧命名

以下命名不应再被视为当前模块：

- `ExtractAgent`
- `ComplianceAgent`
- `ContentAgent`
- `MasterAgent`

如果在仓库中看到这些名字，通常是历史注释、旧文档或迁移说明。

## 3. 当前技术栈

- Python `>=3.10`，推荐按 `environment.yml` 使用 `3.13`
- 前端：Streamlit
- 后端：FastAPI
- LLM：OpenAI 兼容接口
- 向量库：ChromaDB
- 嵌入模型：SiliconFlow `BAAI/bge-m3`
- 审计存储：SQLite

## 4. 当前前端状态

### 4.1 已可用页面

- 首页概览
- 报告上传
- 议题识别
- 差距分析
- 人工复核
- 审计日志
- 规则配置

### 4.2 占位页面

- 对标分析：页面已存在，但当前是规划说明，不是已实现能力

### 4.3 页面行为说明

- 首页核心指标是静态演示值
- 议题识别页在已有 `corpus_result` 时会自动发起检索
- 差距分析与建议生成目前仍由用户在页面手动点击触发

## 5. 当前数据层状态

### 5.1 本地持久化

当前运行时会使用：

- `data/chroma_db/`
- `data/raw_corpus/`
- `data/sqlite_db/audit_log.db`
- `data/export_results/`

### 5.2 知识库目录

当前知识库材料位于：

- `data/knowledge_base/standards/`
- `data/knowledge_base/peer_reports/`
- `data/knowledge_base/topic_taxonomy/`

## 6. 当前未完成项

以下功能仍未真正落地：

- 多企业对标工作流
- 对话式检索问答
- 披露标准版本差异分析

## 7. 本次文档同步说明

本轮已完成以下同步动作：

- 重写部署说明文档
- 重写 FAQ
- 重写用户操作手册
- 重写项目模型说明文档
- 重写项目专用 AGENTS 文档
- 删除两份与当前实现不一致的历史文档

后续如果再次调整架构、环境变量或前端行为，应优先更新文档，避免继续积累“文档比代码老一代”的问题。



