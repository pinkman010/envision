# 开发日志（DEV_LOG）

## 2026-06-28｜P0 阶段 E1 小样本真实 LLM 运行

本次运行使用 E1 样本清单，真实调用 DeepSeek `deepseek-v4-flash`，产物保存于 `data/runs/stage_e/20260628T150050Z_e1_sample/`。

### 运行结果

```text
run_id: 20260628T150050Z_e1_sample
sample_count: 7
assessment_count: 7
llm_called: true
model: deepseek-v4-flash
run_dir validation: ok
```

### 输出摘要

```text
verdict_counts:
- disclosed: 2
- manual_review: 4
- not_applicable: 1

review_status_counts:
- pending: 7

manual_review_input items: 7
advisor recommendations: 6
```

### 验证结果

```text
run_p0_stage_e1_real_run.py --confirm-llm: status=ok
validate_stage_e1_agent_outputs.py --run-dir data/runs/stage_e/20260628T150050Z_e1_sample: status=ok, errors=[]
```

### 过程修正

- 第一次真实运行失败于 Analyst 阶段：`finish_reason=length`，原因是 `LLM_MAX_TOKENS=4096` 对 thinking=max + 7 条样本 JSON 输出偏低。
- 已将 `.env` 和 `.env.example` 中 `LLM_MAX_TOKENS` 调整为 `8192`。
- 第二次真实运行失败于 Analyst 结构化校验：模型输出 `review_status=completed`。
- 已修正 `analyst_prompt.j2`，明确所有 AI 输出的 `review_status` 固定为 `pending`。
- 已在 `AnalystAgent` 中将模型输出的 `review_status` 强制归一为 `pending`，因为复核状态是系统控制字段，不应由模型决定。

### 限制

- 本次结果仍需 E2 人工复核，不作为正式披露结论。
- 尚未执行 2024 当前披露范围全量运行。

## 2026-06-28｜P0 阶段 E1 真实运行入口脚本

本次只实现 E1 真实小样本运行入口，不调用真实 LLM。

### 已完成

- 新增 `scripts/run_p0_stage_e1_real_run.py`。
- 脚本支持 `--sample-manifest`、`--output-dir`、`--confirm-llm`。
- 未传 `--confirm-llm` 时，脚本在调用任何 Agent/LLM 前退出，并返回退出码 2。
- 脚本真实运行路径已实现：按 E1 样本构造 `retrieval_result`，调用 AnalystAgent 和 AdvisorAgent，保存 `analysis_run.json`、raw LLM output、`manual_review_input.json` 和 `run_summary.json`。

### 验证结果

```text
py_compile scripts/run_p0_stage_e1_real_run.py scripts/validate_stage_e1_agent_outputs.py: passed
run_p0_stage_e1_real_run.py without --confirm-llm: exit_code=2
```

### 限制

- 本次未执行 `--confirm-llm`，未调用真实 DeepSeek API。
- 阶段 E1 真实小样本运行仍需单独执行。

## 2026-06-28｜P0 阶段 E1 前置 sample-only 验证

本次只执行 E1 前置 sample-only 部分，不调用真实 LLM，不进入 E1 小样本真实运行。

### 已完成

- 新增 E1 小样本清单：`data/knowledge_base/manifests/p0_stage_e1_sample_manifest.json`。
- 样本覆盖 7 条：普通 current_gap、人工 locator 复核条目、历史 locator 边界项、`requires_topic_instantiation` 边界项和非 current-gap readiness 条目。
- 新增 `scripts/validate_stage_e1_agent_outputs.py`，支持 `--sample-only` 前置校验，并预留 `--run-dir` 结构化输出校验入口。

### 验证结果

```text
py_compile scripts/validate_stage_e1_agent_outputs.py: passed
validate_stage_e1_agent_outputs.py --sample-only: status=ok, sample_count=7, errors=[]
validate_p0_evidence_layer.py: status=ok, requirements=118, manual_locator_review_count=5, errors=[]
validate_stage_d_agent_contract.py: status=ok, context_count=118, manual_locator_context_count=5, errors=[]
run_p0_stage_e_dry_run.py --no-llm: status=ok, llm_called=false
check_llm_config.py: status=ok, model=deepseek-v4-flash, response_format=json_object, temperature_will_be_sent=false
pdfplumber: 0.11.9
```

### 说明

- `readiness_2026:GRI101` 无 report evidence chunk，但它不是 current_gap，`allowed_empty_evidence=true`，属于非阻塞 warning。
- 阶段 E1 真实 LLM 小样本运行仍未执行。

## 2026-06-28｜P0 阶段 E1.0 DeepSeek LLM Adapter 实施与验证

E1.0 用于在 E1 小样本真实 LLM 运行前补齐 DeepSeek OpenAI-compatible API 适配：thinking、reasoning_effort、JSON Output、usage metadata 和不泄露密钥的配置检查。

本阶段不执行真实 LLM 分析，不修改 UI/API/数据库，不改变 E1/E2/E3/E4 编号。

### 已完成

- `.env.example` 已更新 DeepSeek v4 flash、thinking、reasoning_effort 和 JSON Output 示例。
- `settings.py` 已支持 `LLM_THINKING_TYPE`、`LLM_REASONING_EFFORT`、`LLM_RESPONSE_FORMAT`。
- `llm_utils.py` 已支持 thinking enabled/disabled、`reasoning_effort`、`response_format={"type":"json_object"}`，且 thinking enabled 时不传 `temperature`。
- 新增 `call_llm_with_metadata()`，保留原 `call_llm()` 字符串返回接口。
- 新增 `scripts/check_llm_config.py`，配置检查不输出 API key 明文。
- 新增 `scripts/validate_deepseek_llm_adapter.py`，使用 fake client 验证 adapter，不发出网络请求。

### 验证结果

```text
py_compile: passed
check_llm_config.py: status=ok, base_url=https://api.deepseek.com, model=deepseek-v4-flash, effective_thinking_type=enabled, reasoning_effort=max, response_format=json_object, temperature_will_be_sent=false
validate_deepseek_llm_adapter.py: status=ok, errors=[]
validate_p0_evidence_layer.py: status=ok, requirements=118, manual_locator_review_count=5, errors=[]
validate_stage_d_agent_contract.py: status=ok, context_count=118, manual_locator_context_count=5, errors=[]
run_p0_stage_e_dry_run.py --no-llm: status=ok, llm_called=false
```

### 限制

- 本阶段未调用真实 DeepSeek API；真实小样本运行仍属于阶段 E1。
- `.env` 已补充非密钥配置 `LLM_THINKING_TYPE=enabled`、`LLM_REASONING_EFFORT=max`、`LLM_RESPONSE_FORMAT=json_object`；`.env` 不应提交。

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

## 2026-06-29 Stage E2.1 plan

- 基于 E2 人工复核结果，新增 E2.1 证据契约加固计划。
- 计划文件：`docs/superpowers/plans/2026-06-29-p0-stage-e2-1-evidence-contract-hardening.md`。
- 阶段目标：修复 index-only overclaim 风险，固化 E2 regression sample。
- E2 人工复核结论：模型链路可用，但存在“索引命中即充分披露”的过度判断风险。
- 下一阶段不直接执行 E3；先完成 Evidence 分类、requirement checklist、index-only disclosed 防线和 regression 校验，之后再进入“2024 当前披露范围全量运行”。
- 本计划不修改 UI/API/DB，不调用外部 LLM，不 stage、不 commit。

## 2026-06-29 Stage E2.1 plan replacement

- 基于后续范围复核，旧版 E2.1 计划已被新版计划替代。
- 新计划文件：`docs/superpowers/plans/2026-06-29-p0-stage-e2-1-requirement-checklist-and-evidence-contract.md`。
- 替代原因：E2 暴露的问题不只是 index-only guardrail 缺失，而是缺少 P0 requirement 叶子项逐项核验后再汇总结论的稳定阶段门。
- 冻结口径：118 条为 manifest 全部技术记录；115 条为 2024 当前披露分析规范化记录；最终核验单元为普通披露项叶子 requirement 加后续 GRI 3-3 议题实例化结果，当前仅写预计约 143 条。
- 阶段 E3 改名为“2024 当前披露范围全量运行”；`readiness_2026` 和 `watchlist_2027` 单独输出，不进入 2024 披露结果统计。
- 旧计划 `2026-06-29-p0-stage-e2-1-evidence-contract-hardening.md` 已移除。

## 2026-06-29 Stage E2.1-B local contract hardening

- 已完成 E2.1-B 本地结构加固，未调用 LLM，未重建知识库，未修改 UI/API/DB。
- 扩展 `Evidence`、`RequirementCheck`、`DisclosureAssessment` 契约：新增四类 `evidence_kind`、requirement 级 `support_status`、缺失 requirement 列表和汇总理由。
- 扩展 P0 Agent context：每个 context 挂载 `requirement_checklist_items` 和四类 `evidence_bundle`；现有报告索引页证据标记为 `index_evidence`。
- 更新 Analyst Prompt 与 AnalystAgent guardrail：阻断 index-only `disclosed`、缺少 `requirement_checks` 的 `disclosed`、`3-3_generic` 非 `manual_review` 结论。
- 更新 Advisor Prompt：建议链路消费 `missing_requirements` 与 `manual_review_requirements`，并区分 `report_content_improvement` 与 `internal_management_followup`。
- 新增 `p0_stage_e2_regression_manifest.json` 与 `validate_stage_e2_1_evidence_contract.py`，固化 `GRI2:2-1`、`GRI302:302-4`、`3-3_generic` 高风险回归样本。
- 本地验证：`tests/test_stage_e2_1_evidence_contract.py` 与 `tests/test_p0_requirement_checklist.py` 合计 13 项通过；`validate_stage_e2_1_evidence_contract.py`、`validate_p0_requirement_checklist.py`、`validate_stage_e1_agent_outputs.py --sample-only` 均通过。
- 限制：真实 LLM 小样本回归尚未执行；`effective_date` 仍继承 checklist 当前状态，661 个 current requirement 为 `null` 并由校验脚本统计。

### E2.1-B review fixes

- 规格复核发现 `p0_stage_e2_regression_manifest.json` 中的 `blocked_verdicts` 尚未参与 assessment 校验；已修复 `validate_stage_e2_1_evidence_contract.py`，现在 `GRI2:2-1` 和 `GRI302:302-4` 即使具备非索引证据和 `met` checks，也会被 regression gate 阻断为不能直接 `disclosed`。
- 验证脚本已补齐 `--run-dir` 与 `--manual-review-result` 参数，兼容计划中的本地验收命令。
- 代码质量复核发现 Analyst guardrail 对 LLM 照抄 chunk 字段不够容错；已增加 `Evidence` 白名单字段清洗，将 `pdf_page/text` 映射为 `source_page/source_text`，避免 `extra="forbid"` 触发结构化校验失败。
- 已补齐无证据确定性结论防线：current-gap 条目在无证据时不能输出确定性 `not_disclosed`，会降级为 `manual_review`。
- 已补齐非 current-gap 政策性排除豁免：`readiness_2026` / `watchlist_2027` 的 forced `not_applicable` 不再被误判为缺少企业不适用说明。
- 修复后本地验证：`tests/test_stage_e2_1_evidence_contract.py` 与 `tests/test_p0_requirement_checklist.py` 合计 15 项通过；`validate_stage_e2_1_evidence_contract.py --manual-review-result data/runs/stage_e/20260628T150050Z_e1_sample/manual_review_result.json` 通过。
- 复审发现 validator 层仍会误伤非 current-gap 的政策性 `not_applicable`；已补齐 assessment-level 校验豁免，`readiness_2026` / `watchlist_2027` 无需企业不适用说明即可作为 2024 当前披露统计外项目通过。
- 最终本地验证：`tests/test_stage_e2_1_evidence_contract.py` 与 `tests/test_p0_requirement_checklist.py` 合计 16 项通过。

## 2026-06-29 Stage E2.1-C local regression entrypoint and requirement sampling

- 已将 E2.1-C 计划文件命名统一为 `docs/superpowers/plans/2026-06-29-p0-stage-e2-1-c-real-llm-regression-and-checklist-sampling.md`，区别于 E2.1-A/B 的 requirement checklist 与 evidence contract 计划。
- 新增 `scripts/run_p0_stage_e2_1_regression.py`，用于合并 E1 原 7 条样本与 E2 regression 高风险样本，生成真实 LLM 小样本回归 run-dir；未传 `--confirm-llm` 时退出码为 2，且不创建 run-dir、不调用 LLM。
- 新增 `tests/test_stage_e2_1_regression_run.py`，覆盖样本合并去重、LLM 调用保护，以及 E2.1 run-dir 继续兼容 E1 输出验证器的底层契约版本。
- 新增 requirement 抽样核对链路：`scripts/build_p0_requirement_sampling_manifest.py`、`scripts/validate_p0_requirement_sampling_manifest.py`、`data/knowledge_base/manifests/p0_requirement_checklist_sampling_manifest.json`、`data/review/e2_1_requirement_sampling_review_template.json`。
- 当前抽样清单共 40 条 requirement，覆盖 `GRI2:2-1`、`GRI2:2-21`、`GRI302:302-4`、`GRI306:306-4`、`GRI401:401-1` 高风险父项；覆盖 7 个 standard、15 个 official PDF page、33 条 requirement 和 7 条 compilation_requirement。
- 本地预检通过：`check_llm_config.py`、`validate_stage_e2_1_evidence_contract.py`、`validate_p0_requirement_checklist.py`、`validate_stage_e1_agent_outputs.py --sample-only` 均为 ok。
- 本地测试通过：`tests/test_stage_e2_1_evidence_contract.py`、`tests/test_p0_requirement_checklist.py`、`tests/test_stage_e2_1_regression_run.py`、`tests/test_p0_requirement_sampling_manifest.py` 合计 23 项通过。
- 收尾复核发现 disclosed gate 只校验模型已输出的 mandatory checks，未反查 checklist 覆盖全部 mandatory requirements；已修复 Analyst guardrail 和 E2.1 validator，漏列 mandatory requirement check 的 `disclosed` 会被降级或判失败。
- 限制：真实 E2.1 LLM 小样本回归尚未执行；requirement 抽样清单只完成结构抽样，页码、文本边界、requirement_type 和 scoring_role 真实性仍需人工核对。

## 2026-06-29 Stage E2.1-C real LLM regression and DeepSeek token limit

- 已按用户明确授权执行真实 E2.1 LLM 小样本回归，外部模型为 DeepSeek `deepseek-v4-flash`。
- 第一次运行 `20260629T135849Z_e2_1_regression` 在 Analyst 阶段失败，原因是 `LLM_MAX_TOKENS=8192` 导致模型输出 `finish_reason=length` 截断；失败产物保留于 `data/runs/stage_e/20260629T135849Z_e2_1_regression/`。
- 第二次运行使用进程级 `LLM_MAX_TOKENS=16384` 和 `LLM_TIMEOUT=240` 成功，产物保留于 `data/runs/stage_e/20260629T140355Z_e2_1_regression/`，`sample_count=7`，`assessment_count=7`，`llm_called=true`。
- 已根据 DeepSeek 官方文档中 `deepseek-v4-flash` 输出长度最大 `384K` 的说明，将 `.env` 与 `.env.example` 的 `LLM_MAX_TOKENS` 调整为 `393216`（384 * 1024）。
- 验证通过：`check_llm_config.py` 为 ok；`validate_stage_e2_1_evidence_contract.py --run-dir data/runs/stage_e/20260629T140355Z_e2_1_regression` 为 ok；`validate_stage_e1_agent_outputs.py --run-dir data/runs/stage_e/20260629T140355Z_e2_1_regression` 为 ok，保留 `readiness_2026:GRI101` 空证据 warning。
- 限制：真实回归结果仍需人工复核，不能直接作为最终披露结论；`LLM_MAX_TOKENS=393216` 会显著提高单次请求的理论输出上限，后续正式运行仍应监控成本、延迟和 API 实际限流。

## 2026-06-29 Stage E2.1-C manual review result

- 已将 E2.1 小样本人工复核结果写入 `data/runs/stage_e/20260629T140355Z_e2_1_regression/manual_review_result.json`，复核状态为 `completed`。
- 复核范围：7 条样本；人工结论为 `partially_disclosed=4`、`manual_review=2`、`not_applicable=1`；`readiness_2026:GRI101` 另记录 `readiness_verdict=readiness_gap`。
- 阶段门判断：`blocked_before_e3`。E2.1 guardrail 未发现 index-only `disclosed` 放行问题，但检索/证据层过度依赖 GRI 索引，未自动补取索引指向页正文证据，导致多条样本被保守判为 `manual_review`。
- 关键人工发现：`GRI2:2-1`、`GRI302:302-4`、`GRI306:306-4`、`GRI401:401-1` 均存在额外正文证据，应为 `partially_disclosed`；`GRI2:2-21` 为省略理由待审；`GRI3:3-3_generic` 仍需议题实例化；`GRI101` 需从 current_gap 五分类中分离为 2026 readiness gap。
- 主流程修复点：索引 evidence 仅用于定位；索引命中后需自动补取指向页正文证据；保留 source_text 表格横向串列错误标签；manual_review reason 需分类；`401-1:2.1` 需 requirement scope 复核；`302-4:2.7`、`306-4:2.2` 等 compilation parent 不应单独参与 aggregation。
- 验证通过：`validate_stage_e2_1_evidence_contract.py --manual-review-result data/runs/stage_e/20260629T140355Z_e2_1_regression/manual_review_result.json` 为 ok。

## 2026-06-29 Stage E2.1-D plan

- 已写入 E2.1-D 修复计划：`docs/superpowers/plans/2026-06-29-p0-stage-e2-1-d-index-target-and-fulltext-evidence-retrieval.md`。
- 计划目标：解除 E2.1-C 人工复核形成的 `blocked_before_e3`，修复索引指向页正文补取、全文证据检索、index evidence 支持关系、manual_review reason 分类、readiness 独立结论、`401-1:2.1` scope 和 compilation parent aggregation。
- 生命周期计划已同步：E3 进入条件改为 E2.1-D 修复、复测、人工复核和 requirement 抽样核对均通过后才允许进入。
- 本次仅写入计划和文档同步，未修改业务代码，未调用 LLM，未重建知识库。

## 2026-06-30 Stage E2.1-D real regression manual review

- 已按授权执行 E2.1-D 真实 DeepSeek 小样本回归，run id 为 `20260629T170447Z_e2_1_regression`，`sample_count=7`，`assessment_count=7`，`llm_called=true`。
- 本地验证通过：`validate_stage_e1_agent_outputs.py --run-dir data/runs/stage_e/20260629T170447Z_e2_1_regression` 为 ok；`validate_stage_e2_1_evidence_contract.py --run-dir data/runs/stage_e/20260629T170447Z_e2_1_regression --require-e2-1-d-body-evidence` 为 ok。
- 已将人工复核结果写入 `data/runs/stage_e/20260629T170447Z_e2_1_regression/manual_review_result.json`，复核状态为 `completed`，验证命令 `validate_stage_e2_1_evidence_contract.py --manual-review-result data/runs/stage_e/20260629T170447Z_e2_1_regression/manual_review_result.json` 为 ok。
- 人工结论：`partially_disclosed=4`、`manual_review=2`、`not_applicable=1`；`readiness_2026:GRI101` 另保留 `readiness_verdict=readiness_gap`。
- 阶段门判断：`conditionally_passed_before_e3`，等价记录为 `passed_with_required_field_corrections`。E2.1-D 已修复“过度依赖 GRI 索引、缺少正文证据导致过度 manual_review”的主问题，但不作为无条件 E3 放行。
- E3 前必修项：`GRI2:2-21` 顶层 verdict 从 `not_applicable` 改为 `manual_review` 并附 `omission_reason_requires_review`；`2-1`、`302-4`、`306-4`、`401-1` 的 `missing_requirements` 改为子维度颗粒度；证据输出同时保留 PDF `source_page` 与 `report_page_label`；建议文本避免根据公开报告推断企业内部不存在制度或数据；`3-3_generic` 继续不进入普通评分。

## 2026-06-30 Stage E2.1-E field corrections before current full run

- 已吸收 E2.1-D 人工复核字段修正，未执行 E3 全量运行，未调用外部 LLM。
- 已修复 `manual_review_result.json` 审计层结构化字段，并新增 `data/review/e2_1_e_field_correction_expectations.json` 固化 7 条样本字段修正预期。
- 已修正 `GRI2:2-21` 省略披露语义：商业保密从略披露进入 `manual_review + omission_reason_requires_review`，不作为 `not_applicable`。
- 已区分 `partial_requirements` 与 `missing_requirements`，并补强 guardrail，避免 `partially_met` requirement 同时出现在 missing 与 partial 中。
- 已强化 `3-3_generic` 非普通评分状态：输出 `manual_review + needs_topic_instantiation + not_scored_requires_topic_instantiation`，并清空普通评分字段。
- 已强化 readiness 字段：`readiness_2026` 政策性 `not_applicable` 会覆盖错误预填值，保留 `readiness_verdict=readiness_gap`。
- 已强化 evidence 页码契约：`source_page` 为 PDF 物理页码，`report_page_label` 为报告印刷页码或 `cover`；E2.1-D 人工修正页码已写入结构化 `field_corrections.evidence_pages_to_add`。
- 已约束 Advisor 建议边界：公开报告未披露只能写“报告未披露/无法核实”，不得推断企业内部不存在制度、数据或管理活动；需要内部信息时标记 `internal_management_followup`。
- 新增 `scripts/validate_stage_e2_1_e_field_corrections.py`，对阶段门决策、7 条 item、字段修正、结构化页码、requirement 颗粒度和 readiness/3-3 语义做本地校验。
- 验证通过：`pytest tests/test_stage_e2_1_e_field_corrections.py tests/test_stage_e2_1_evidence_contract.py tests/test_stage_e2_1_d_index_target_evidence.py tests/test_p0_requirement_checklist.py -q -p no:cacheprovider --basetemp tmp/pytest-e2-1-e-pre-final-2`，结果 45 passed。
- 验证通过：`validate_stage_e2_1_e_field_corrections.py`、`validate_stage_e2_1_evidence_contract.py --manual-review-result data/runs/stage_e/20260629T170447Z_e2_1_regression/manual_review_result.json`、`validate_p0_index_target_evidence.py`、`validate_p0_requirement_checklist.py` 均为 `status: ok`。
- 阶段门判断：E2.1-E 本地字段修正通过，可进入 E3 普通 current disclosure 全量运行准备；E3 真实运行仍需单独确认，`readiness_2026`、`watchlist_2027` 和 `3-3_generic` 不进入普通 current-gap 评分。

## 2026-06-30 Stage E3 planning and documentation closure

- 当前未执行 E3 真实运行，未调用外部 LLM。
- 已修正 `docs/ESG项目全生命周期实施计划.md` 9.4 历史残留：RetrievalAgent 结构化 Evidence 和 Agent 间独立结构化校验不再标记为 E1 前置未完成，改为 E2.1 已完成基础契约、E4 前做 API / Streamlit 层结构化稳定性回归。
- 已新增 E3 运行冻结包：
  - `docs/stage_e3/e3_current_scope_manifest.json`
  - `docs/stage_e3/e3_llm_invocation_approval.md`
  - `docs/stage_e3/e3_preflight_validation.md`
  - `docs/stage_e3/e3_expected_outputs.md`
- 已新增 E3 计划文件：`docs/superpowers/plans/2026-06-30-p0-stage-e3-current-disclosure-full-run.md`。
- E3 执行口径已改为分批运行：GRI 2、GRI 3（不含 3-3 generic）、环境、员工/人权、治理/供应链；每批需 hard gate 和 3-5 条 smoke review 通过后才进入下一批。
- 已在生命周期计划中新增 E3.5：普通 E3 通过后，单独处理 GRI 3-3 议题级实例化。
- 已新增 `docs/P0-P1-P2需求对齐表.md`，明确 P0 是单报告 GRI 披露证据核验验证样例；友商对标、客户/融资银行/资本市场视角、第三方数据库、供应链风险监测、Claw 舆情、登录、多用户和管理驾驶舱均保留为 P1/P2 roadmap。
- 已补充 E3 preflight 口径：记录 `git status --short` 审计快照；检查 `current_gap:GRI405:405-2` 和 `current_gap:GRI414:414-2` 精确 ID，避免 405-2 / 414-2 拼写或映射错误。
- 已补充 E3 LLM 授权口径：每批 approval 需记录 prompt 模板版本或 hash、关键 LLM 参数、预计 token、成本风险和时延风险。
- 已在生命周期计划 9.4 增补 E4 风险：RetrievalAgent 结构化 evidence 回归、AdvisorAgent P0 输出结构化校验。
- 阶段判断：现在仍不直接跑 E3；下一步是在用户明确授权后执行 E3 第一批 `e3_batch_01_gri2` 的真实运行。

## 2026-06-30 Stage E3 batch 01 GRI2 real run

- 已按用户明确授权执行 E3 第一批 `e3_batch_01_gri2` 真实 DeepSeek 运行，发送范围限于公开报告证据片段、GRI requirement 数据和 Prompt。
- 新增受 `--confirm-llm` 保护的批次运行入口 `scripts/run_p0_stage_e3_batch.py`；未传确认参数时不创建 run-dir、不调用外部 LLM。
- 新增 `scripts/validate_stage_e3_batch_outputs.py` 与 `tests/test_stage_e3_batch_outputs.py`，校验 E3 批次范围、输出文件、current_gap 范围、非 index-only 正向结论、partial 缺口字段、manual_review reason、正文证据字段、页码偏移和 Advisor 越界推断。
- 第一次真实运行 `20260630T020614Z_e3_batch_01_gri2` 在 Analyst 阶段失败，原因是 LLM 输出 `support_status=partial_met`，不符合本地契约枚举；失败产物保留于 `data/runs/stage_e/20260630T020614Z_e3_batch_01_gri2/`。
- 已修复 Analyst 输出归一化：`partial_met`、`partially met`、`not applicable`、`not assessed` 等常见别名会映射到本地 `RequirementSupportStatus` 枚举。
- 已同步 E2.1 证据契约校验器口径：`partially_disclosed` 可由 `missing_requirements` 或 `partial_requirements` 支撑，符合 E3 hard gate。
- 第二次真实运行成功，run id 为 `20260630T021253Z_e3_batch_01_gri2`，产物保留于 `data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2/`，`sample_count=30`，`assessment_count=30`，`llm_called=true`。
- Verdict 分布：`partially_disclosed=14`、`manual_review=13`、`disclosed=2`、`not_disclosed=1`。
- 已生成人工 smoke review 模板 `data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2/smoke_review_template.json`，抽样项为 `2-22`、`2-1`、`2-4`、`2-6`、`2-8`。
- 验证通过：`py_compile` 覆盖 Analyst、E3 runner、E3 validator、E2.1 validator；`pytest tests/test_stage_e2_1_evidence_contract.py tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-batch`，结果 29 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2` 为 ok；`validate_stage_e2_1_evidence_contract.py --run-dir data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2` 为 ok。
- 阶段判断：E3 batch 01 本地 hard gate 通过，但尚未完成人工 smoke review；进入 batch 02 前需先复核 smoke review 5 条样本，重点检查 `disclosed` 是否有正文实质证据、`manual_review` reason 是否准确、`partial_requirements` 与页码是否符合报告原文。

## 2026-06-30 Stage E3 batch 01 smoke review and field corrections

- 已吸收 E3 batch 01 GRI2 smoke review 人工结论，阶段门记录为 `blocked_before_batch_02`，blocking reasons 为 `evidence_page_error`、`source_text_not_verbatim`、`verdict_rule_adjustment_required`。
- 已写入 `data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2/smoke_review_result.json`，覆盖 5 条样本：`2-22`、`2-1`、`2-4`、`2-6`、`2-8`。
- 已新增 `scripts/apply_stage_e3_batch01_smoke_corrections.py`，保留 raw LLM artifact 不变，生成：
  - `analyst_result_corrected.json`
  - `analysis_run_corrected.json`
  - `stage_gate_result.json`
  - `batch_validation_result_after_smoke_corrections.json`
- 已修正 `2-22` source_text：替换省略号概括为 PDF 第 4 页/报告第 3 页和 PDF 第 5 页/报告第 4 页的可定位逐字短片段。
- 已修正 `2-1` requirement 颗粒度：`2-1-b` 与 `2-1-c` 进入 `partial_requirements`，`2-1-d` 保持 `missing_requirements`。
- 已修正 `2-6`：UNGC 证据页码改为 PDF 第 9 页/报告第 8 页；补充供应链证据支持 `2-6-b:ii`，补充 DHL 和西班牙政府合作证据支持 `2-6-c`；`2-6-b:iii` 与 `2-6-d` 保持缺失。
- 已修正 `2-8`：从 `manual_review` 改为 `not_disclosed`，清空 `manual_review_requirements` 与 `manual_review_reason_codes`。
- 已补强 Analyst guardrail：无正文证据、无省略说明、已完成合理检索覆盖且所有适用 hard-score requirement 均为 `not_met` 时，允许 `not_disclosed`，不再一律提升为 `manual_review`。
- 已补强 E3 validator：优先校验 corrected artifact；正文证据 `source_text` 不得使用 `...` 或 `…` 省略号概括；可要求存在 `smoke_review_result.json`。
- 批次级复核时发现除 smoke 5 条外，batch 01 还有 `2-2`、`2-3`、`2-13`、`2-23`、`2-24`、`2-25`、`2-26`、`2-28`、`2-29` 的正文 `source_text` 使用省略号概括或页码绑定不准；已在 corrected artifact 中一并修正为可定位原文短片段，并修正 `2-23`、`2-24`、`2-28` 的 UNGC 页码及 `2-25` 客户反馈证据页码。
- 验证通过：`py_compile` 覆盖修正脚本、E3 validator、Analyst；`pytest tests/test_stage_e2_1_evidence_contract.py tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-smoke-fixes`，结果 31 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2 --require-smoke-review-result` 为 ok，使用 corrected artifact；`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2/analyst_result_corrected.json` 为 ok。
- 修正后 verdict 分布：`partially_disclosed=14`、`manual_review=12`、`not_disclosed=2`、`disclosed=2`。
- 阶段判断：本地修正和 validator 已通过，但 gate 仍保留 `blocked_before_batch_02` 审计记录；进入 batch 02 前需要明确确认是否接受 corrected artifact 作为 batch 01 阶段门输入。

## 2026-06-30 Stage E3 batch 02 GRI3 without 3-3 generic real run

- 已按用户明确授权执行 E3 第二批 `e3_batch_02_gri3_without_3_3` 真实 DeepSeek 运行，发送范围限于公开报告证据片段、GRI requirement 数据和 Prompt。
- 执行前已确认 batch 02 范围仅包含 `current_gap:GRI3:3-1` 与 `current_gap:GRI3:3-2`，明确排除 `current_gap:GRI3:3-3_generic`。
- 真实运行成功，run id 为 `20260630T043746Z_e3_batch_02_gri3_without_3_3`，产物保留于 `data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3/`，`sample_count=2`，`assessment_count=2`，`llm_called=true`。
- Verdict 分布：`partially_disclosed=2`。
- 结果摘要：`GRI3:3-1` 为 `partially_disclosed`，缺口为 `3-1:a:i`、`3-1:a:ii`、`3-1:b`，`3-1:a` 为部分支持；`GRI3:3-2` 为 `partially_disclosed`，缺口为 `3-2:b`。
- 已生成 smoke review 模板 `data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3/smoke_review_template.json`，因本批仅 2 条，模板覆盖全部 batch 02 条目。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3` 为 ok；`validate_stage_e2_1_evidence_contract.py --run-dir data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3` 为 ok。
- 阶段判断：E3 batch 02 本地 hard gate 通过，但尚未完成人工 smoke review；进入 batch 03 environment 前需先复核 `3-1` 与 `3-2` 两条，重点检查 PDF 第 15 页/报告第 14 页重要性评估证据是否足以支撑过程和议题清单判断，以及缺口颗粒度是否合理。

## 2026-06-30 Stage E3 batch 02 smoke review result

- 已写入 `data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3/smoke_review_result.json`，人工复核状态为 `completed`。
- 阶段门判断：`passed_before_batch_03`。2 条 smoke review 样本均通过，未发现 index-only disclosed、页码偏移错误、证据编造或错误聚合问题。
- 人工结论：`current_gap:GRI3:3-1` 为 `partially_disclosed`，`current_gap:GRI3:3-2` 为 `partially_disclosed`。
- 证据复核：两条均使用 PDF 第 15 页/报告第 14 页“重要性评估”正文证据，证据类型为 `substantive_report_evidence`，页码偏移正确。
- Requirement gap 复核：`3-1:a` 部分支持，`3-1:a:i`、`3-1:a:ii`、`3-1:b` 缺失合理；`3-2:a` 支持，`3-2:b` 缺少较上一报告期变化说明，顶层 `partially_disclosed` 合理。
- 非阻塞问题：`source_text_too_long`。当前 source_text 为整页解析文本，可后续缩短为更精确逐字片段，不影响 batch 02 放行。
- 已写入 `stage_gate_result.json`，gate status 为 `passed_before_batch_03`；已保存 `batch_validation_result_after_smoke_review.json`。
- 验证通过：`py_compile scripts/validate_stage_e3_batch_outputs.py`；`pytest tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-batch02-smoke`，结果 5 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3 --require-smoke-review-result` 为 ok；`validate_stage_e2_1_evidence_contract.py --run-dir data/runs/stage_e/20260630T043746Z_e3_batch_02_gri3_without_3_3` 为 ok。
- 阶段判断：可进入 E3 batch 03 environment；真实调用前仍需用户明确授权发送公开报告证据片段、GRI requirement 数据和 Prompt 到当前配置的 DeepSeek API。

## 2026-06-30 Stage E3 batch 03 environment real run

- 已按用户明确授权执行 E3 第三批 `e3_batch_03_environment` 真实 DeepSeek 运行，发送范围限于公开报告证据片段、GRI requirement 数据和 Prompt。
- 执行前确认 batch 03 范围为 29 条 current_gap 环境披露项：`GRI301=3`、`GRI302=5`、`GRI303=5`、`GRI304=4`、`GRI305=7`、`GRI306=5`。
- 首次完整批次运行 `20260630T045346Z_e3_batch_03_environment` 因 sandbox 网络权限失败，错误为 socket access permission；失败产物保留用于审计。
- 提权后完整批次运行 `20260630T045439Z_e3_batch_03_environment` 成功调用外部模型，但未被采纳：LLM 仅返回 GRI301 的 3 条 assessment，其余 26 条由 guardrail 填充为 `missing_llm_assessment_for_manifest_item`；同时 validator 发现 GRI301 正文 `source_text` 使用省略号概括。
- 为避免单次长批次输出截断，已在同一授权范围内按标准拆分执行 6 个子批次，均通过本地 validator：
  - `20260630T050140Z_e3_batch_03_environment_gri301`
  - `20260630T050653Z_e3_batch_03_environment_gri302`
  - `20260630T051202Z_e3_batch_03_environment_gri303`
  - `20260630T051906Z_e3_batch_03_environment_gri304`
  - `20260630T052325Z_e3_batch_03_environment_gri305`
  - `20260630T052819Z_e3_batch_03_environment_gri306`
- 已生成合并产物 `data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged/`，`run_mode=stage_e3_batch_split_merged`，`sample_count=29`，`assessment_count=29`。
- 合并后 verdict 分布：`not_disclosed=16`、`partially_disclosed=12`、`manual_review=1`；唯一 manual review reason 为 `omission_reason_requires_review`。
- 已补强 E3 validator：允许审计明确的 `stage_e3_batch_split_merged` run mode，同时继续要求普通 batch 与 split merged 均满足 evidence hard gate。
- 已生成 smoke review 模板 `data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged/smoke_review_template.json`，抽样项为 `302-4`、`304-4`、`301-1`、`301-2`、`301-3`。
- 已写入 `stage_gate_result.json`，gate status 为 `pending_smoke_review_before_batch_04`；原始完整批次未采纳，split merged artifact 作为 batch 03 本地验证输入。
- 验证通过：`py_compile scripts/validate_stage_e3_batch_outputs.py`；`pytest tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-batch03-merged`，结果 6 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged` 为 ok；`validate_stage_e2_1_evidence_contract.py --run-dir data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged` 为 ok。
- 阶段判断：E3 batch 03 本地 hard gate 通过，但尚未完成人工 smoke review；进入 batch 04 前必须先复核 5 条 smoke review 样本，重点检查环境项量化数据证据、GRI301 三条的 source_text 逐字性、页码偏移、missing/partial requirement 颗粒度和是否存在 index-only 正向结论。

## 2026-06-30 Stage E3 batch 03 smoke review result

- 已写入 `data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged/smoke_review_result.json`，人工复核状态为 `completed`。
- 阶段门判断：`passed_before_batch_04_with_minor_requirement_granularity_issue`。5 条 smoke review 未发现 index-only positive disclosure、系统性页码偏移、source_text 找不到、AI 编造报告内容或错误正向披露。
- 人工结论：`GRI302:302-4` 为 `partially_disclosed`；`GRI304:304-4` 为 `manual_review`，reason 为 `omission_reason_requires_review`；`GRI301:301-1`、`301-2`、`301-3` 均为 `not_disclosed`。
- 非阻塞小修：`301-2:2.2`、`301-3:2.4` 属于 parent/intro compilation node，不应单独进入 `missing_requirements` hard missing 聚合，应由子项 `2.2.1/2.2.2`、`2.4.1/2.4.2` 参与判断。
- 已生成 corrected artifact，保留 raw LLM artifact 不变：
  - `data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged/analyst_result_corrected.json`
  - `data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged/analysis_run_corrected.json`
- 已更新 `stage_gate_result.json`，gate status 为 `passed_before_batch_04_with_minor_requirement_granularity_issue`，next required action 为 `batch_04_requires_separate_llm_invocation_authorization`。
- 已补强 Analyst guardrail 与 Analyst Prompt：带子项且文本为引导语的 compilation parent/intro node 不参与 hard missing 聚合；已同步 E2.1 evidence validator 的 mandatory coverage 口径。
- 已补强 E3 validator：允许 batch 03 的 `passed_before_batch_04_with_minor_requirement_granularity_issue` smoke gate。
- 阶段判断：batch 03 可以带小修进入 batch 04；batch 04 真实 LLM 调用前仍需用户单独授权发送公开报告证据片段、GRI requirement 数据和 Prompt。

## 2026-06-30 Stage E3 batch 04 employees and human rights real run

- 已按用户明确授权执行 E3 第四批 `e3_batch_04_employees_and_human_rights` 真实 DeepSeek 运行，发送范围限于公开报告证据片段、GRI requirement 数据和 Prompt。
- 执行前确认 batch 04 范围为 32 条 current_gap：`GRI401=3`、`GRI402=1`、`GRI403=10`、`GRI404=3`、`GRI405=2`、`GRI406=1`、`GRI407=1`、`GRI408=1`、`GRI409=1`、`GRI410=1`、`GRI413=2`、`GRI416=2`、`GRI417=3`、`GRI418=1`。
- 真实运行成功，run id 为 `20260630T060615Z_e3_batch_04_employees_and_human_rights`，产物保留于 `data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights/`，`sample_count=32`，`assessment_count=32`，`llm_called=true`。
- Raw artifact 初次 E3 validator 发现 1 个 hard gate 字段问题：`current_gap:GRI404:404-2` 的正文 `source_text` 使用省略号概括，不符合逐字原文要求。
- 已保留 raw LLM artifact 不变，并生成 corrected artifact：`analyst_result_corrected.json` 与 `analysis_run_corrected.json`。
- 字段修正内容：将 `GRI404:404-2` 的 evidence `source_text` 替换为 `p0_report_evidence_index.json` 中 `chunk_f2f3a14a804fb44709d2c946` 对应的 PDF 第 35 页/报告第 34 页逐字短片段，并补充支持 `current_gap:GRI404:404-2:a` 的 evidence binding。
- Corrected verdict 分布：`manual_review=16`、`partially_disclosed=10`、`not_disclosed=6`；manual review reason 分布为 `additional_evidence_needed=14`、`omission_reason_requires_review=2`。
- 已生成 smoke review 模板 `data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights/smoke_review_template.json`，抽样项为 `402-1`、`401-2`、`401-3`、`401-1`、`403-1`。
- 已写入 `stage_gate_result.json`，gate status 为 `pending_smoke_review_before_batch_05`，next required action 为 `complete_human_smoke_review_before_batch_05`。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights` 为 ok，使用 corrected artifact；`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights/analyst_result_corrected.json` 为 ok。
- 阶段判断：E3 batch 04 本地 hard gate 经字段修正后通过，但尚未完成人工 smoke review；进入 batch 05 前必须先复核 5 条 smoke review 样本，重点检查 `manual_review` 是否过度保守、索引指向页是否足够、页码与 source_text 是否一致、以及 `401-1` 与 `403-1` 的 requirement 聚合颗粒度。
- 补充生成 `manual_review_input_corrected.json`，供后续人工总复核使用；raw `manual_review_input.json` 保留不变。

## 2026-06-30 Stage E3 batch 04 smoke review result

- 已写入 `data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights/smoke_review_result.json`，人工复核状态为 `completed`。
- 阶段门判断：`blocked_before_batch_05_required_field_corrections`。5 条 smoke review 未发现系统性页码偏移、source_text 明显造假或 AI 编造报告事实，但发现 `over_manual_review`、`wrong_verdict_aggregation`、`additional_body_evidence_needed`、`evidence_requirement_binding_issue`。
- 已保留 raw LLM artifact 不变，并更新 corrected artifact：`analyst_result_corrected.json`、`analysis_run_corrected.json`、`manual_review_input_corrected.json`。
- `GRI401:401-1`：从 `not_disclosed` 修正为 `partially_disclosed`；补 PDF 第 33 页/报告第 32 页和 PDF 第 65 页/报告第 64 页证据；`401-1:a`、`401-1:b` 改为 `partial_requirements`；`401-1:2.1` 继续不进入 hard missing。
- `GRI401:401-2`：从 `manual_review` 修正为 `partially_disclosed`；补 PDF 第 34 页/报告第 33 页薪酬福利正文证据；缺口保留全职/临时兼职差异、重要运营地点拆分，以及未明确披露的人寿保险、伤残保障、股权等子项。
- `GRI401:401-3`：从 `manual_review` 修正为 `partially_disclosed`；补 PDF 第 34 页/报告第 33 页和 PDF 第 66 页/报告第 65 页育儿假证据；`401-3:a` 与 `401-3:e` 记录为 partial，其余已披露人数类子项绑定证据。
- `GRI402:402-1`：顶层仍为 `partially_disclosed`；补 PDF 第 66 页/报告第 65 页证据，并修正 `402-1:a` 的 `supporting_evidence_ids`；`402-1:b` 仍缺少集体协议说明。
- `GRI403:403-1`：顶层仍为 `partially_disclosed`；保留 PDF 第 38 页/报告第 37 页 EHS 体系证据，补 PDF 第 39 页/报告第 38 页 ISO 45001 管理系统框架证据；`403-1:b` 仍缺少覆盖范围说明。
- Corrected verdict 分布更新为：`partially_disclosed=13`、`manual_review=14`、`not_disclosed=5`；manual review reason 分布为 `additional_evidence_needed=12`、`omission_reason_requires_review=2`。
- 已补强 E3 validator：允许 `blocked_before_batch_05_required_field_corrections` 作为 batch 04 smoke review gate。
- 验证通过：`py_compile scripts/validate_stage_e3_batch_outputs.py`；`pytest tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-batch04-smoke`，结果 8 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights --require-smoke-review-result` 为 ok；`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e/20260630T060615Z_e3_batch_04_employees_and_human_rights/analyst_result_corrected.json` 为 ok。
- 风险记录：`advisor_result.json` 仍是基于 raw analyst 输出生成的建议，未重新调用 LLM 生成 corrected advisor；最终建议链路前需基于 corrected analyst 重新生成或标记 raw advisor 为 stale。
- 阶段判断：batch 04 corrected artifacts 已通过本地复验，但阶段门按人工结论保留 `blocked_before_batch_05_required_field_corrections` 审计状态；进入 batch 05 前需确认接受 corrected artifacts 作为 batch 04 阶段门输入。
- 已确认接受 batch 04 corrected artifacts 作为阶段门输入；`stage_gate_result.json` 保留 `blocked_before_batch_05_required_field_corrections` 审计状态，并记录 `corrected_artifacts_accepted_as_stage_gate_input=true`。

## 2026-06-30 Stage E3 batch 01-04 audit closure before batch 05

- 本次未调用外部 LLM，未重建知识库，未覆盖 raw LLM artifacts，仅补齐阶段门审计字段并复跑本地校验。
- Batch 01：已在 `data/runs/stage_e/20260630T021253Z_e3_batch_01_gri2/stage_gate_result.json` 补充 `corrected_artifacts_accepted_as_stage_gate_input=true`、`effective_gate_status=accepted_after_corrections_before_batch_02`、`validation_status_after_corrections=ok`、`validation_errors_after_corrections=[]`、`accepted_corrected_artifacts`。原始 `gate_status=blocked_before_batch_02` 保留为 smoke review 阻断审计结论。
- Batch 03：已在 `data/runs/stage_e/20260630T053306Z_e3_batch_03_environment_split_merged/run_summary.json` 补充 `validation_status_after_smoke_review=ok`、`validation_errors_after_smoke_review=[]`、`effective_validation_status=ok`、`corrected_artifacts_used_for_stage_gate=true`。原始 `validation_status=failed` 保留为 pre-correction merged artifact 的初始验证记录。
- 复验通过：batch 01、batch 03、batch 04 的 E3 validator 均为 ok，且使用 corrected artifacts；对应 corrected `analyst_result_corrected.json` 的 E2.1 evidence contract validator 均为 ok。
- Batch 05 scope preflight 通过：`e3_batch_05_governance_supply_chain_economic` 共 21 条，覆盖 `GRI201/202/203/204/205/206/207/308/414`，其中 `current_gap:GRI414:414-2` 精确命中。
- `git diff --check` 仅报告 CRLF/LF warning，无 whitespace error。
- 阶段判断：`ready_for_batch05_after_audit_closure`。下一步若执行 batch 05 真实运行，仍需单独授权发送公开报告证据片段、GRI requirement 数据和 Prompt 到当前配置的 DeepSeek API。

## 2026-06-30 Stage E3 batch 05 governance, supply chain and economic real run

- 已按用户明确授权执行 E3 第五批 `e3_batch_05_governance_supply_chain_economic` 真实 DeepSeek 运行，发送范围限于公开报告证据片段、GRI requirement 数据和 Prompt。
- 执行前确认 batch 05 范围为 21 条 current_gap：`GRI201=4`、`GRI202=2`、`GRI203=2`、`GRI204=1`、`GRI205=3`、`GRI206=1`、`GRI207=4`、`GRI308=2`、`GRI414=2`，其中 `current_gap:GRI414:414-2` 精确命中。
- 真实运行成功，run id 为 `20260630T070123Z_e3_batch_05_governance_supply_chain_economic`，产物保留于 `data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/`，`sample_count=21`，`assessment_count=21`，`llm_called=true`。
- Raw artifact 初次 E3 validator 发现 10 个 hard gate 字段问题：`GRI201:201-2`、`GRI201:201-3`、`GRI202:202-1`、`GRI207:207-1`、`GRI207:207-2`、`GRI308:308-1`、`GRI308:308-2`、`GRI414:414-1`、`GRI414:414-2` 的正文 `source_text` 使用省略号概括，不符合逐字原文要求。
- 已保留 raw LLM artifact 不变，并生成 corrected artifact：`analyst_result_corrected.json`、`analysis_run_corrected.json`、`manual_review_input_corrected.json`。
- 字段修正内容：使用 `p0_report_evidence_index.json` 中相同 `chunk_id` 的原始证据文本替换 10 条非逐字 `source_text`；不修改 verdict、不修改 requirement 聚合、不重新调用 LLM。
- Corrected verdict 分布：`manual_review=20`、`partially_disclosed=1`；manual review reason 分布为 `omission_reason_requires_review=5`、`weak_evidence_support=15`、`additional_evidence_needed=15`。
- 已写入 `stage_gate_result.json`，gate status 为 `pending_smoke_review_before_e3_current_scope_acceptance`，next required action 为 `complete_human_smoke_review_before_e3_current_scope_acceptance`。
- 已生成 smoke review 模板 `smoke_review_template.json`，抽样项为 `201-2`、`201-1`、`201-3`、`201-4`、`202-1`。
- 验证通过：`py_compile scripts/apply_stage_e3_batch05_field_corrections.py scripts/validate_stage_e3_batch_outputs.py scripts/validate_stage_e2_1_evidence_contract.py`；`pytest tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-batch05`，结果 8 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic` 为 ok，使用 corrected artifact；`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/analyst_result_corrected.json` 为 ok。
- 阶段判断：batch 05 本地 hard gate 经字段修正后通过，但尚未完成人工 smoke review；E3 当前披露范围全量分批运行结果进入最终接受前，必须复核 5 条 smoke review 样本，重点检查过度 `manual_review`、索引省略理由、正文证据页码、requirement binding 和经济/供应链条款的 false negative 风险。

## 2026-06-30 Stage E3 batch 05 smoke review result

- 已写入 `data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/smoke_review_result.json`，人工复核状态为 `completed`。
- 阶段门判断：`blocked_before_e3_current_scope_acceptance_required_field_corrections`。5 条 smoke review 未发现页码系统性偏移、source_text 造假、AI 编造报告内容或 index-only positive disclosure；主要问题为 `over_manual_review`、`wrong_verdict_aggregation`、`manual_review_to_not_disclosed_required`。
- 已保留 raw LLM artifact 不变，并更新 corrected artifact：`analyst_result_corrected.json`、`analysis_run_corrected.json`、`manual_review_input_corrected.json`。
- `GRI201:201-2`：保持 `partially_disclosed`；PDF 第 17 页/报告第 16 页、PDF 第 18 页/报告第 17 页页码正确；`201-2:2.2` 作为实质 compilation requirement 保持 `missing_requirements`。
- `GRI201:201-1`：保持 `manual_review`，reason 为 `omission_reason_requires_review`；索引写明因商业保密限制从略披露，全文未发现直接经济价值、分配经济价值、留存经济价值等正文数据。
- `GRI201:201-3`：从 `manual_review` 修正为 `not_disclosed`；索引指向“关怀员工，幸福职场”但无省略理由，正文未披露固定福利计划义务、退休计划负债、养老金基金覆盖、缴款比例或参与水平；对应 hard-score requirements 已写入 `missing_requirements`。
- `GRI201:201-4`：保持 `manual_review`，reason 为 `omission_reason_requires_review`；索引写明因商业保密限制从略披露，全文未发现政府财政援助金额、税收减免、补贴、补助、奖励或国家/地区拆分正文数据。
- `GRI202:202-1`：从 `manual_review` 修正为 `not_disclosed`；正文未披露按性别的标准起薪与当地最低工资之比、重要运营地点或定义口径；对应 hard-score requirements 已写入 `missing_requirements`。
- Corrected verdict 分布更新为：`manual_review=18`、`partially_disclosed=1`、`not_disclosed=2`。
- 已补强 E3 validator：允许 `blocked_before_e3_current_scope_acceptance_required_field_corrections` 作为 batch 05 smoke review gate，同时继续执行 evidence hard gate。
- 验证通过：`py_compile scripts/apply_stage_e3_batch05_smoke_corrections.py scripts/apply_stage_e3_batch05_field_corrections.py scripts/validate_stage_e3_batch_outputs.py scripts/validate_stage_e2_1_evidence_contract.py`。
- 验证通过：`pytest tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-batch05-smoke`，结果 9 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic --require-smoke-review-result` 为 ok，使用 corrected artifact；`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/analyst_result_corrected.json` 为 ok。
- 已在 `stage_gate_result.json` 记录 `corrected_artifacts_accepted_as_stage_gate_input=true` 和 `effective_gate_status=accepted_after_corrections_for_e3_current_scope_acceptance`，同时保留原始 smoke review 阻断状态。
- 阶段判断：batch 05 corrected artifacts 可作为 E3 current scope acceptance 的阶段门输入；下一步应做 E3 current scope acceptance audit，汇总 batch01-05 corrected artifacts，并确认普通 current disclosure 分批运行是否整体闭环。

## 2026-06-30 Stage E3 batch 05 corrected Advisor regeneration

- 已按用户明确授权，基于 `analyst_result_corrected.json` 重新调用当前配置的 DeepSeek API 生成 batch 05 corrected Advisor 输出；发送范围限于 batch 05 corrected analyst 结果、公开报告证据片段摘要和 Advisor Prompt。
- 已保留原始 `advisor_result.json` 与 `advisor_raw_llm_output.txt` 不变，并新增：
  - `data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/advisor_result_corrected.json`
  - `data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/advisor_raw_llm_output_corrected.txt`
- Corrected Advisor 生成状态为 `completed`，`p0_recommendations=21`；summary 为 `total_recommendations=21`、`manual_review_recommendations=18`、`high_priority_count=3`。
- 已更新 `run_summary.json`：记录 `advisor_result_corrected_path`、`advisor_raw_llm_output_corrected_path`、`advisor_regenerated_from`、`advisor_corrected_llm_called=true`、`raw_advisor_result_status=superseded_by_advisor_result_corrected`、`validation_status_after_corrected_advisor=ok`。
- 已更新 `stage_gate_result.json`：将 `advisor_result_corrected.json` 加入 corrected artifacts 和 accepted stage gate input files，保留 smoke review 原始阻断状态与修正后有效状态。
- 已补强 E3 validator：当存在 `advisor_result_corrected.json` 时，优先使用 corrected Advisor artifact 进行建议越界短语校验。
- 验证通过：`py_compile scripts/regenerate_stage_e3_corrected_advisor.py scripts/validate_stage_e3_batch_outputs.py`。
- 验证通过：`pytest tests/test_stage_e3_batch_outputs.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-corrected-advisor`，结果 10 passed。
- 验证通过：`validate_stage_e3_batch_outputs.py --run-dir data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic --require-smoke-review-result` 为 ok，且 `advisor_source_file=advisor_result_corrected.json`；`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e/20260630T070123Z_e3_batch_05_governance_supply_chain_economic/analyst_result_corrected.json` 为 ok。
- 阶段判断：batch 05 的 Analyst、AnalysisRun、ManualReviewInput 与 Advisor corrected artifacts 已形成闭环，可纳入 E3 current scope acceptance audit。

## 2026-06-30 Stage E3 current scope acceptance audit

- 已写入 `docs/stage_e3/e3_current_scope_acceptance_result.json`，阶段门状态记录为 `conditionally_passed_for_e3_5_scope`，最终评测状态记录为 `final_evaluation_blocked_pending_traceability_cleanup_and_advisor_regeneration`。
- 已写入 `docs/stage_e3/e3_current_scope_effective_artifacts.json`，固定 batch01-05 的 effective artifacts；raw artifacts 仅作为审计留痕，统计与后续 E3.5 输入应使用 effective artifacts。
- E3 ordinary current disclosure 范围覆盖确认：batch01-05 合计 114 条 ordinary `current_gap`，唯一数 114，无重复；未混入 `current_gap:GRI3:3-3_generic`、`readiness_2026:*`、`watchlist_2027:*`。
- 有效 assessment artifact：batch01 使用 `analyst_result_corrected.json`，batch02 使用 `analyst_result.json`，batch03 使用 `analyst_result_corrected.json`，batch04 使用 `analyst_result_corrected.json`，batch05 使用 `analyst_result_corrected.json`。
- 有效结果分布：`disclosed=2`、`partially_disclosed=42`、`not_disclosed=25`、`manual_review=45`；`review_status=pending` 共 114 条。
- Manual review reason 分布：`additional_evidence_needed=29`、`omission_reason_requires_review=14`、`weak_evidence_support=13`、`index_evidence_cannot_support_disclosed=2`。
- 阶段门判断：允许启动 E3.5 GRI 3-3 topic-level instantiation，但 E3.5 只应依赖 114 条 ordinary `current_gap` 的范围覆盖和当前 assessment 统计。
- 阻断项：最终评测、最终建议链路和论文实验统计暂不放行，需先完成 requirement ID 清洗、evidence binding 统一、PDF evidence 定位修正或人工豁免、以及基于 effective artifacts 的 Advisor 重新生成。
- Advisor 状态：batch05 已有 `advisor_result_corrected.json`；batch01、batch03、batch04 的 advisor 输出仍基于 corrected assessment 前结果，不能进入最终建议；batch02 可作为未修正批次的原始 advisor 参考，但最终建议链路仍建议基于合并 effective assessments 统一生成。

## 2026-06-30 Stage E3.5 GRI 3-3 topic-level instantiation and E3 traceability cleanup

- 已写入 E3.5 计划与范围文件：`docs/stage_e3_5/e3_5_gri_3_3_topic_instantiation_plan.md`、`docs/stage_e3_5/e3_5_gri_3_3_topic_scope.json`、`docs/stage_e3_5/e3_5_gri_3_3_execution_notes.md`。
- 已将 `current_gap:GRI3:3-3_generic` 按远景能源报告实质性议题实例化为 16 个 topic-level assessment，运行包为 `data/runs/stage_e3_5/20260630T083621Z_e3_5_gri3_3_topic_instantiation/`。
- E3.5 本轮未调用外部 LLM；16 条 3-3 topic-level assessment 均为 `manual_review`，requirement 级状态均为 `not_assessed`，`not_scored_reason=pending_e3_5_topic_level_llm_assessment`。该产物只证明 3-3 已从 generic 节点拆成议题级核验单元，不代表 3-3 已完成真实披露核验。
- 已并行生成 E3 traceability cleanup 计划、审计和执行文件：`docs/stage_e3_cleanup/e3_traceability_cleanup_plan.md`、`docs/stage_e3_cleanup/e3_traceability_cleanup_audit.json`、`docs/stage_e3_cleanup/e3_traceability_cleanup_execution_notes.md`。
- 已生成 cleanup 运行包 `data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup/`，包含 `traceability_cleanup_result.json`、`requirement_id_cleanup_map.json`、`evidence_binding_cleanup_map.json`、`pdf_source_text_location_waiver.json`、`run_summary.json`。
- Cleanup 结果：基于 114 条 accepted effective assessments，发现 25 个 unique requirement 引用清洗点、89 个 evidence 绑定清洗点；raw artifacts 和 effective artifacts 均未被修改。
- PDF source_text 定位采用人工豁免包口径：沿用 E3 acceptance audit baseline，159 条正文证据中 PyPDF2 匹配 28 条、未匹配 131 条；不得宣称全量 source_text 已机器定位通过。
- 已准备统一 final advisor 本地输入包 `data/runs/stage_e_final_advisor/20260630T083620Z_e3_unified_final_advisor/merged_effective_analyst_result.json`，合并 114 条 accepted effective ordinary current-gap assessments，未包含 `current_gap:GRI3:3-3_generic`。
- 已写入 `docs/stage_e3/e3_final_advisor_invocation_approval.md`。本轮未调用 DeepSeek；统一 final advisor 生成前仍需用户明确授权发送 114 条合并 effective assessments、公开报告证据片段和 Advisor Prompt。
- 验证通过：`py_compile scripts/build_stage_e3_5_topic_assessments.py scripts/build_stage_e3_traceability_cleanup_artifacts.py scripts/prepare_stage_e3_unified_final_advisor.py tests/test_stage_e3_5_and_cleanup_artifacts.py`。
- 验证通过：`pytest tests/test_stage_e3_5_and_cleanup_artifacts.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-cleanup`，结果 3 passed。
- 验证通过：E3.5 `AnalysisRun.model_validate_json`；cleanup result assessment count 为 114；final advisor input assessment count 为 114 且唯一数为 114。
- `git diff --check` 仅报告既有 CRLF/LF warning，无 whitespace error。

## 2026-06-30 Stage E3.5 GRI 3-3 index-row scope correction

- 已暂停统一 final advisor 真实生成。原因：此前本地输入包仅包含 114 条 ordinary current-gap effective assessments，未纳入 GRI 3-3 展开结果；若现在调用 DeepSeek，只能形成阶段性普通披露项建议，后续仍需重跑。
- 已修正 E3.5 口径：16 条 materiality-topic draft 保留为议题归并和交叉映射参考，最终核验单元采用报告 GRI 索引逐行的 3-3 instances。
- 已写入 `docs/stage_e3_5/e3_5_gri_3_3_index_instance_scope.json`，共 29 条 GRI index-row 3-3 instances。
- 已执行 `scripts/build_stage_e3_5_index_3_3_assessments.py`，生成运行包 `data/runs/stage_e3_5/20260630T084946Z_e3_5_gri3_3_index_instantiation/`。
- 该运行包包含 29 条 `manual_review / not_assessed` 3-3 assessment，占位状态为 `pending_e3_5_index_row_3_3_llm_assessment`，未调用外部 LLM。
- 当前最终 current assessment units 目标口径为 `114 ordinary current_gap + 29 GRI 3-3 instances = 143`。
- 已更新 `docs/stage_e3/e3_final_advisor_invocation_approval.md`，将 114 条 unified final advisor 输入标记为 `stage_only_incomplete_pending_e3_5`，不得作为最终建议授权输入。
- 验证通过：`py_compile scripts/build_stage_e3_5_index_3_3_assessments.py tests/test_stage_e3_5_and_cleanup_artifacts.py`。
- 验证通过：`pytest tests/test_stage_e3_5_and_cleanup_artifacts.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-index-row`，结果 4 passed。

## 2026-06-30 Stage E3.5 GRI 3-3 real LLM run and 143 draft set

- 已按用户明确授权执行 E3.5 GRI 3-3 index-row 真实 DeepSeek 核验，发送范围限于 29 条 3-3 instances、公开报告证据片段、GRI 3-3 requirements、索引页定位和 Analyst Prompt。
- 新增 runner：`scripts/run_stage_e3_5_index_3_3_llm.py`；新增测试：`tests/test_stage_e3_5_index_3_3_runner.py`。
- 运行包：`data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/`，`assessment_count=29`，`llm_called=true`，模型为 `deepseek-v4-flash`。
- 29 条 3-3 原始 LLM verdict 分布：`partially_disclosed=17`、`not_disclosed=6`、`manual_review=6`。
- 初次机器 smoke 发现 18 个硬预警，均为 `source_text_not_verbatim`，未发现结构 validator 错误。
- 已新增并执行 `scripts/apply_stage_e3_5_3_3_source_text_corrections.py`，保留 raw LLM artifact 不变，生成 `analyst_result_merged_corrected.json`、`analysis_run_merged_corrected.json`、`manual_review_input_merged_corrected.json`、`source_text_correction_log.json`、`machine_smoke_review_result_corrected.json`。
- 字段修正结果：`source_text_correction_count=55`；修正后 `validation_status_after_source_text_corrections=ok`，`machine_smoke_hard_issue_count_after_source_text_corrections=0`。
- 已生成 E3.5 smoke review 抽样模板 `data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/smoke_review_template.json`；人工 smoke review 尚未完成，阶段门保持 `pending_human_smoke_review_after_source_text_corrections`。
- 已新增并执行 `scripts/build_stage_e3_final_current_effective_set.py`，生成 143 条 current assessment unit draft：`data/runs/stage_e_final_assessment_set/20260630T091725Z_e3_final_current_effective_set_draft/`。
- 143 条 draft 范围：`114 ordinary current_gap + 29 GRI 3-3 index-row assessments`；verdict 分布为 `partially_disclosed=59`、`not_disclosed=31`、`manual_review=51`、`disclosed=2`。
- 已写入 `docs/stage_e3/e3_final_current_effective_assessment_set_draft.json`，状态为 `draft_pending_e3_5_human_smoke_review`。
- Unified final advisor 真实生成仍阻断，直到 E3.5 人工 smoke review 接受 29 条 3-3 corrected artifact。
- 验证通过：`py_compile scripts/run_stage_e3_5_index_3_3_llm.py tests/test_stage_e3_5_index_3_3_runner.py scripts/apply_stage_e3_5_3_3_source_text_corrections.py scripts/build_stage_e3_final_current_effective_set.py`。
- 验证通过：`pytest tests/test_stage_e3_5_index_3_3_runner.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-3-3-runner`，结果 2 passed。
- 验证通过：`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/analyst_result_merged_corrected.json`，状态 ok。
- 验证通过：`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e_final_assessment_set/20260630T091725Z_e3_final_current_effective_set_draft/final_current_effective_assessment_set_draft.json`，状态 ok。
- 验证通过：143 条 `analysis_run_draft.json` 通过 `AnalysisRun.model_validate_json`；`git diff --check` 仅报告既有 CRLF/LF warning，无 whitespace error。

## 2026-06-30 Stage E3.5 GRI 3-3 smoke review corrections

- 已写入 E3.5 人工 smoke review 结果：`data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/smoke_review_result.json`。
- 人工 smoke review 原始阶段门：`blocked_required_field_corrections_before_acceptance`；复核 7 条，证据页码检查均为 ok，阻断问题集中在 requirement-level aggregation 与 evidence binding。
- 已新增并执行 `scripts/apply_stage_e3_5_3_3_smoke_review_corrections.py`，保留 raw 与 corrected artifacts 不变，新增 reviewed artifacts：`analyst_result_merged_reviewed.json`、`analysis_run_merged_reviewed.json`、`manual_review_input_merged_reviewed.json`。
- 修正内容：`GRI303:3-3` 与 `GRI401:3-3` 从 `manual_review` 修正为 `partially_disclosed`；`GRI301:3-3` 的 3-3:e:ii 调整为 `partially_met`；`GRI414:3-3` 的 3-3:e:ii、3-3:e:iii 调整为 `partially_met` 并补充供应商绩效表证据。
- 29 条 3-3 reviewed verdict 分布：`partially_disclosed=19`、`not_disclosed=6`、`manual_review=4`。
- E3.5 stage gate 已更新为 `reviewed_field_corrections_applied_pending_acceptance`；`validation_status_after_human_smoke_review_corrections=ok`，`machine_smoke_hard_issue_count_after_human_smoke_review_corrections=0`。
- 已按 reviewed 3-3 artifacts 重建 143 条 current assessment unit draft：`data/runs/stage_e_final_assessment_set/20260630T112719Z_e3_final_current_effective_set_draft/`。
- 新 143 条 draft verdict 分布：`partially_disclosed=61`、`not_disclosed=31`、`manual_review=49`、`disclosed=2`。
- 已更新 `docs/stage_e3/e3_final_current_effective_assessment_set_draft.json`，指向最新 143 条 reviewed draft set。
- 验证通过：`py_compile scripts/apply_stage_e3_5_3_3_smoke_review_corrections.py scripts/build_stage_e3_final_current_effective_set.py`。
- 验证通过：`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/analyst_result_merged_reviewed.json`，状态 ok。
- 验证通过：`validate_stage_e2_1_evidence_contract.py --assessment-file data/runs/stage_e_final_assessment_set/20260630T112719Z_e3_final_current_effective_set_draft/final_current_effective_assessment_set_draft.json`，状态 ok。
- 验证通过：`analysis_run_merged_reviewed.json` 为 29 条，最新 143 条 `analysis_run_draft.json` 为 143 条且不含 `current_gap:GRI3:3-3_generic`。
- 下一步阶段门建议：明确接受 reviewed 3-3 artifacts 作为 E3.5 effective input 后，再准备 143 条 unified final advisor 调用授权。

## 2026-06-30 Stage E3.5 effective acceptance and 143-item unified final Advisor

- 已按用户授权将 E3.5 `reviewed_field_corrections_applied_pending_acceptance` 追认为 effective input；`stage_gate_result.json` 当前 `gate_status=accepted_after_human_smoke_review_field_corrections`，并保留 `pre_effective_acceptance_gate_status=reviewed_field_corrections_applied_pending_acceptance`。
- 新增脚本：`scripts/accept_stage_e3_5_and_final_current_set.py`、`scripts/run_stage_e3_143_unified_final_advisor.py`、`scripts/apply_stage_e3_143_advisor_summary_correction.py`；新增测试：`tests/test_stage_e3_143_final_advisor.py`。
- 已生成 143 条 accepted current assessment set：`data/runs/stage_e_final_assessment_set/20260630T113930Z_e3_final_current_effective_set_accepted/final_current_effective_assessment_set.json`。
- accepted set 范围：`114 ordinary current_gap + 29 GRI 3-3 index-row assessments = 143`；verdict 分布为 `partially_disclosed=61`、`not_disclosed=31`、`manual_review=49`、`disclosed=2`。
- 已更新 `docs/stage_e3/e3_final_current_effective_assessment_set.json`，状态为 `accepted_effective_input_for_unified_final_advisor`。
- 已按用户授权执行 143 条 unified final Advisor 真实 DeepSeek 调用；发送范围限于 accepted assessment 的精简 Advisor 输入、requirement checks、evidence kinds 和 Advisor Prompt，未发送 `.env`、密钥、原始 PDF 或非公开内部数据。
- Advisor 运行包：`data/runs/stage_e_final_advisor/20260630T114005Z_e3_143_unified_final_advisor/`；raw 输出为 `final_advisor_result.json`，effective 输出为 `final_advisor_result_corrected.json`。
- Advisor raw 输出的建议主体校验通过，但 `summary.total_recommendations` 与实际建议条数不一致；已保留 raw 输出并生成 corrected artifact，仅按 `p0_recommendations` 重算 summary 计数字段。
- effective Advisor 输出建议数：141；`advisor_validation_result_corrected.json` 状态为 ok，errors 与 warnings 均为空。
- 已更新 `docs/stage_e3/e3_final_advisor_invocation_approval.md`，记录 143 条真实调用、accepted set、effective Advisor 输出和 corrected validation 状态。
- 验证通过：`py_compile scripts/accept_stage_e3_5_and_final_current_set.py scripts/run_stage_e3_143_unified_final_advisor.py scripts/apply_stage_e3_143_advisor_summary_correction.py tests/test_stage_e3_143_final_advisor.py`。
- 验证通过：`pytest tests/test_stage_e3_143_final_advisor.py tests/test_stage_e3_5_and_cleanup_artifacts.py tests/test_stage_e3_5_index_3_3_runner.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-final-advisor`，结果 9 passed。
- 验证通过：E3.5 reviewed 29 条与 143 条 accepted set 的 `validate_stage_e2_1_evidence_contract.py` 均为 ok。
- 验证通过：`analysis_run_merged_reviewed.json` 为 29 条唯一 assessment，143 条 accepted `analysis_run.json` 为 143 条唯一 assessment，均不含 `current_gap:GRI3:3-3_generic`。
- `git diff --check` 仅报告既有 CRLF/LF warning，无 whitespace error。
- 阶段判断：E3.5 reviewed artifacts 已成为 effective input，143 条 final current effective assessment set 与 unified final Advisor 运行已形成审计闭环；后续仍需对 final Advisor 建议进行人工评测，不应直接当作未经复核的最终论文结论。

## 2026-06-30 Stage E3 traceability cleanup acceptance gate

- 已按人工阶段门建议接受 traceability cleanup 结果，状态记录为 `traceability_cleanup_accepted_with_explicit_waivers_for_f_evaluation`，不写成 clean accepted。
- 新增阶段门文件：`docs/stage_e3_cleanup/e3_traceability_cleanup_acceptance_gate.json`；同时写入 cleanup 运行包：`data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup/stage_gate_acceptance_result.json`。
- 阶段门结论：`must_fix=[]`；143 条 accepted current assessment set 可进入 F0 evaluation preparation；`final_advisor_result_corrected.json` 可进入 Advisor usefulness review 准备；traceability cleanup maps 可作为 F0/后续 F 阶段 effective metric mapping 输入。
- 明确豁免：requirement-level metrics 必须使用 `requirement_id_cleanup_map.json`；E4 持久化/Streamlit 前必须用 `evidence_binding_cleanup_map.json` 统一到 `evidence_id`；PDF `source_text` 机器匹配限制以人工豁免记录，不能宣称全部证据原文均机器定位验证通过。
- 口径限制：cleanup 包原始范围为 114 条 ordinary E3 assessments；143 条 final set 进入 F0/后续 F 统计时，普通 E3 requirement-level 统计使用 cleanup maps，29 条 E3.5 reviewed 3-3 assessments 使用其已验证 accepted artifacts，除非后续发现单独 traceability 问题。
- 下一步入口：可启动 F0 人工评测准备；E4 持久化、API 与 Streamlit 工作台仍是 P0 完整闭环前置任务，E4 前再做 evidence_id 绑定规范化和展示层 traceability 统一。

## 2026-06-30 Stage F0 human evaluation package

- 已生成 F0 人工评测运行包：`data/runs/stage_f/20260630T132346Z_f_human_evaluation_package/`。
- 输出 workbook：`f_human_evaluation_workbook.xlsx`，包含 `README`、`1_assessment_review`、`2_advisor_review`、`3_requirement_sample`、`error_taxonomy` 五个 sheet。
- 同步输出 CSV/JSON 备份：`assessment_review_sheet.csv/json`、`advisor_review_sheet.csv/json`、`requirement_review_sample.csv/json`、`error_taxonomy.json`、`f_evaluation_scope_manifest.json`、`run_summary.json`。
- `assessment_review_sheet` 覆盖 143 条 final assessments，人工填写字段全部留空。
- `advisor_review_sheet` 覆盖 141 条 final Advisor corrected 建议，并补 2 条 `disclosed/no_action` coverage rows，总计 143 行，人工填写字段全部留空。
- `requirement_review_sample` 采用确定性分层抽样，样本数 140 条；抽样按 assessment verdict 与 requirement support status 分层，并强制纳入 `requirement_id_cleanup_map.json` 命中的 requirement 引用。
- Workbook 和备份保留 AI verdict、rationale、aggregation reason、missing/partial/manual_review requirements、manual_review reason、证据页码、evidence_id/chunk_id、source_text preview、requirement IDs、Advisor recommendation text、cleanup notes 和 PDF machine-match waiver note。
- 本阶段不计算指标，不填 human verdict，不调用 LLM；等待人工填写 workbook 后再进入后续指标计算。
- 验证通过：输出目录包含用户要求的 10 个文件；CSV/JSON 行数为 assessment=143、advisor=143、requirement_sample=140。
- 验证通过：使用 `@oai/artifact-tool` 重新导入 workbook，确认 5 个 sheet 存在；关键范围可读；公式错误扫描 0 命中；5 个 sheet 均完成 render 检查。
- 阶段判断：F0 人工评测包已准备好；E4 持久化、API 与 Streamlit 工作台仍未完成，不能写成完整 F 阶段或 P0 产品闭环。

## 2026-06-30 Stage E4 pending-review workbench plan

- 已写入 E4 执行计划：`docs/superpowers/plans/2026-06-30-p0-stage-e4-pending-review-workbench.md`。
- E4 目标：基于 143 条 accepted current assessments 与 143 条 Advisor coverage 建设 pending-review 状态下的 AnalysisRun 持久化、API、Streamlit 条款级查看、人工复核录入和导出功能。
- E4 状态口径：所有接入页面和导出的 Stage E 数据必须保持 `review_status=pending`、`final_evaluation_status=pending_human_evaluation`；Advisor 仅标注为 AI-assisted recommendation pending human review。
- 已同步生命周期计划 9.1/9.3：F0 人工评测包可由人工并行填写，主流程下一步进入 E4；完整 F 指标计算等待 E4 产品闭环和人工评测结果回传后执行。
- 本次仅写入计划与文档状态，不修改业务代码、不调用 LLM、不计算 F 阶段指标。

## 2026-06-30 Stage E4 Task 1-3 persistence, seed and API

- 已完成 E4 Task 1-3：新增 pending-review SQLite 持久化层、Stage E accepted artifacts seed 脚本和 P0 review API。
- 新增 `src/storage/p0_review_store.py` 与 `src/storage/__init__.py`：支持 `p0_review_runs`、`p0_assessments`、`p0_advisor_items`、`p0_review_decisions` 四张表，写入时强制 `review_status=pending`、`final_evaluation_status=pending_human_evaluation`、`recommendation_status=ai_assisted_pending_human_review`。
- 新增 `scripts/seed_stage_e4_pending_review.py`：从 143 条 accepted assessment set、`analysis_run.json`、141 条 corrected Advisor 建议、F0 `advisor_review_sheet.json` 和 traceability cleanup maps 构造 E4 seed payload。
- Advisor coverage 已补齐为 143 条：141 条真实 Advisor corrected 建议，加 `current_gap:GRI2:2-22`、`current_gap:GRI2:2-29` 两条 disclosed/no-action coverage。
- 已执行真实 seed，写入本地 SQLite pending-review 数据，并生成 summary：`data/runs/stage_e4/20260630T144314Z_e4_pending_review_seed/seed_summary.json`。
- Seed 结果：assessment=143，advisor coverage=143；verdict 分布为 `partially_disclosed=61`、`not_disclosed=31`、`manual_review=49`、`disclosed=2`；Advisor recommendation status 全部为 `ai_assisted_pending_human_review`。
- 新增 `src/api/p0_review_router.py` 并注册到 `src/api/router.py` 的 `/p0-review`：支持 runs、summary、assessments、advisor-items、review-decisions 和三类 CSV export endpoint。
- API summary 仅返回 pending-review 统计，不输出 `accuracy`、`precision`、`recall`、`terminal_accuracy_metric`、`human_verified_count`、`confirmed_recommendation_count` 等 F 阶段指标。
- 新增测试：`tests/test_stage_e4_p0_review_store.py`、`tests/test_stage_e4_seed_pending_review.py`、`tests/test_stage_e4_p0_review_api.py`。
- RED 验证：store 测试最初因 `src.storage` 缺失失败；seed 测试最初因 `scripts.seed_stage_e4_pending_review` 缺失失败；API 测试最初因 `src.api.p0_review_router` 缺失失败。
- GREEN 验证通过：`pytest tests/test_stage_e4_p0_review_store.py tests/test_stage_e4_seed_pending_review.py tests/test_stage_e4_p0_review_api.py -q -p no:cacheprovider --basetemp tmp/pytest-e4-task1-3`，结果 12 passed。
- 验证通过：`py_compile src/storage/p0_review_store.py scripts/seed_stage_e4_pending_review.py src/api/p0_review_router.py src/api/router.py`。
- 本阶段未调用 LLM，未修改 Stage E accepted artifacts，未计算 F 阶段指标。下一步进入 E4 Task 4-5：Streamlit P0 review workbench 和导出服务完善。

## 2026-06-30 Stage E4 Task 4-5 Streamlit workbench and export service

- 已完成 E4 Task 4-5：新增 Streamlit P0 条款级复核工作台，并完善 assessment、Advisor 和 review decision 的 CSV/JSON 导出服务。
- 新增 `src/services/p0_review_export.py` 与 `src/services/__init__.py`：从 `P0ReviewStore` 构造导出行，保留 AI 原始字段、人工复核字段、requirement IDs、evidence IDs、chunk IDs、source pages、report page labels、pending 状态和 recommendation status；不计算 F 阶段指标。
- 已更新 `src/api/p0_review_router.py`：CSV 导出端点改用导出服务，并新增 JSON 导出端点：
  - `/p0-review/runs/{run_id}/exports/assessments.json`
  - `/p0-review/runs/{run_id}/exports/advisor-items.json`
  - `/p0-review/runs/{run_id}/exports/review-decisions.json`
- 新增 Streamlit 页面 `src/ui/pages/09_p0_review_workbench.py`，并在 `src/ui/app.py` 注册为 `P0条款复核` 页面。
- 页面能力：选择 E4 run、查看 143 条 assessment、查看 evidence 与 requirement checks、查看对应 Advisor coverage、保存人工复核记录、下载 assessment/advisor/review decisions 的 CSV/JSON。
- 页面状态口径：显示 `final_evaluation_status=pending_human_evaluation` 和 `AI-assisted recommendation pending human review`；不展示最终评测指标或最终确认类结论。
- 已通过 API smoke 写入一条本地测试复核记录：`review_decision_id=review_89f1b70556dd1981`，`source=e4_task4_smoke`；该记录仅用于 E4 页面保存链路验证，不代表 F 阶段人工评测结论。
- 新增测试：`tests/test_stage_e4_p0_review_export.py`、`tests/test_stage_e4_streamlit_workbench_static.py`。
- RED 验证：导出测试最初因 `src.services` 缺失失败；Streamlit 静态测试最初因 `09_p0_review_workbench.py` 缺失失败。
- GREEN 验证通过：`pytest tests/test_stage_e4_p0_review_store.py tests/test_stage_e4_seed_pending_review.py tests/test_stage_e4_p0_review_api.py tests/test_stage_e4_p0_review_export.py tests/test_stage_e4_streamlit_workbench_static.py -q -p no:cacheprovider --basetemp tmp/pytest-e4-task1-5`，结果 16 passed。
- 验证通过：`py_compile src/storage/p0_review_store.py scripts/seed_stage_e4_pending_review.py src/services/p0_review_export.py src/api/p0_review_router.py src/api/router.py src/ui/pages/09_p0_review_workbench.py src/ui/app.py`。
- 本地服务 smoke 通过：FastAPI `http://127.0.0.1:8010`，Streamlit `http://127.0.0.1:8510`；API summary 返回 assessment=143、advisor coverage=143、`final_evaluation_status=pending_human_evaluation`；assessment JSON export 返回 200。
- `git diff --check` 仅报告既有 CRLF/LF warning，无 whitespace error。
- 本阶段未调用 LLM，未修改 Stage E accepted artifacts，未计算 F 阶段指标。下一步进入 E4 Task 6-8：F 人工评测导入入口、文档同步和 E4 端到端验收。

## 2026-06-30 Stage E4 Task 6-8 F import, docs and end-to-end closure

- 已完成 E4 Task 6：新增 `scripts/import_f_human_review_results.py`，支持导入 F workbook 对应的 CSV/JSON 复核行。
- 导入脚本会校验 `manifest_item_id`、`assessment_id` 或 `advisor_item_id` 是否能匹配 E4 pending-review 数据；未知 row key 会被拒绝并返回错误清单。
- 导入结果只写入 `p0_review_decisions`，导入来源为 `source=f_human_evaluation_import`；AI 原始 assessment 和 Advisor 原始建议保持不可变。
- 新增测试：`tests/test_stage_e4_import_f_review_results.py`。RED 验证最初因 `scripts.import_f_human_review_results` 缺失失败；GREEN 验证通过，覆盖 JSON 导入、CSV 未知 key 拒绝、重复导入和 AI 原始字段不变。
- 已完成 E4 Task 7 文档同步：生命周期计划标记 E4 pending-review 工作台完成；模型说明文档补充 E4 持久化 schema、状态语义、`/p0-review` API 和 Streamlit 页面；用户操作手册新增 P0条款复核页面操作说明。
- E4 状态边界继续保持：`review_status=pending`、`final_evaluation_status=pending_human_evaluation`、Advisor 状态为 AI-assisted recommendation pending human review；F 阶段指标等待人工 workbook 回传后计算。
- E4 Task 8 端到端验证已执行：E4 tests、seed、FastAPI、Streamlit、summary、导出和 review decision 保存链路均通过。
- 最终 E4 验证通过：`pytest tests/test_stage_e4_p0_review_store.py tests/test_stage_e4_seed_pending_review.py tests/test_stage_e4_p0_review_api.py tests/test_stage_e4_p0_review_export.py tests/test_stage_e4_import_f_review_results.py tests/test_stage_e4_streamlit_workbench_static.py -q -p no:cacheprovider --basetemp tmp/pytest-e4-task1-8`，结果 19 passed。
- 最终 seed 验证通过：`scripts/seed_stage_e4_pending_review.py` 生成 `data/runs/stage_e4/20260630T150827Z_e4_pending_review_seed/seed_summary.json`。
- 本地服务 smoke 通过：FastAPI `http://127.0.0.1:8010` 返回 assessment=143、advisor coverage=143、`final_evaluation_status=pending_human_evaluation`；Streamlit `http://127.0.0.1:8510` 返回 200；review decisions JSON export 返回 200。
- 禁用完成态表述扫描通过：`rg "终局准确性指标|人工评测完成|终局建议确认|terminal_accuracy_metric" src docs/项目模型说明文档.md docs/用户操作手册.md` 无命中。
- 本阶段未调用 LLM，未修改 Stage E accepted artifacts，未计算 F 阶段指标。

## 2026-06-30 Stage E4 fixed-report artifact-backed E2E smoke

- 已执行 P0 fixed-report artifact-backed E2E workflow smoke，不重跑 143 条 LLM，不计算终局准确性指标，不宣称人工评测完成，不生成论文最终指标。
- Smoke 范围：143 条 accepted current assessments、143 条 Advisor coverage、E4 SQLite/API/Streamlit pending-review 工作台。
- 结果文件：`data/runs/stage_e4/20260630T152020Z_e4_fixed_report_e2e_smoke/e2e_smoke_result.json`。
- API smoke 通过：FastAPI `http://127.0.0.1:8010` 返回 assessment=143、advisor coverage=143、`final_evaluation_status=pending_human_evaluation`。
- Assessment detail smoke 通过：通过 API 打开 `current_gap:GRI201:201-1` detail，确认存在 requirement checks、evidence、`source_page`、`report_page_label` 和 `source_text`。
- 人工复核保存链路通过：写入测试记录 `review_decision_id=review_5b7c5255b33e05fb`，`reviewer=e4_smoke_test`，`source=e4_manual_smoke`，comment 为 `E4 smoke test record; not final human evaluation`。
- 导出 smoke 通过：assessment/advisor/review decisions JSON export 均返回 200；导出内容未命中最终指标、人工验证完成、最终建议确认或 completion status 类表述。
- Streamlit 入口 smoke 通过：`http://127.0.0.1:8510` 返回 200。Playwright MCP 可打开页面，但 snapshot 仅捕获 Streamlit banner；页面内容验证由静态页面测试、API detail 检查和导出检查覆盖。
- 阶段状态记录为 `P0 fixed-report artifact-backed E2E workflow smoke passed`。
- 限制继续保留：`final_evaluation_status=pending_human_evaluation`；F metrics pending human-filled workbook；P0 final evaluation not completed。

## 2026-07-01 Stage F human evaluation inputs archived

- 已读取桌面三份人工评测 workbook：`staff.xlsx`、`professor.xlsx`、`member.xlsx`，并归档到 `data/runs/stage_f/20260701T030010Z_f_human_evaluation_completed/`。
- 每份 workbook 均包含三张评测表：assessment 143 行、advisor 143 行、requirement sample 140 行；三类表均与 F0 基准 key 完整匹配，缺失 key=0，额外 key=0。
- 已保留原始 workbook 副本到 `source_workbooks/`，并生成每位评测人的 CSV/JSON 备份。
- 已生成 `f_human_evaluation_input_manifest.json`、`f_human_evaluation_acceptance_result.json` 和 `run_summary.json`，状态为 `accepted_as_f_human_evaluation_inputs`。
- 首次不完整归档目录 `data/runs/stage_f/20260701T025932Z_f_human_evaluation_completed/` 已写入 `superseded_by.json`，正式后续使用 `20260701T030010Z_f_human_evaluation_completed`。
- 本步骤未调用 LLM，未修改 Stage E accepted artifacts，未导入 E4 SQLite，未计算 F 阶段指标。

## 2026-07-01 Stage F human evaluation import, metrics and error analysis

- 已将 `data/runs/stage_f/20260701T030010Z_f_human_evaluation_completed/` 中三位评测人的完成表导入 E4 SQLite：assessment 429 条、advisor 429 条、requirement sample 420 条，总计 1278 条 review decision，导入错误 0。
- 新增执行脚本：`scripts/import_and_compute_stage_f_human_evaluation.py`，按三位评测人分别入库，并按多数表决计算 F 阶段指标。
- 指标输出目录：`data/runs/stage_f/20260701T030541Z_f_metrics_and_error_analysis/`。
- 主要结果：assessment 多数表决准确率 0.9790，macro F1 0.9806；Advisor accepted 或 minor_revision 比率 1.0000；requirement 抽样支持状态准确率 1.0000。
- 主要误差归因：assessment 侧包括 additional_body_evidence_needed、omission_reason_handling_error、over_manual_review、index_only_positive_risk、wrong_verdict_aggregation；Advisor 侧主要为 advisor_internal_data_flag_error 和 advisor_not_actionable；requirement 侧主要为 traceability_mapping_required。
- 输出文件包括 `f_metrics_summary.json`、`f_error_analysis.json`、`f_consensus_review_rows.json`、三张 consensus CSV、`f_metrics_and_error_analysis_report.md`、`run_summary.json`。
- 本步骤未调用 LLM，未修改 Stage E accepted artifacts；requirement 指标基于 140 条抽样表，不代表全量 requirement object 指标。

## 2026-07-01 P0 project closure final smoke

- 已写入中文计划文件：`docs/superpowers/plans/2026-07-01-p0-project-closure-and-final-smoke.md`。
- 已执行 P0 fixed-report artifact-backed 项目闭环最终验收 smoke，输出目录：`data/runs/stage_e4/20260701T032000Z_p0_project_closure_final_smoke/`。
- 验收结果：`p0_project_closure_final_smoke_passed`，`all_required_checks_ok=true`。
- API 行为通过 FastAPI TestClient 验证：summary 返回 assessment=143、advisor coverage=143、`review_status=pending`、`final_evaluation_status=pending_human_evaluation`。
- Assessment detail 验证通过：存在 requirement checks、evidence、`source_page`、`report_page_label` 和 `source_text`。
- 复核保存链路通过：写入 smoke 记录 `review_decision_id=review_a4fc7ade5241c597`，`source=p0_project_closure_smoke`；该记录仅用于产品闭环 smoke，不代表 F 阶段人工评测结论。
- 导出链路通过：assessment/advisor/review decisions 的 CSV/JSON 导出接口均返回 200 且内容非空。
- Streamlit 入口 smoke 通过：8510 端口因 Windows socket 权限被拒，自动切换到 8521，HTTP 返回 200；工作台静态契约标记检查通过。
- 限制：当前项目 Python 环境缺少 `uvicorn`，因此 API 未以 live uvicorn server 方式启动；API router 和 SQLite store 行为已通过 TestClient 验证。F 阶段人工评测数据和指标保留归档，不作为本轮产品闭环完成条件。
- 首次失败 smoke 目录 `data/runs/stage_e4/20260701T031859Z_p0_project_closure_final_smoke/` 已写入 `superseded_by.json`，后续使用 `20260701T032000Z_p0_project_closure_final_smoke`。

## 2026-07-01 P0 delivery docs and runtime closure

- 已同步项目交付口径：P0 fixed-report artifact-backed workflow completed；F 阶段人工评测数据和指标产物归档保留，不作为当前产品闭环验收条件。
- 已更新生命周期计划、项目模型说明文档和用户操作手册，下一步入口调整为阶段 G：交付包、演示脚本、录屏和求职材料转化。
- 已处理运行环境缺口：`pyproject.toml` 声明 `uvicorn[standard]`，但当前项目专用 Python 环境无写权限且缺少可导入的 `uvicorn`/`anyio` 包体；直接写入环境目录被 Windows 权限拒绝。
- 已将 API 启动所需依赖安装到项目内 `vendor/python_runtime/`，并修正 ACL；`src/main.py`、`scripts/run_api.py` 和 `sitecustomize.py` 会优先加载该 runtime 目录。
- 新增 `scripts/run_api.py`，用户手册后端启动命令更新为 `python scripts/run_api.py`。
- 已执行 live FastAPI smoke，输出目录：`data/runs/stage_e4/20260701T034420Z_p0_delivery_live_api_smoke/`；`/health` 返回 200，`/api/v1/p0-review/runs/20260630T113930Z_e3_final_current_effective_set_accepted/summary` 返回 assessment=143、advisor coverage=143、`final_evaluation_status=pending_human_evaluation`。
- 本步骤未调用 LLM，未修改 Stage E/F accepted artifacts。

## 2026-07-01 Delivery document and stale artifact cleanup

- 已重写 `docs/部署说明文档.md` 和 `docs/FAQ.md`，统一为当前 P0 fixed-report artifact-backed review workbench 口径：后端启动使用 `python scripts/run_api.py`，E4 工作台显示 143 条 assessments 和 143 条 Advisor coverage，状态保持 `pending_human_evaluation`。
- 已删除 `.playwright-mcp/` 浏览器状态目录，该目录不属于 P0 产品交付物。
- 已接受旧导出模板删除：`templates/export_templates/analysis_template.xlsx` 与 `templates/export_templates/word_template.docx`；当前 E4 导出链路使用 CSV/JSON 服务，不依赖旧 Excel/Word 模板。
- 已清理两个明确 superseded 的运行目录：`data/runs/stage_e4/20260701T031859Z_p0_project_closure_final_smoke/` 和 `data/runs/stage_f/20260701T025932Z_f_human_evaluation_completed/`。
- 保留当前 accepted artifacts、E4 SQLite、`data/knowledge_base/`、正式 Stage F 归档目录和 `vendor/python_runtime/`。
- 本步骤未调用 LLM，未修改 Stage E accepted current assessment set 或 final Advisor corrected 输出。

## 2026-07-01 P0 delivery cleanup: legacy UI and script archive

- 已删除本地编辑器目录 `.vscode/`、空目录 `data/export_results/` 和空目录 `templates/export_templates/`。
- 已移除 legacy Streamlit 页面 `03_materiality.py`、`04_analysis.py`、`05_review.py`、`06_benchmarking.py`、`08_rules.py`；当前 P0 导航只保留首页概览、报告上传、P0 条款复核和审计日志。
- 已从 `src/config/paths.py` 与 `src/config/__init__.py` 移除 `EXPORT_TEMPLATES_DIR`，当前导出链路不依赖旧 Excel/Word 模板目录。
- 已将 7 个一次性 Stage E 字段修正脚本移动到 `scripts/archive_stage_e/`，保留复现能力，同时减少主 `scripts/` 目录噪音。
- 已更新 `docs/用户操作手册.md`、`docs/项目模型说明文档.md`、`README.md` 和 Streamlit 静态测试，明确 legacy 页面已从 P0 交付中移除。
- 本步骤未调用 LLM，未修改 Stage E accepted artifacts、final Advisor corrected 输出或 E4 SQLite 数据。

## 2026-07-01 P0 delivery cleanup: home page and Stage E script archive

- 已删除空旧库 `data/sqlite_db/review_records.db`；当前 P0 工作台使用 `data/sqlite_db/esg_system.db`，审计日志使用 `data/sqlite_db/audit_log.db`。
- 已更新 Streamlit 首页旧静态文案，移除“120+ 语料库”“ISSB/SASB/HKEX”“上传-识别-差距-建议”等旧 MVP 展示口径，改为当前 P0 fixed-report、143 条 assessment、143 条 Advisor coverage 和 pending human review 状态。
- 已将 Stage E/E3/E3.5 历史构建、真实运行、接受和 final Advisor 生成脚本移动到 `scripts/archive_stage_e/`；主 `scripts/` 保留 API 启动、E4 seed、F 导入/计算、通用校验和 P0 基础构建脚本。
- 已同步修正归档脚本与历史测试的 import 路径，保留阶段复现能力。
- 本步骤未调用 LLM，未修改 Stage E accepted artifacts、final Advisor corrected 输出或 E4 SQLite 当前 P0 数据。
