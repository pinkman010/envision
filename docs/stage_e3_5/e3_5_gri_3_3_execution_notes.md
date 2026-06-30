# E3.5 GRI 3-3 Execution Notes

## 执行边界

本节点只负责 GRI 3-3 topic-level instantiation 方案与数据草案。未修改 traceability cleanup 文件，未修改原始 PDF，未覆盖 raw artifacts，未调用外部 LLM。

`current_gap:GRI3:3-3_generic` 不进入普通评分。E3.5 的执行对象是 16 个 topic instances，后续评估应按 topic 逐项判断管理披露是否覆盖 GRI 3-3 要求。

## 已读取输入

- `AGENTS.md`
- `docs/stage_e3/e3_current_scope_acceptance_result.json`
- `docs/stage_e3/e3_current_scope_effective_artifacts.json`
- `data/knowledge_base/manifests/p0_report_evidence_index.json`
- `data/knowledge_base/manifests/p0_gri_requirement_checklist.json`

## 本地证据检索结果

自动检索命中“重要性”“议题”“利益相关方”“ESG战略”等线索。主证据为：

- `pdf_page=15`
- `report_page_label=14`
- `source_chunk_id=chunk_e5d997720034f27d8de684b9`
- 证据含义：报告说明通过政策法规解析、ESG 标准研究、利益相关方调研及双因素矩阵分析识别 16 项 ESG 重要性议题，并给出重要性矩阵。

交叉验证证据为：

- `pdf_page=11`
- `report_page_label=10`
- `source_chunk_id=chunk_a168baace8b3681e8e04d70e`
- 证据含义：ESG 战略与目标页按环境、人、治理、产品列示重要性议题及目标。

## 可执行步骤

1. 使用 `docs/stage_e3_5/e3_5_gri_3_3_topic_scope.json` 作为 topic-level batch 输入草案。
2. 为每个 `topic_instance_id` 派生 GRI 3-3 assessment item，保留原字段并追加运行字段：`run_id`、`assessment_mode`、`canonical_disclosure_id=3-3`、`topic_instance_id`、`evidence[]`、`review_status`。
3. DeepSeek 授权后，逐 topic 检索该议题对应章节证据，判断 GRI 3-3 管理披露要求，输出 topic-level assessment。
4. 所有无充分报告证据的判断进入 `manualReview`，不得补造企业披露事实。
5. E3.5 assessment 输出完成后，进入人工复核；通过后再由主流程决定是否纳入最终统计。

## 禁止事项

- 不覆盖 `data/runs/stage_e/**` 的 raw artifacts。
- 不修改 `data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf`。
- 不改 traceability cleanup 相关文件。
- 不把静态草案写成已完成 3-3 核验。
- 不在 DeepSeek 授权前调用外部模型。

## 2026-06-30 主流程执行记录

已由主流程执行 `scripts/build_stage_e3_5_topic_assessments.py`，生成 E3.5 topic-level instantiation 运行包：

- Run id：`20260630T083621Z_e3_5_gri3_3_topic_instantiation`
- Run directory：`data/runs/stage_e3_5/20260630T083621Z_e3_5_gri3_3_topic_instantiation/`
- Topic-level assessments：16
- Verdict：全部为 `manual_review`
- Requirement support status：全部为 `not_assessed`
- `not_scored_reason`：`pending_e3_5_topic_level_llm_assessment`
- `llm_called`：`false`

本节点已完成的是 GRI 3-3 议题级实例化和可追溯 assessment 占位，不等同于真实 LLM 核验结论。后续如需把 3-3 纳入最终统计，需要单独授权 E3.5 真实 LLM 核验并完成人工复核。

## 2026-06-30 索引逐行口径修正

主流程复核后确认：16 条 materiality-topic draft 只能作为议题归并映射，最终 E3.5 assessment unit 应采用报告 GRI 索引逐行口径。原因是报告 GRI 索引在各 topic-specific GRI Standard 下列示 Disclosure 3-3，当前 P0 口径要求最终核验单元以原始索引逐行复核结果为准。

已执行 `scripts/build_stage_e3_5_index_3_3_assessments.py`，生成索引逐行 3-3 实例化运行包：

- Run id：`20260630T084946Z_e3_5_gri3_3_index_instantiation`
- Run directory：`data/runs/stage_e3_5/20260630T084946Z_e3_5_gri3_3_index_instantiation/`
- GRI 3-3 index-row instances：29
- Expected final current assessment units：143
- Verdict：全部为 `manual_review`
- Requirement support status：全部为 `not_assessed`
- `not_scored_reason`：`pending_e3_5_index_row_3_3_llm_assessment`
- `llm_called`：`false`

已写入范围文件：

- `docs/stage_e3_5/e3_5_gri_3_3_index_instance_scope.json`

因此，当前 unified final advisor 真实生成应暂停。后续顺序应为：先对 29 条 3-3 index-row instances 执行真实 LLM 核验和 smoke review，再合并 114 条 ordinary effective assessments 与 3-3 effective assessments，最后生成统一 final advisor。

## 2026-06-30 真实 LLM 核验执行记录

已按用户明确授权执行 E3.5 GRI 3-3 index-row 真实 LLM 核验，发送范围限于 29 条 3-3 instances、公开报告证据片段、GRI 3-3 requirements、索引页定位和 Analyst Prompt。

- Runner：`scripts/run_stage_e3_5_index_3_3_llm.py`
- Run id：`20260630T085702Z_e3_5_gri3_3_llm_index_assessment`
- Run directory：`data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/`
- LLM called：`true`
- Model：`deepseek-v4-flash`
- Assessment count：29
- Validation status：`ok`
- Raw verdict distribution：`partially_disclosed=17`、`not_disclosed=6`、`manual_review=6`

机器 smoke 初次发现 18 个硬预警，均为 `source_text_not_verbatim`。已执行 `scripts/apply_stage_e3_5_3_3_source_text_corrections.py`，保留 raw LLM artifact 不变，生成 corrected artifacts：

- `analyst_result_merged_corrected.json`
- `analysis_run_merged_corrected.json`
- `manual_review_input_merged_corrected.json`
- `source_text_correction_log.json`
- `machine_smoke_review_result_corrected.json`

修正后结果：

- `source_text_correction_count=55`
- `validation_status_after_source_text_corrections=ok`
- `machine_smoke_hard_issue_count_after_source_text_corrections=0`
- Gate status：`pending_human_smoke_review_after_source_text_corrections`

已生成 smoke review 抽样模板：

- `data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/smoke_review_template.json`

说明：机器 smoke 只能检查 index-only positive、页码偏移、source_text 省略号、partial gap 字段、manual_review reason code 等结构问题；不能替代人工 smoke review。E3.5 结果在人工 smoke review 通过前不得标记为 clean accepted。

## 2026-06-30 143 条 final current set draft

已生成 143 条 current assessment unit draft：

- Builder：`scripts/build_stage_e3_final_current_effective_set.py`
- Run id：`20260630T091725Z_e3_final_current_effective_set_draft`
- Run directory：`data/runs/stage_e_final_assessment_set/20260630T091725Z_e3_final_current_effective_set_draft/`
- Doc summary：`docs/stage_e3/e3_final_current_effective_assessment_set_draft.json`
- Scope：`114 ordinary current_gap + 29 GRI 3-3 index-row assessments = 143`
- Verdict distribution：`partially_disclosed=59`、`not_disclosed=31`、`manual_review=51`、`disclosed=2`
- Status：`draft_pending_e3_5_human_smoke_review`

该 draft 可作为人工 smoke review 和后续 final advisor 输入准备的范围基础，但不得作为最终 clean effective set 使用。

## 2026-06-30 人工 Smoke Review 字段修正

已根据人工 smoke review 结论写入结果文件：

- `data/runs/stage_e3_5/20260630T085702Z_e3_5_gri3_3_llm_index_assessment/smoke_review_result.json`

人工 smoke review 原始阶段门为：

- `blocked_required_field_corrections_before_acceptance`

已执行 `scripts/apply_stage_e3_5_3_3_smoke_review_corrections.py`，保留 raw 与 corrected artifacts 不变，新增 reviewed artifacts：

- `analyst_result_merged_reviewed.json`
- `analysis_run_merged_reviewed.json`
- `manual_review_input_merged_reviewed.json`
- `human_smoke_review_correction_log.json`
- `merged_validation_result_after_human_smoke_review_corrections.json`
- `machine_smoke_review_result_reviewed.json`

字段修正摘要：

- `current_gap:GRI303:3-3`：`manual_review` 修正为 `partially_disclosed`，补充水资源正文证据并绑定 3-3:c、3-3:d、3-3:d:i、3-3:d:iii、3-3:e:ii、3-3:e:iii。
- `current_gap:GRI301:3-3`：保持 `partially_disclosed`，将 3-3:e:ii 调整为 `partially_met` 并移入 `partial_requirements`。
- `current_gap:GRI401:3-3`：`manual_review` 修正为 `partially_disclosed`，绑定雇佣章节、员工结构、员工流失率、薪酬福利、民主沟通等正文证据。
- `current_gap:GRI414:3-3`：保持 `partially_disclosed`，补充供应商绩效表证据，将 3-3:e:ii、3-3:e:iii 调整为 `partially_met`。

Reviewed artifact 结果：

- 29 条 3-3 reviewed verdict 分布：`partially_disclosed=19`、`not_disclosed=6`、`manual_review=4`
- `validation_status_after_human_smoke_review_corrections=ok`
- `machine_smoke_hard_issue_count_after_human_smoke_review_corrections=0`
- Pre-acceptance stage gate：`reviewed_field_corrections_applied_pending_acceptance`

已按 reviewed artifacts 重建 143 条 current assessment unit draft：

- Run id：`20260630T112719Z_e3_final_current_effective_set_draft`
- Run directory：`data/runs/stage_e_final_assessment_set/20260630T112719Z_e3_final_current_effective_set_draft/`
- Verdict distribution：`partially_disclosed=61`、`not_disclosed=31`、`manual_review=49`、`disclosed=2`
- Draft status：`draft_pending_e3_5_human_smoke_review`

2026-06-30 主流程追认结果：

- E3.5 reviewed artifacts 已明确接受为 effective input。
- 当前 E3.5 stage gate：`accepted_after_human_smoke_review_field_corrections`
- 已生成 143 条 accepted current assessment set：`data/runs/stage_e_final_assessment_set/20260630T113930Z_e3_final_current_effective_set_accepted/final_current_effective_assessment_set.json`
- 143 条 unified final Advisor 已真实生成，effective 输出为：`data/runs/stage_e_final_advisor/20260630T114005Z_e3_143_unified_final_advisor/final_advisor_result_corrected.json`

## 验证记录

- `py_compile scripts/build_stage_e3_5_topic_assessments.py` 通过。
- `pytest tests/test_stage_e3_5_and_cleanup_artifacts.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-cleanup` 通过，结果 3 passed。
- `pytest tests/test_stage_e3_5_and_cleanup_artifacts.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-index-row` 通过，结果 4 passed。
- `pytest tests/test_stage_e3_5_index_3_3_runner.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-3-3-runner` 通过，结果 2 passed。
- `AnalysisRun.model_validate_json` 通过。
- topic count 等于 16。
- index-row 3-3 instance count 等于 29。
- 未包含 `current_gap:GRI3:3-3_generic`。
- 16 条 assessment 均为 `manual_review`，且均带 `pending_e3_5_topic_level_llm_assessment`。
- 29 条 index-row assessment 均为 `manual_review`，且均带 `pending_e3_5_index_row_3_3_llm_assessment`。
- E3.5 corrected LLM artifact 通过 `validate_stage_e2_1_evidence_contract.py --assessment-file .../analyst_result_merged_corrected.json`。
- 143 条 final current set draft 通过 `validate_stage_e2_1_evidence_contract.py --assessment-file .../final_current_effective_assessment_set_draft.json`。
- 143 条 `analysis_run_draft.json` 通过 `AnalysisRun.model_validate_json`。
- E3.5 reviewed artifact 通过 `validate_stage_e2_1_evidence_contract.py --assessment-file .../analyst_result_merged_reviewed.json`。
- 143 条 reviewed draft set 通过 `validate_stage_e2_1_evidence_contract.py --assessment-file .../20260630T112719Z_e3_final_current_effective_set_draft/final_current_effective_assessment_set_draft.json`。
- 143 条 accepted set 通过 `validate_stage_e2_1_evidence_contract.py --assessment-file .../20260630T113930Z_e3_final_current_effective_set_accepted/final_current_effective_assessment_set.json`。
- 143 条 accepted `analysis_run.json` 通过 `AnalysisRun.model_validate_json`，数量为 143，唯一数为 143，不含 `current_gap:GRI3:3-3_generic`。
- 143 条 unified final Advisor corrected validation 为 ok，建议数 141，errors 与 warnings 均为空。

## 风险

- PDF 矩阵抽取有布局风险，重要性等级应进行人工视觉核验。
- 报告第 14 页文本存在“品质量与安全”等抽取缺字风险；topic 名称以第 10 页 ESG 战略与目标和目录表述交叉校正为“产品质量与安全”。
- 3-3 已完成真实 LLM 核验和 reviewed effective acceptance，但 AI 输出仍需进入阶段 F 人工评测。
- E3 final evaluation 不再受 Advisor regeneration 阻塞；后续重点是 traceability cleanup 结果接受或人工豁免、final Advisor 建议人工评测和论文实验统计。
