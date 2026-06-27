# P0 Verdict 枚举映射

## 代码枚举

`AssessmentVerdict` 当前使用 Python/JSON 友好命名：

| 代码值 | 展示含义 | 生命周期计划旧表述 |
|---|---|---|
| `disclosed` | 已披露 | `disclosed` |
| `partially_disclosed` | 部分披露 | `partial` |
| `not_disclosed` | 未披露 | `missing` |
| `not_applicable` | 不适用 | `notApplicable` |
| `manual_review` | 待人工复核 | `manualReview` |

## 规则

- P0 内部契约以代码值为准。
- UI/API/导出可以映射为中文展示值。
- 不在 E0 重命名现有枚举，避免破坏已通过验证的模型与 manifest。
