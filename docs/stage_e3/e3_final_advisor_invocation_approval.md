# E3 143-Item Unified Final Advisor Invocation

## Status

- DeepSeek API has been called for the accepted 143-item final current disclosure set.
- E3.5 reviewed artifacts are accepted as effective input.
- Input includes 114 ordinary current-gap assessments and 29 GRI 3-3 index-row assessments.

## Send Scope

- Accepted current assessment units: 143
- Advisor input is reduced to assessment fields, requirement checks, and evidence kinds rendered by `advisor_prompt.j2`.
- No `.env`, API keys, raw PDFs, or non-public internal data.

## Local Artifacts

- Accepted set: `C:\Alvin\SUFE\整合实践\envision\data\runs\stage_e_final_assessment_set\20260630T113930Z_e3_final_current_effective_set_accepted\final_current_effective_assessment_set.json`
- Advisor run directory: `C:\Alvin\SUFE\整合实践\envision\data\runs\stage_e_final_advisor\20260630T114005Z_e3_143_unified_final_advisor`
- Input file: `final_effective_analyst_input.json`
- Raw output file: `final_advisor_result.json`
- Effective output file: `final_advisor_result_corrected.json`
- Correction note: raw output is preserved; corrected output only recalculates `summary` counts from `p0_recommendations`.

## Verdict Distribution

- `disclosed`: 2
- `manual_review`: 49
- `not_disclosed`: 31
- `partially_disclosed`: 61

## Config Snapshot

- `LLM_MODEL`: `deepseek-v4-flash`
- `LLM_BASE_URL`: `https://api.deepseek.com`
- `LLM_THINKING_TYPE`: `enabled`
- `LLM_REASONING_EFFORT`: `max`
- `LLM_RESPONSE_FORMAT`: `json_object`

## Validation

- Advisor validation status: `ok`
- Recommendation count: `141`
- Validation warnings after correction: `0`

## Risk

- Advisor output remains AI-assisted and must be treated as pending review until final human evaluation.
- Recommendations may describe public-report disclosure gaps only; internal management claims require internal confirmation.
