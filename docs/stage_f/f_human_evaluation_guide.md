# F 阶段人工评测指南

## 1. 评测目标

本阶段用于人工复核系统对远景能源 2024 ESG 报告的 GRI 参照披露核验结果，并评估 Advisor 建议是否可用。

评测对象：

- 143 条 final assessments
- 143 条 Advisor review rows（141 条真实 Advisor 建议 + 2 条 `disclosed/no_action` coverage 行）
- 140 条 requirement-level 抽样记录

人工评测结果用于计算：

- disclosure verdict accuracy
- macro F1
- requirement support accuracy
- evidence page accuracy
- manual_review justified rate
- Advisor recommendation acceptance rate
- error attribution

## 2. 参考文件

必看文件：

- `data/runs/stage_f/20260630T132346Z_f_human_evaluation_package/f_human_evaluation_workbook.xlsx`
- `data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf`
- `data/runs/stage_e_final_assessment_set/20260630T113930Z_e3_final_current_effective_set_accepted/final_current_effective_assessment_set.json`
- `data/runs/stage_e_final_advisor/20260630T114005Z_e3_143_unified_final_advisor/final_advisor_result_corrected.json`
- `data/processed/gri/p0_gri_requirement_checklist.json`

辅助文件：

- `data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup/`
- `docs/stage_e3/e3_final_current_effective_assessment_set.json`
- `docs/stage_e3/e3_final_advisor_invocation_approval.md`
- `docs/DEV_LOG.md`

主要填写文件是 `f_human_evaluation_workbook.xlsx`，其中包含 5 个 sheet：

- `README`
- `1_assessment_review`
- `2_advisor_review`
- `3_requirement_sample`
- `error_taxonomy`

CSV/JSON 文件是备份和后续指标计算输入，不建议人工直接改 CSV/JSON。

## 3. 总体原则

1. 只根据公开 ESG 报告和 GRI requirement 判断。
2. GRI 索引只能用于定位，不能单独支持 `disclosed`。
3. 必须逐项 requirement 判断，不能因主题相关就判整项充分披露。
4. `manual_review` 不直接算错，要判断是否合理触发人工复核。
5. `not_applicable` 必须有明确理由。
6. Advisor 建议不能推断企业内部不存在制度、流程或数据。

推荐表述：

- 报告未披露……
- 基于公开报告无法核实……
- 需要企业内部确认……

避免表述：

- 企业没有……
- 企业未建立……
- 企业缺乏……
- 内部不存在……

## 4. `1_assessment_review`

用途：人工复核 143 条 final assessments 的 disclosure-level 结论。

预填字段：

- `manifest_item_id`
- `standard_id`
- `canonical_disclosure_id`
- `assessment_mode`
- `ai_verdict`
- `ai_confidence`
- `ai_review_status`
- `ai_rationale`
- `ai_aggregation_reason`
- `missing_requirements`
- `partial_requirements`
- `manual_review_requirements`
- `manual_review_reason_codes`
- `not_applicable_requirements`
- `requirement_count`
- `requirement_support_summary`
- `requirement_ids`
- `evidence_count`
- `evidence_kinds`
- `source_pages`
- `report_page_labels`
- `evidence_ids`
- `chunk_ids`
- `source_sections`
- `evidence_source_text_preview`
- `cleanup_requirement_note`
- `cleanup_evidence_binding_note`
- `pdf_source_text_waiver_note`

人工填写字段：

- `human_verdict`
- `human_verdict_reason`
- `human_evidence_page_check`
- `human_requirement_gap_check`
- `human_error_code`
- `human_error_notes`
- `reviewer`
- `reviewed_at`

`human_verdict` 取值：

- `disclosed`
- `partially_disclosed`
- `not_disclosed`
- `not_applicable`
- `manual_review`

判断口径：

- `disclosed`：所有适用 mandatory requirements 均有充分正文证据支持。
- `partially_disclosed`：部分 mandatory requirements 有正文证据支持，但仍有明确缺口。
- `not_disclosed`：完成合理检索后，没有找到有效正文证据，也没有合理省略或不适用说明。
- `not_applicable`：报告或业务事实提供了充分的不适用理由。
- `manual_review`：存在省略理由待审、适用性不清、证据冲突、页码疑问、文本质量问题或边界问题。

检查字段取值建议：

- `human_evidence_page_check`：`ok / minor_issue / wrong_page / not_checkable`
- `human_requirement_gap_check`：`ok / too_coarse / missing_gap / wrong_gap / not_checkable`
- `human_error_code`：使用 `error_taxonomy` 中的错误代码；无错误填 `none`
- `human_verdict_reason`：简要说明人工 verdict 的依据，尤其是 AI verdict 被改动时
- `human_error_notes`：记录页码、证据、requirement gap 或 aggregation 的具体问题

## 5. `2_advisor_review`

用途：人工复核 Advisor 建议是否正确、可用、不过度推断。

评测范围：

- 141 条实际 Advisor 建议，`row_type=advisor_recommendation`
- 2 条 `disclosed/no_action` coverage 项，`row_type=disclosed_no_action_coverage`

2 条 coverage 项对应：

- `current_gap:GRI2:2-22`
- `current_gap:GRI2:2-29`

这 2 条在 accepted assessments 中为 `disclosed`，原始 Advisor 没有生成建议。评测时只需确认 `no_action` 是否合理。

预填字段：

- `review_key`
- `row_type`
- `manifest_item_id`
- `standard_id`
- `canonical_disclosure_id`
- `linked_ai_verdict`
- `recommendation_type`
- `priority`
- `requirement_id`
- `recommendation_type`
- `priority`
- `current_disclosure`
- `gap`
- `next_report_addition`
- `requires_internal_data`
- `recommendation`
- `basis`
- `advisor_review_status`

人工填写字段：

- `human_usefulness_rating`
- `human_accuracy_check`
- `human_overreach_check`
- `human_requirement_binding_check`
- `human_internal_data_flag_check`
- `human_error_code`
- `human_comment`
- `reviewer`
- `reviewed_at`

`human_usefulness_rating` 取值建议：

- `accepted`
- `minor_revision`
- `major_revision`
- `rejected`

检查字段取值建议：

- `human_accuracy_check`：`ok / minor_issue / wrong_gap / conflicts_with_assessment / not_checkable`
- `human_overreach_check`：`ok / overclaims_internal_absence / needs_internal_confirmation / not_checkable`
- `human_requirement_binding_check`：`ok / wrong_requirement / too_broad / missing_requirement / not_checkable`
- `human_internal_data_flag_check`：`ok / should_be_true / should_be_false / not_checkable`
- `human_error_code`：使用 `error_taxonomy` 中的错误代码；无错误填 `none`

判断口径：

- `accepted`：绑定正确 requirement，基于公开报告证据，缺口表述准确，行动建议具体。
- `minor_revision`：方向正确，但措辞、优先级、`requires_internal_data` 或具体性需要小修。
- `major_revision`：绑定、缺口、建议类型或证据基础存在明显问题，需要重写。
- `rejected`：建议不基于证据、越界推断、绑定错误，或与 assessment 结论冲突。

## 6. `3_requirement_sample`

用途：抽样评测 requirement-level support status。

建议样本量：

- 最低：50-80 条边界样本
- 推荐：100-150 条分层样本

优先覆盖：

- `disclosed`
- `partially_disclosed`
- `not_disclosed`
- `manual_review`
- GRI 3-3
- 定量披露
- 省略说明
- 跨页证据
- 曾人工修正过的条目

预填字段：

- `sample_id`
- `selected_reason`
- `manifest_item_id`
- `standard_id`
- `canonical_disclosure_id`
- `assessment_verdict`
- `requirement_id_raw`
- `requirement_id_effective`
- `cleanup_requirement_action`
- `support_status`
- `is_mandatory`
- `conditional`
- `condition_text`
- `requirement_id`
- `requirement_text`
- `supporting_evidence_ids_raw`
- `supporting_evidence_ids_effective`
- `evidence_binding_cleanup_note`
- `evidence_pages`
- `report_page_labels`
- `evidence_kinds`
- `evidence_source_text_preview`
- `missing_reason`
- `manual_review_reason`
- `assessment_rationale`

人工填写字段：

- `human_support_status`
- `human_requirement_text_check`
- `human_evidence_binding_check`
- `human_error_code`
- `human_comment`
- `reviewer`
- `reviewed_at`

`human_support_status` 取值：

- `met`
- `partially_met`
- `not_met`
- `not_applicable_claimed`
- `manual_review`
- `not_assessed`

判断口径：

- `met`：该 requirement 的关键要素均被正文证据支持。
- `partially_met`：有相关正文证据，但维度、数据、方法、范围或拆分不完整。
- `not_met`：未找到能支持该 requirement 的有效正文证据。
- `not_applicable_claimed`：报告声称不适用或从略，但理由仍需判断是否充分。
- `manual_review`：适用性、证据解释、页码、文本质量或省略理由需要人工判断。

检查字段取值建议：

- `human_requirement_text_check`：`ok / wrong_requirement / too_broad / not_checkable`
- `human_evidence_binding_check`：`ok / wrong_evidence / missing_evidence / not_checkable`
- `human_error_code`：使用 `error_taxonomy` 中的错误代码；无错误填 `none`

## 7. 错误类型

`human_error_code` 建议使用 `error_taxonomy` sheet 中的错误代码。常用枚举包括：

- `none`
- `requirement_mapping_error`
- `retrieval_miss`
- `evidence_page_error`
- `source_text_not_verbatim`
- `source_text_not_found`
- `evidence_requirement_binding_issue`
- `wrong_support_status`
- `wrong_verdict_aggregation`
- `over_manual_review`
- `under_manual_review`
- `omission_reason_handling_error`
- `not_applicable_without_reason`
- `index_only_positive_risk`
- `advisor_overclaim`
- `advisor_not_actionable`
- `advisor_wrong_requirement_binding`
- `advisor_wrong_recommendation_type`
- `advisor_wrong_priority`
- `duplicate_or_redundant_advice`
- `traceability_limitation`

## 8. 推荐填写顺序

1. `1_assessment_review`
2. `2_advisor_review`
3. `3_requirement_sample`

时间不足时，前两张为必填；第三张可先填 50-80 条边界样本。

## 9. 填写注意事项

- 不要修改系统预填字段。
- 只填写 `human_*` 字段、`reviewer` 和 `reviewed_at`。
- 不要修改 `review_key`、`manifest_item_id`、AI verdict、requirement、evidence、recommendation 等系统预填字段。
- 不确定时填 `uncertain` 或 `manual_review`，并在 `human_comment` 或 `human_error_notes` 中说明原因。
- 页码判断优先检查 `source_page` 和 `report_page_label`。
- 表格证据可以按 PDF 页面视觉确认。
- 3-3 条目按 topic 判断，不使用 `3-3_generic`。
- 省略披露重点判断省略理由是否充分。
- Advisor 建议必须区分报告披露缺口和内部管理改进建议。

## 10. 完成标准

最低完成要求：

- `1_assessment_review` 全量填写 143 行
- `2_advisor_review` 全量填写 143 行，包括 141 条 Advisor 建议和 2 条 `no_action` coverage
- `3_requirement_sample` 至少填写抽样样本；当前 workbook 已抽样 140 行，建议全量填写

完成后可计算：

- 五分类准确率
- macro F1
- requirement support accuracy
- evidence page accuracy
- source_text traceability rate
- manual_review justified rate
- Advisor acceptance rate
- Advisor overclaim rate
- 错误类型分布
- 误差复盘报告
- 论文实验结果摘要
