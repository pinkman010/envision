# P0 阶段 A：来源与范围冻结记录

> **给执行代理的说明：** 本文件是已完成阶段的记录，不是待执行计划。不要根据本文件重新执行阶段 A。本文件用于确认 P0 来源溯源、范围边界、GRI 索引处理方式，以及阶段 B/C 的输入前提。

**目标：** 冻结 P0 单报告 ESG 披露分析的原始资料、标准范围和分析边界，确保后续 manifest、领域契约、证据层、Agent 改造均建立在可追溯资料上。

**架构：** 阶段 A 不改变运行时架构。它建立来源与范围基线，供阶段 B 的 `p0_gri_disclosure_manifest.json`、分析契约，以及阶段 C 的 GRI 条款与证据层使用。

**技术栈：** 本地 PDF、SHA-256 哈希、JSON manifest、Python/pypdf 验证、Git 跟踪 `data/knowledge_base/manifests/*.json` 元数据。

---

## 1. 阶段 A 目的

阶段 A 的目的不是让 Agent 开始分析，而是先回答后续阶段必须依赖的基础问题：

1. P0 分析哪一份企业报告。
2. 使用哪一份 GRI 官方资料作为权威参考。
3. 哪些 disclosure 进入 2024 `current_gap` 分析。
4. 哪些新标准只进入 `readiness_2026` 或 `watchlist_2027`，不得倒推为 2024 缺口。
5. 原始资料如何证明没有被替换。
6. 报告自带 GRI 索引中的源表错误如何保留审计痕迹。

阶段门：任何条款进入 Agent 前，均能回答“原文在哪里、何时生效、为何适用于本次分析”。

---

## 2. P0 边界

P0 覆盖：

- 业务场景：单报告 ESG 披露分析 MVP。
- 企业报告：远景能源 2024 中文 ESG 报告。
- 标准框架：GRI，按版本和生效日期管理。
- P0 界面：本仓库 Streamlit。
- 当前分析：报告期适用的 GRI disclosure coverage/gap。
- 准备度分析：截至 2026 年生效的新 GRI 要求，只作为下一期披露准备度。
- 观察项：2027 年及以后生效的新 GRI 要求，只作为未来标准观察。

P0 不覆盖：

- 不接入 `C:\Users\43480\Desktop\esg-dashboard`。
- 不把多企业实质性议题对标计入 P0 验收。
- 不把 Claw 舆情监测或实时舆情监测计入 P0 验收。
- 不把登录、多用户协作、企业内部系统接入计入 P0 验收。
- 不把 AI 输出直接视为正式披露结论。

影响：后续阶段只围绕“远景 2024 中文报告 + GRI disclosure 分析 + 证据追溯 + 人工复核”建设，不为展示效果提前开发 P1/P2 能力。

---

## 3. 原始资料

### 3.1 远景能源 2024 中文 ESG 报告

- 相对路径：`data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf`
- 本地完整路径：`C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\peer_reports\Envision Energy 2024-zh.pdf`
- 文档类型：`esg_report`
- 发布方：Envision Energy
- 语言：`zh-CN`
- 报告期：`2024-01-01` 至 `2024-12-31`
- 页数：`78`
- 文件大小：`15,202,630 bytes`
- SHA-256：`57360DCDA8E6256726BE5D2A49F8921E13187B40AE44661549903F702DF38068`
- 溯源状态：`official_catalogue_verified_local_copy_not_binary_matched`
- 官方目录 URL：`https://www.envision-group.com/sustainability`

P0 用途：

- 企业披露事实来源。
- 报告页码、证据原文、人工复核和评测基线。
- GRI 指标索引来源。

限制：

- 本地 PDF 已可读，但未完成与官网 PDF 的二进制级哈希匹配。
- PDF 元数据可显示加密状态，但项目 Conda 环境下文本提取可用。

### 3.2 GRI 官方英文合订本

- 相对路径：`data/knowledge_base/standards/gri_reference/GRI_Standards_Official_Consolidated_Set_en.pdf`
- 本地完整路径：`C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\standards\gri_reference\GRI_Standards_Official_Consolidated_Set_en.pdf`
- 文档类型：`gri_standards_consolidated_set`
- 发布方：Global Reporting Initiative (GRI)
- 语言：`en`
- 页数：`1,022`
- 文件大小：`25,992,242 bytes`
- SHA-256：`5FA47C6680D10DCFF7E3781952F95C7B2AD58A27972812330F7AD40F034FF466`
- 溯源状态：`official_download_sha256_verified`
- 官方来源 URL：`https://www.globalreporting.org/pdf.ashx?id=12024`

P0 用途：

- GRI 英文权威参考资料。
- canonical disclosure ID、标准版本、生效日期和未来 readiness/watchlist 判断依据。

命名决策：

- 目录使用 `gri_reference`，不使用 `gri_2021`。
- 原因：该合订本包含 GRI 2021 通用标准和 2024/2025 后续更新。命名为 `gri_2021` 会误导后续实现，把未来要求误当成 2021 当前要求。

---

## 4. 阶段 A 产物

### 4.1 来源清单

文件：

`data/knowledge_base/manifests/p0_source_manifest.json`

用途：

- 记录两份原始资料。
- 保存路径、文档类型、溯源状态、页数、文件大小和 SHA-256。
- 证明项目使用的是哪两份原始文件。

它回答：

- 使用了哪些资料。
- 资料保存在哪里。
- 哈希是什么。
- 溯源状态是什么。

### 4.2 GRI 披露项清单

文件：

`data/knowledge_base/manifests/p0_gri_disclosure_manifest.json`

用途：

- 冻结 P0 披露分析范围。
- 告诉后端要分析哪些 GRI disclosure。
- 区分源表 ID 与 canonical ID。
- 区分 `current_gap`、`readiness_2026`、`watchlist_2027`。

它回答：

- 哪些 disclosure 行进入范围。
- 哪些行用于 2024 当前缺口分析。
- 哪些行只用于未来准备度或观察项。
- 披露行位于报告索引哪一页。
- 哪些源表 ID 存在已确认笔误。

---

## 5. 远景报告 GRI 索引范围

远景报告 GRI 索引位于 PDF 物理页 71-76。

| PDF 物理页 | 报告页脚页码 | 内容 |
|---|---:|---|
| 71 | 70 | GRI 使用说明、GRI 1、GRI 2 的 2-1 至 2-21 |
| 72 | 71 | GRI 2 的 2-22 至 2-30、GRI 3、GRI 201、GRI 202 |
| 73 | 72 | GRI 203 至 207、GRI 301、GRI 302 |
| 74 | 73 | GRI 303 至 306 |
| 75 | 74 | GRI 308、GRI 401 至 405 |
| 76 | 75 | GRI 406 至 418 |

报告声明参考：

- `GRI 1: Foundation 2021`
- `GRI 2: General Disclosures 2021`
- `GRI 3: Material Topics 2021`
- 报告自带 GRI 索引列出的多个 GRI Topic Standards。

P0 当前缺口范围不是全部 GRI 要求，而是：

> 远景能源 2024 ESG 报告自带 GRI 索引中明确列出的 GRI disclosure items，并用 GRI 官方英文资料对齐 canonical ID 和版本。

避免表述为：

> 2024 年所有已生效 GRI 要求。

原因：该表述会暗示完整 GRI universe 审计，可能包含远景报告未声明采用的标准或行业标准。

---

## 6. 分析模式

### 6.1 `current_gap`

用途：

- 2024 披露缺口分析。
- 基于远景报告自带 GRI 索引。

阶段 A/B 校验后的数量：

- `115` 行。

包括：

- GRI 2：`2-1` 至 `2-30`
- GRI 3：`3-1`、`3-2`、`3-3_generic`
- GRI 201、202、203、204、205、206、207、301、302、303、304、305、306、308、401、402、403、404、405、406、407、408、409、410、413、414、416、417、418 的主题披露项。

限制：

- `3-3_generic` 只是临时范围标记。
- 生产分析应按实质性议题或主题标准实例化 GRI 3-3，不应长期把它当成一个唯一最终评估行。

### 6.2 `readiness_2026`

用途：

- 前瞻性准备度叙事。
- 不计入 2024 披露缺口评分。

数量：

- `1` 行。

包括：

- `GRI 101: Biodiversity 2024`，`2026-01-01` 生效，关联当前 `GRI 304`。

### 6.3 `watchlist_2027`

用途：

- 未来标准变化观察。
- 不计入 2024 披露缺口评分。

数量：

- `2` 行。

包括：

- `GRI 102: Climate Change 2025`，`2027-01-01` 生效。
- `GRI 103: Energy 2025`，`2027-01-01` 生效。

---

## 7. 已确认的源表编号问题

阶段 A 识别并由用户人工核实了远景报告 GRI 索引中的两处编号错误。

### 7.1 GRI 405-2

- 报告位置：用户核实为远景报告第 75 页；GRI 索引 PDF 物理页 75；报告页脚页码 74。
- 披露项：男女基本工资和报酬的比例。
- 源表写作：`405-1`
- canonical disclosure ID：`405-2`
- manifest 状态：`source_typo_confirmed`

处理要求：

- 保留 `source_disclosure_id = 405-1`。
- 后端分析使用 `canonical_disclosure_id = 405-2`。
- 不得静默覆盖源表错误。

### 7.2 GRI 414-2

- 报告位置：用户核实为远景报告第 76 页；GRI 索引 PDF 物理页 76；报告页脚页码 75。
- 披露项：供应链中的负面社会影响以及采取的行动。
- 源表写作：`414-1`
- canonical disclosure ID：`414-2`
- manifest 状态：`source_typo_confirmed`

处理要求：

- 保留 `source_disclosure_id = 414-1`。
- 后端分析使用 `canonical_disclosure_id = 414-2`。
- 不得静默覆盖源表错误。

---

## 8. Git 与数据处理规则

阶段 A 确定的数据版本控制规则：

- 跟踪：`data/knowledge_base/manifests/*.json`
- 忽略：PDF 原文和大部分运行时/生成型 `data/` 内容。

理由：

- JSON manifest 是轻量元数据，支持项目复现。
- PDF 文件较大，并且存在版权/分发边界。
- 仓库应保存溯源和契约元数据，但不提交大型原始二进制资料。

---

## 9. 阶段 A 后的已知限制

阶段 A 尚未产出：

- 结构化 GRI 条款正文。
- GRI 要求的中文工作译文。
- 报告 evidence chunks。
- disclosure 到 evidence 的候选映射。
- Agent/Prompt 改造。
- AnalysisRun 持久化。
- Streamlit 任务中心。
- 人工复核流程。
- 可导出的最终复核结果。
- 评测指标。

PDF 抽取限制：

- 报告 GRI 索引是表格结构。
- 普通文本抽取可能破坏表格边界、合并相邻 ID、拆开多行单元格或打乱双栏阅读顺序。
- 因此 manifest 不能盲目信任纯文本抽取结果；已知源表问题必须保留人工确认痕迹。

---

## 10. 阶段 A 完成条件

阶段 A 通过的条件：

- 原始 PDF 本地存在，且哈希已记录。
- `p0_source_manifest.json` 记录资料来源和溯源状态。
- GRI 参考目录命名为 `gri_reference`，不是 `gri_2021`。
- `p0_gri_disclosure_manifest.json` 冻结 P0 披露范围。
- `current_gap`、`readiness_2026`、`watchlist_2027` 已分离。
- 405-2 与 414-2 的源表错误已保留并标记为 `source_typo_confirmed`。
- `data/knowledge_base/manifests/*.json` 可进入 Git，PDF 仍被忽略。
- 阶段 B 可读取 manifest 并构建验证过的分析契约。

阶段 B 后续验证确认：

- `total_disclosures = 118`
- `current_gap = 115`
- `readiness_2026 = 1`
- `watchlist_2027 = 2`
- `source_documents_loaded = 2`
- `source_documents_match_manifest = true`
- `has_405_2_typo = true`
- `has_414_2_typo = true`
- `has_3_3_scope_marker = true`

---

## 11. 交接给阶段 B 与阶段 C

阶段 B 使用阶段 A 产物创建：

- Pydantic 领域模型。
- manifest 读取器。
- `AnalysisRun` 契约。
- 可重复运行的验证脚本。

阶段 C 使用阶段 A/B 产物创建：

- `p0_gri_requirement_pack.json`
- `p0_report_evidence_index.json`
- GRI 条款定位记录。
- 报告证据分块索引。
- 阶段 C 验证脚本。

在阶段 C 产出条款要求与报告证据候选前，不进入 Agent/Prompt 改造。