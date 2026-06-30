# E3 Expected Outputs

E3 outputs must be saved per batch under a timestamped batch directory. The first batch naming pattern is `data/runs/stage_e/20260630T000000Z_e3_batch_01_gri2/`; later batches replace the timestamp and batch suffix with the actual approved batch.

## Required Batch Artifacts

Each batch run directory must contain:

- `run_summary.json`
- `analysis_run.json`
- `retrieval_result.json`
- `analyst_result.json`
- `advisor_result.json`
- `analyst_raw_llm_output.txt`
- `advisor_raw_llm_output.txt`
- `manual_review_input.json`
- `batch_scope_manifest.json`
- `batch_validation_result.json`
- `smoke_review_template.json`
- `smoke_review_result.json` after human smoke review

## Required Assessment Fields

Each disclosure assessment must preserve:

- `manifest_item_id`
- `standard_id`
- `standard_year`
- `canonical_disclosure_id`
- `assessment_mode`
- `verdict`
- `confidence`
- `evidence`
- `requirement_checks`
- `missing_requirements`
- `partial_requirements`
- `not_applicable_requirements`
- `manual_review_requirements`
- `manual_review_reason_codes`
- `readiness_verdict`
- `not_scored_reason`
- `aggregation_reason`
- `rationale`
- `review_status`

## Required Evidence Fields

Every non-index body evidence item used to support `disclosed` or `partially_disclosed` must include:

- `chunk_id`
- `source_document`
- `source_page`
- `report_page_label`
- `source_text`
- `evidence_kind`
- `supports_requirement_ids`
- `judgment_reason`

## Batch Summary Fields

`run_summary.json` or `batch_validation_result.json` must report:

- `batch_id`
- `batch_label`
- `run_id`
- `llm_called`
- `started_at`
- `completed_at`
- `assessment_count`
- `verdict_counts`
- `manual_review_count`
- `index_only_block_count`
- `page_offset_error_count`
- `advisor_boundary_error_count`
- `validation_status`

## Smoke Review Requirements

After each batch, manually smoke review 3 to 5 items. The smoke review must include at least:

- one `disclosed` or highest-confidence positive item when present
- one `partially_disclosed` item when present
- one `manual_review` item when present
- one item with multi-page evidence when present
- one item with no obvious report body evidence when present

Stop before the next batch if smoke review finds a systemic issue.
