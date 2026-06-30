# E3.5 GRI 3-3 Topic-Level Instantiation Plan

## 结论

E3.5 可以启动，但最终核验单元应采用报告 GRI 索引逐行口径。依据是 `docs/stage_e3/e3_current_scope_acceptance_result.json` 已明确 `allow_start_e3_5_gri_3_3_topic_instantiation=true`，但 clean acceptance、final evaluation 和 final Advisor chain 仍处于 blocked 状态。

`current_gap:GRI3:3-3_generic` 不进入普通评分。GRI 3-3 必须从 generic 节点展开为报告 GRI 索引中的 topic-specific 3-3 instances，再进入真实 LLM 核验和人工复核。

本阶段不得阻塞 traceability cleanup。E3.5 与 requirement ID cleanup、evidence binding cleanup、PDF evidence location cleanup 并行推进；unified final advisor 真实生成暂停到 3-3 effective assessments 完成之后。

2026-06-30 主流程修正：16 条 materiality-topic draft 只保留为议题归并和交叉映射参考；最终 E3.5 核验单元采用 29 条 GRI index-row 3-3 instances。因此最终 current assessment units 目标口径为：

```text
114 ordinary current_gap effective assessments
+ 29 GRI 3-3 index-row instances
= 143 final current disclosure assessment units
```

## 阶段门

通过条件：

- 已基于本地证据索引定位报告重要性评估证据。
- 已形成 29 个 GRI index-row 3-3 instance 草案。
- 每个 index-row instance 均具备 `manifest_item_id`、`standard_id`、`canonical_disclosure_id=3-3`、`index_source_page`、`index_report_page_label`、`index_source_chunk_id`、`mapped_materiality_topic_zh`、`requires_llm_assessment=true`、`initial_status=pending_llm_assessment`。
- 已保留 16 个 materiality topic 作为归并映射，不将其作为最终核验单元计数。
- 已明确原始 PDF、raw artifacts 和 traceability cleanup 文件不被修改。

未通过条件：

- GRI index-row 3-3 instance 数量不是 29，且没有人工逐行复核说明。
- topic instance 缺少可追溯证据页码或 chunk ID。
- 未获 DeepSeek 授权即执行真实 3-3 披露核验。
- 将 `3-3_generic` 作为 ordinary current_gap hard score 条目参与普通评分。
- 在 3-3 effective assessments 完成前执行 unified final advisor 真实生成。

## 输入

- `AGENTS.md`
- `docs/stage_e3/e3_current_scope_acceptance_result.json`
- `docs/stage_e3/e3_current_scope_effective_artifacts.json`
- `data/knowledge_base/manifests/p0_report_evidence_index.json`
- `data/knowledge_base/manifests/p0_gri_requirement_checklist.json`

## 证据定位

主证据：

- 文件：`data/knowledge_base/manifests/p0_report_evidence_index.json`
- PDF 页：15
- 报告页码标注：14
- Chunk ID：`chunk_e5d997720034f27d8de684b9`
- 依据：该 chunk 的“重要性评估”段落说明远景能源通过政策法规解析、ESG 标准研究、利益相关方调研及双因素矩阵分析，在报告期内系统识别、筛选出 16 项 ESG 重要性议题，并在报告中重点披露。

交叉验证证据：

- 文件：`data/knowledge_base/manifests/p0_report_evidence_index.json`
- PDF 页：11
- 报告页码标注：10
- Chunk ID：`chunk_a168baace8b3681e8e04d70e`
- 依据：该 chunk 的“ESG 战略与目标”页按环境、人、治理、产品列示重要性议题、目标和目标达成进展。

## Materiality Topic Crosswalk 草案

草案文件为 `docs/stage_e3_5/e3_5_gri_3_3_topic_scope.json`，共 16 项：

| 序号 | topic_instance_id | 中文议题 | 英文 slug |
|---:|---|---|---|
| 1 | `gri_3_3_topic_001_climate_change` | 应对气候变化 | `climate_change` |
| 2 | `gri_3_3_topic_002_waste_management` | 废弃物管理 | `waste_management` |
| 3 | `gri_3_3_topic_003_energy_management` | 能源管理 | `energy_management` |
| 4 | `gri_3_3_topic_004_biodiversity_and_land_use` | 生物多样性与土地利用 | `biodiversity_and_land_use` |
| 5 | `gri_3_3_topic_005_water_resource_management` | 水资源管理 | `water_resource_management` |
| 6 | `gri_3_3_topic_006_circular_economy` | 循环经济 | `circular_economy` |
| 7 | `gri_3_3_topic_007_occupational_health_and_safety` | 职业健康与安全 | `occupational_health_and_safety` |
| 8 | `gri_3_3_topic_008_human_capital_development` | 人力资本发展 | `human_capital_development` |
| 9 | `gri_3_3_topic_009_labor_and_human_rights` | 劳工与人权 | `labor_and_human_rights` |
| 10 | `gri_3_3_topic_010_socioeconomic_contribution_and_community_relations` | 社会经济贡献与社区关系 | `socioeconomic_contribution_and_community_relations` |
| 11 | `gri_3_3_topic_011_corporate_governance` | 公司治理 | `corporate_governance` |
| 12 | `gri_3_3_topic_012_business_ethics` | 商业道德行为 | `business_ethics` |
| 13 | `gri_3_3_topic_013_data_security_and_privacy_protection` | 数据安全与隐私保护 | `data_security_and_privacy_protection` |
| 14 | `gri_3_3_topic_014_innovation_management` | 创新管理 | `innovation_management` |
| 15 | `gri_3_3_topic_015_product_quality_and_safety` | 产品质量与安全 | `product_quality_and_safety` |
| 16 | `gri_3_3_topic_016_sustainable_supply_chain_management` | 可持续供应链管理 | `sustainable_supply_chain_management` |

该 16 项不作为最终 assessment unit 数量，只作为 29 条 GRI index-row 3-3 instances 的 `mapped_materiality_topic_zh` 交叉映射。

## GRI Index-Row 3-3 Instance 草案

草案文件为 `docs/stage_e3_5/e3_5_gri_3_3_index_instance_scope.json`，共 29 项：

| 序号 | manifest_item_id | 标准 | 索引 PDF 页 | 映射实质性议题 |
|---:|---|---|---:|---|
| 1 | `current_gap:GRI201:3-3` | GRI 201 经济绩效 | 72 | 社会经济贡献与社区关系 |
| 2 | `current_gap:GRI202:3-3` | GRI 202 市场表现 | 72 | 人力资本发展 |
| 3 | `current_gap:GRI203:3-3` | GRI 203 间接经济影响 | 73 | 社会经济贡献与社区关系 |
| 4 | `current_gap:GRI204:3-3` | GRI 204 采购实践 | 73 | 可持续供应链管理 |
| 5 | `current_gap:GRI205:3-3` | GRI 205 反腐败 | 73 | 商业道德行为 |
| 6 | `current_gap:GRI206:3-3` | GRI 206 反竞争行为 | 73 | 商业道德行为 |
| 7 | `current_gap:GRI207:3-3` | GRI 207 税务 | 73 | 公司治理 |
| 8 | `current_gap:GRI301:3-3` | GRI 301 物料 | 73 | 循环经济 |
| 9 | `current_gap:GRI302:3-3` | GRI 302 能源 | 73 | 能源管理 |
| 10 | `current_gap:GRI303:3-3` | GRI 303 水资源和污水 | 74 | 水资源管理 |
| 11 | `current_gap:GRI304:3-3` | GRI 304 生物多样性 | 74 | 生物多样性与土地利用 |
| 12 | `current_gap:GRI305:3-3` | GRI 305 排放 | 74 | 应对气候变化 |
| 13 | `current_gap:GRI306:3-3` | GRI 306 废弃物 | 74 | 废弃物管理 |
| 14 | `current_gap:GRI308:3-3` | GRI 308 供应商环境评估 | 75 | 可持续供应链管理 |
| 15 | `current_gap:GRI401:3-3` | GRI 401 雇佣 | 75 | 人力资本发展 |
| 16 | `current_gap:GRI402:3-3` | GRI 402 劳资关系 | 75 | 劳工与人权 |
| 17 | `current_gap:GRI403:3-3` | GRI 403 职业健康与安全 | 75 | 职业健康与安全 |
| 18 | `current_gap:GRI404:3-3` | GRI 404 培训与教育 | 75 | 人力资本发展 |
| 19 | `current_gap:GRI405:3-3` | GRI 405 多元化与平等机会 | 75 | 劳工与人权 |
| 20 | `current_gap:GRI406:3-3` | GRI 406 反歧视 | 76 | 劳工与人权 |
| 21 | `current_gap:GRI407:3-3` | GRI 407 结社自由与集体谈判 | 76 | 劳工与人权 |
| 22 | `current_gap:GRI408:3-3` | GRI 408 童工 | 76 | 劳工与人权 |
| 23 | `current_gap:GRI409:3-3` | GRI 409 强迫或强制劳动 | 76 | 劳工与人权 |
| 24 | `current_gap:GRI410:3-3` | GRI 410 安保实践 | 76 | 劳工与人权 |
| 25 | `current_gap:GRI413:3-3` | GRI 413 当地社区 | 76 | 社会经济贡献与社区关系 |
| 26 | `current_gap:GRI414:3-3` | GRI 414 供应商社会评估 | 76 | 可持续供应链管理 |
| 27 | `current_gap:GRI416:3-3` | GRI 416 客户健康与安全 | 76 | 产品质量与安全 |
| 28 | `current_gap:GRI417:3-3` | GRI 417 营销与标识 | 76 | 产品质量与安全 |
| 29 | `current_gap:GRI418:3-3` | GRI 418 客户隐私 | 76 | 数据安全与隐私保护 |

## 输出

- `docs/stage_e3_5/e3_5_gri_3_3_topic_instantiation_plan.md`
- `docs/stage_e3_5/e3_5_gri_3_3_topic_scope.json`
- `docs/stage_e3_5/e3_5_gri_3_3_index_instance_scope.json`
- `docs/stage_e3_5/e3_5_gri_3_3_execution_notes.md`

## 验证

最小验证：

- JSON 能被项目 Python 环境解析。
- `topic_instances` 数量等于 16，作为归并映射。
- `instances` 数量等于 29，作为最终 3-3 核验单元草案。
- 每个 index-row instance 的必填字段完整。
- 每个 index-row instance 的 `requires_llm_assessment` 均为 `true`。
- 每个 index-row instance 的 `initial_status` 均为 `pending_llm_assessment`。

扩大验证：

- 人工打开 PDF 第 14 页，对照重要性矩阵和文本抽取结果，确认 16 项议题无 OCR 或布局误读。
- DeepSeek 授权后，对每个 topic instance 执行 GRI 3-3 管理披露核验，输出 topic-level assessment、证据、页码、运行 ID 和人工复核状态。

## 风险与限制

- 重要性矩阵来自 PDF 文本抽取，图表布局会影响议题排序和等级判断；最终使用前需要人工视觉核验。
- 本草案只识别 GRI index-row 3-3 instances 和 materiality topic crosswalk；后续真实核验和 accepted 状态以 `docs/stage_e3_5/e3_5_gri_3_3_execution_notes.md` 与运行包为准。
- 历史限制：未获 DeepSeek 授权前不得真实核验 3-3；该限制已由后续用户授权和 E3.5 真实运行记录解除。
- 当前剩余限制：E3 final evaluation 仍需 traceability cleanup 结果接受或人工豁免，以及 final Advisor 建议人工评测；本计划草案本身不得替代最终披露评分结果。
