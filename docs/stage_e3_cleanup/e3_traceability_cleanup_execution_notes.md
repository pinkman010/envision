# E3 Traceability Cleanup Execution Notes

## 执行边界

本节点负责生成 E3 current scope 的追溯性清洗映射与人工豁免包。主流程未修改 114 条 effective assessment artifact，未覆盖 raw LLM artifact，未修改原始 PDF，未调用外部 LLM。

清洗范围包括：

- requirement ID 清洗。
- `supporting_evidence_ids` 绑定统一。
- PDF `source_text` 机器定位修正或人工豁免。
- stale Advisor 输出识别与 unified final advisor 输入准备。

## 2026-06-30 主流程执行记录

已由主流程执行 `scripts/build_stage_e3_traceability_cleanup_artifacts.py`，生成清洗运行包：

- Run id：`20260630T083619Z_e3_traceability_cleanup`
- Run directory：`data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup/`
- Effective assessment count：114
- Effective artifacts modified：`false`
- Raw artifacts modified：`false`

生成文件：

- `traceability_cleanup_result.json`
- `requirement_id_cleanup_map.json`
- `evidence_binding_cleanup_map.json`
- `pdf_source_text_location_waiver.json`
- `run_summary.json`

## 清洗结果摘要

- Requirement references not in checklist：25 unique IDs。
- Evidence binding cleanup entries：89。
- PDF source_text 定位：沿用 E3 acceptance audit baseline，159 条正文证据中 PyPDF2 匹配 28 条、未匹配 131 条。
- PDF 定位状态：已生成 `manual_waiver_package_generated_pending_human_acceptance`，用于说明 PyPDF2 全字符串匹配不足以作为唯一 hard gate。

## 口径说明

- 25 个 requirement 引用清洗点主要来自两类问题：GRI303 的点号层级 ID 可规范化为冒号层级 ID；batch05 的父级 disclosure ID 不应作为 leaf requirement 引用。
- 89 个 evidence 绑定清洗点主要是 `supporting_evidence_ids` 指向 `chunk_id`，最终审计口径建议统一改为指向 `evidence[].evidence_id`，`chunk_id` 保留为 evidence metadata。
- PDF `source_text` 未做批量自动改写。原因是 PDF 表格和版式抽取会导致 PyPDF2 文本顺序与可视页面不一致；当前以人工豁免包记录限制，避免误称全量机器定位通过。

## 验证记录

- `py_compile scripts/build_stage_e3_traceability_cleanup_artifacts.py` 通过。
- `pytest tests/test_stage_e3_5_and_cleanup_artifacts.py -q -p no:cacheprovider --basetemp tmp/pytest-e3-5-cleanup` 通过，结果 3 passed。
- 本地校验确认 cleanup result 中 assessment count 为 114，且 raw/effective artifact 均未被修改。

## 后续约束

- 2026-06-30 主流程已接受 traceability cleanup 阶段门，状态为 `traceability_cleanup_accepted_with_explicit_waivers_for_f_evaluation`。
- 阶段门文件：`docs/stage_e3_cleanup/e3_traceability_cleanup_acceptance_gate.json`、`data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup/stage_gate_acceptance_result.json`。
- 143 条 accepted current assessment set 可以进入 F0 人工评测准备；final Advisor effective 输出 `final_advisor_result_corrected.json` 可以进入建议可用性评测准备。
- E4 持久化、API 与 Streamlit 工作台仍未完成，因此不得写成完整进入 F 阶段或 P0 工作流闭环。
- F0 / 后续 F 阶段 requirement-level metrics 必须使用 `requirement_id_cleanup_map.json` 作为有效映射层，不能直接按 raw requirement ID 统计。
- E4 持久化或 Streamlit 展示前，应将 `supporting_evidence_ids` 统一为 `evidence_id`，`chunk_id` 仅作为 evidence metadata 保留。
- PDF `source_text` 机器匹配限制已人工豁免。论文与报告只能写“证据页码可追溯，部分 source_text 经人工复核豁免机器匹配限制”，不得写成“全部证据原文均机器定位验证通过”。
