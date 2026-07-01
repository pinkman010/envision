# 常见问题（FAQ）

## 1. 当前系统是否已经可以使用？

可以用于当前 P0 范围。

当前可直接使用的是固定报告 artifact-backed review workbench：

- 远景能源 2024 中文 ESG 报告
- 143 条 current disclosure assessments
- 143 条 Advisor coverage
- 条款级查看、人工复核保存、CSV/JSON 导出

当前状态仍是 pending review：

```text
review_status=pending
final_evaluation_status=pending_human_evaluation
```

AI 结果不能直接作为企业正式披露结论。

## 2. 为什么是 143 条？

当前 143 条由两部分构成：

| 类型 | 数量 |
|---|---:|
| ordinary current disclosure | 114 |
| GRI 3-3 index-row instances | 29 |
| 合计 | 143 |

早期出现过 118、115 等技术口径，当前 P0 页面、README 和生命周期文档统一使用 143 条 accepted current assessment set。

## 3. 系统怎么启动？

先写入 E4 pending-review 数据：

```powershell
python scripts/seed_stage_e4_pending_review.py
```

启动后端：

```powershell
python scripts/run_api.py
```

启动前端：

```powershell
streamlit run src/ui/app.py
```

访问：

```text
http://127.0.0.1:8501
```

## 4. 为什么推荐使用 `scripts/run_api.py`？

当前推荐入口是：

```powershell
python scripts/run_api.py
```

原因：

- 它会优先加载项目内 `vendor/python_runtime/`。
- 可以避开部分环境中 `uvicorn` 安装位置和环境权限不一致的问题。
- 与当前 README 和部署说明保持一致。

## 5. 使用 P0 工作台会调用外部 LLM 吗？

不会。

E4 条款复核工作台读取的是已接受的 Stage E artifacts 和 SQLite 数据。只有执行真实分析脚本、重新生成 Advisor 或重新跑 Stage E/E3/E3.5 时才会调用外部 LLM。

## 6. 数据保存在什么位置？

关键数据位置：

| 数据 | 路径 |
|---|---|
| 原始报告和标准 | `data/knowledge_base/` |
| 阶段运行产物 | `data/runs/` |
| E4 工作台 SQLite | `data/sqlite_db/` |
| requirement 复核样本 | `data/review/` |
| 项目内 runtime bridge | `vendor/python_runtime/` |

`data/export_results/` 是导出结果目录，可为空，程序需要时会重建。

## 7. 哪些目录不能随便删？

不要直接删除：

- `data/knowledge_base/`
- `data/runs/`
- `data/sqlite_db/`
- `data/review/`
- `vendor/python_runtime/`
- `.env`

这些目录分别对应原始证据、审计留痕、工作台数据、测试口径、运行补丁和本地配置。

## 8. 哪些内容可以清理？

通常可以清理：

- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- 临时测试目录
- 空的 `data/export_results/`
- 明确带 `superseded_by.json` 且已确认不再需要的旧运行目录

清理前建议先看 `git status --short`，避免误删 tracked 文件。

## 9. 为什么 GRI 索引不能直接判断“已披露”？

GRI 索引主要用于定位披露位置。披露充分性仍需要正文实质证据支持。

当前规则：

- `index_evidence` 只能定位。
- `disclosed` 和 `partially_disclosed` 必须有正文证据。
- 商业保密、从略披露和不适用说明通常进入 `manual_review`。

## 10. 五分类 verdict 是什么？

| verdict | 含义 |
|---|---|
| `disclosed` | 已披露 |
| `partially_disclosed` | 部分披露 |
| `not_disclosed` | 未披露 |
| `not_applicable` | 不适用 |
| `manual_review` | 待人工复核 |

`manual_review` 是风险控制机制，不等同于错误。

## 11. Advisor 建议能直接使用吗？

不能直接作为正式建议使用。

当前 Advisor 状态是：

```text
AI-assisted recommendation pending human review
```

建议内容用于人工复核、修改和导出。对外披露前需要企业 ESG 团队或导师确认。

## 12. 当前支持上传新报告后自动生成 143 条结果吗？

当前 P0 工作台使用固定报告 accepted artifacts。

上传页面和 1+4 Agents 链路仍存在，但“任意报告上传后自动稳定生成完整 143 条核验结果”还没有产品化闭环。这属于后续工程化方向。

## 13. 旧的议题识别、差距分析、人工复核页面还在吗？

旧的议题识别、差距分析、人工复核、对标分析和规则配置页面已从仓库和当前 Streamlit 导航中移除。当前 Streamlit 导航只注册：

- 首页概览
- 报告上传
- 条款复核
- 审计日志

当前 P0 展示和复核以“条款复核”页面为准。

## 14. 如何验证当前 P0 工作台？

运行：

```powershell
$env:PYTHONPATH='vendor/python_runtime'
python -m pytest `
  tests\test_stage_e4_p0_review_store.py `
  tests\test_stage_e4_seed_pending_review.py `
  tests\test_stage_e4_p0_review_api.py `
  tests\test_stage_e4_p0_review_export.py `
  tests\test_stage_e4_import_f_review_results.py `
  tests\test_stage_e4_streamlit_workbench_static.py `
  -q -p no:cacheprovider
```

再检查 live API smoke：

```powershell
python -c "import json; from pathlib import Path; d=json.loads(Path('data/runs/stage_e4/20260701T034420Z_p0_delivery_live_api_smoke/live_api_smoke_result.json').read_text(encoding='utf-8')); assert d['status']=='p0_delivery_live_api_smoke_passed'; print('ok')"
```

## 15. 后续最应该做什么？

当前下一步是 Stage G：

- 整理交付包
- 写演示脚本
- 准备录屏
- 准备项目汇报和答辩口径

工程化后续方向：

- 任意报告上传后的完整 143 条核验链路
- evidence binding 统一为 `evidence_id`
- 更完整的任务管理和异常恢复
- 多用户、权限、部署和生产数据隔离
