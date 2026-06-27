# 阶段 E 真实运行 Runbook

## 目的

执行一次真实 P0 单报告分析，保存原始模型输出、结构化 AnalysisRun、人工复核输入和运行日志。

## 运行前检查

- `validate_p0_evidence_layer.py` 通过。
- `validate_stage_d_agent_contract.py` 通过。
- `.env` 中模型配置可用。
- 用户确认允许调用外部 LLM，并接受可能产生的费用。

## 输出目录

`data/runs/stage_e/<run_id>/`

包含：

```text
analysis_run.json
analyst_raw_llm_output.txt
advisor_raw_llm_output.txt
manual_review_input.json
run_summary.json
```

## 注意

- 不提交 `.env`。
- 不把未人工复核的 AI 输出写成正式披露结论。
- 运行失败时保存失败阶段和错误信息。
