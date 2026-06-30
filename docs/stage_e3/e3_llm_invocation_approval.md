# E3 LLM Invocation Approval

## Status

Not approved for execution.

E3 may call DeepSeek only after explicit user confirmation in the active thread. This file is an approval checklist, not approval itself.

## Frozen Invocation Boundary

- Stage: E3, 2024 current disclosure batched full run.
- Report: `data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf`.
- Standard profile: `gri_p0_2024_current_disclosure_v1`.
- Scope file: `docs/stage_e3/e3_current_scope_manifest.json`.
- Excluded from ordinary current-gap statistics:
  - `readiness_2026`
  - `watchlist_2027`
  - `current_gap:GRI3:3-3_generic`
- Execution mode: batched, not one-shot full run.
- Raw LLM outputs: preserve under the batch run directory.
- Secrets: do not write API keys or `.env` content to logs or artifacts.

## Required Confirmation Text

Before any E3 LLM call, obtain an explicit message equivalent to:

```text
I confirm E3 batch <batch_id> may send the required public report evidence snippets, GRI requirement data, and prompts to the configured DeepSeek API.
```

## Approval Record

| Field | Value |
|---|---|
| approved | false |
| approved_batch_id |  |
| approver |  |
| approval_thread_date |  |
| model | DeepSeek configured in local `.env` |
| notes | E2.1-E passed local gates, but E3 execution remains blocked until explicit confirmation. |

## Abort Conditions

Stop the batch and do not continue to the next batch if any of these occur:

- `disclosed` or `partially_disclosed` is supported only by `index_evidence`.
- A `partially_disclosed` item has neither `missing_requirements` nor `partial_requirements`.
- A `manual_review` item lacks `manual_review_reason_codes`.
- Body evidence lacks `source_page`, `report_page_label`, `source_text`, `evidence_kind`, or `chunk_id`.
- Page offset validation fails.
- Advisor output infers internal absence such as "企业未建立" or "企业没有" without internal confirmation.
- Batch smoke review finds a systemic issue.
