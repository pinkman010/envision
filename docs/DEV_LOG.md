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
- 阶段判断：现在仍不直接跑 E3；下一步是在用户明确授权后执行 E3 第一批 `e3_batch_01_gri2` 的真实运行。
