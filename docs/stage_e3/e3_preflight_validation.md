# E3 Preflight Validation

Run this checklist before requesting approval for each E3 batch.

## Local Commands

```powershell
$tmp = Join-Path (Get-Location) 'tmp\pytest-e3-preflight'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$env:TEMP = $tmp
$env:TMP = $tmp
C:\ProgramData\miniconda3\envs\envision\python.exe -m pytest tests\test_stage_e2_1_e_field_corrections.py tests\test_stage_e2_1_evidence_contract.py tests\test_stage_e2_1_d_index_target_evidence.py tests\test_p0_requirement_checklist.py -q -p no:cacheprovider --basetemp $tmp
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_stage_e2_1_e_field_corrections.py
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_stage_e2_1_evidence_contract.py --manual-review-result data\runs\stage_e\20260629T170447Z_e2_1_regression\manual_review_result.json
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_index_target_evidence.py
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_requirement_checklist.py
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\check_llm_config.py
```

## Expected Local Results

- Pytest exits 0.
- All validators return `status: ok`.
- `validate_p0_requirement_checklist.py` reports:
  - `requirement_count=661`
  - `current_gap_scored_requirement_count=658`
  - `topic_instantiation_required_count=1`
  - `excluded_counts_by_mode.readiness_2026=1`
  - `excluded_counts_by_mode.watchlist_2027=2`
- `check_llm_config.py` must not print secrets.

## Batch Preflight Checks

For the target batch:

- Confirm the batch appears in `docs/stage_e3/e3_current_scope_manifest.json`.
- Confirm the batch excludes `current_gap:GRI3:3-3_generic`.
- Confirm output directory does not already contain a completed run with the same run id.
- Confirm the active thread contains explicit approval for that batch.
- Confirm smoke review template is ready for 3 to 5 sampled items after the batch.

## Stop Criteria

Do not request LLM approval if any local validation fails or if the batch scope cannot be reconciled to the frozen scope manifest.
