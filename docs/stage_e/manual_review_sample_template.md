# 阶段 E 人工复核样本模板

## 样本字段

| 字段 | 含义 | 是否必填 |
|---|---|---|
| `run_id` | AnalysisRun ID | 是 |
| `assessment_id` | DisclosureAssessment ID | 是 |
| `manifest_item_id` | P0 disclosure manifest item ID | 是 |
| `standard_id` | GRI 标准 ID | 是 |
| `canonical_disclosure_id` | GRI 披露项 ID | 是 |
| `assessment_mode` | current_gap/readiness_2026/watchlist_2027 | 是 |
| `model_verdict` | 模型输出 verdict | 是 |
| `human_verdict` | 人工复核 verdict | 是 |
| `evidence_page` | 报告证据页码 | 是 |
| `evidence_text` | 报告证据摘录 | 是 |
| `error_type` | 错误类型 | 否 |
| `review_note` | 复核说明 | 是 |

## error_type 枚举

- `standard_applicability`
- `chinese_terminology`
- `evidence_retrieval`
- `model_reasoning`
- `output_format`
- `human_policy`
- `not_error`

## 复核原则

- 没有报告证据时，不得把结论复核为确定性已披露或未披露。
- 人工复核应记录证据页码和证据摘录。
- 对模型输出与人工结论不一致的样本，必须填写 `error_type`。
