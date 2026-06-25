# Agent Prompt与Schema约束说明

## 材料性质

本说明用于记录远景能源ESG分析原型中多Agent链路的Prompt设计和Schema约束方式，作为ESRS/GRI标准解析、报告证据匹配、披露差距判断和补充建议生成的过程性依据。该材料服务于课程整合实践Demo说明，不代表企业级生产系统已经上线。

## 方法口径

项目参考CO-STAR的结构化提示思路，将每个Agent的上下文、任务目标、输出格式和约束条件显式写入Prompt；同时结合Schema/Guardrails约束输出字段、证据纪律和人工复核标记，降低自由生成、无证据判断和格式漂移风险。

本项目采用自定义多Agent分工原型，未依赖外部多Agent编排框架。多Agent链路的目标是验证结构化分析结果能否被生成，并进一步进入前端DemoDataset数据契约，由前端看板展示和复核。

## 多Agent职责分工

| Agent | 主要职责 | 核心输入 | 核心输出 | 约束重点 |
|---|---|---|---|---|
| OrchestratorAgent | 任务编排、批次管理、结果聚合 | 任务参数、批次信息、各Agent中间结果 | 聚合后的AgentRunResult | 不直接生成业务结论，保留各阶段来源 |
| CorpusAgent | 报告语料解析、证据片段整理、页码和来源保留 | 企业ESG报告、竞对报告、解析配置 | EvidenceChunk | 不编造页码、章节或报告事实 |
| RetrievalAgent | 议题识别、ESRS/GRI条款召回、候选匹配生成 | RequirementPack、EvidenceChunk、议题映射 | 候选条款与证据匹配结果 | 保留标准来源和证据来源，证据不足标记复核 |
| AnalystAgent | 披露状态、差距等级、证据充分性初判 | 条款要求、报告证据、候选匹配结果 | DisclosureGap | 只有存在明确证据时判定已披露，证据不足时保守处理 |
| AdvisorAgent | 补充披露建议生成、人工确认事项标记 | DisclosureGap、企业议题、业务约束 | 建议文本与reviewFlag | 建议不得写成企业已完成事实，不替代正式披露文本 |

## Prompt约束

### Context

每次任务需要明确公司名称、行业、报告年度、标准范围、批次编号、报告语言、处理对象和当前任务阶段。上下文只用于限定分析范围，不作为企业事实来源。

### Objective

每个Agent只完成自身职责。CorpusAgent只整理证据，RetrievalAgent只召回和匹配候选条款，AnalystAgent只做覆盖状态和差距等级初判，AdvisorAgent只生成辅助建议，OrchestratorAgent只负责编排和聚合。

### Response

Agent输出应为结构化结果，不输出无关前言、泛泛总结或无法进入后续数据契约的自由文本。输出结果应简洁、审慎、可追溯。

### Evidence Rules

- 不编造页码、章节、KPI、管理动作或企业事实。
- 只有存在明确、直接、可定位的报告证据时，才能判定已披露。
- 语义近似但证据不完整时，应判定为部分披露或标记人工复核。
- 证据不足、标准适用性不清或来源定位不清时，必须设置reviewFlag。
- 外部舆情只作为风险信号，不直接决定ESRS/GRI披露符合性。

### Output Rules

输出字段必须能够进入前端DemoDataset或中间结构。关键字段包括标准来源、条款编号、议题、ESG维度、披露属性、披露状态、差距等级、当前披露、证据片段、来源页码、补充建议、优先级和人工复核标记。

## System Prompt与Task Prompt双层结构

多Agent链路采用双层Prompt设计。System Prompt用于固定角色、职责边界、证据纪律和输出要求；Task Prompt用于注入运行时变量，例如companyName、reportYear、batchId、标准条目、检索片段、报告证据和企业议题。

示例结构如下：

```text
System Prompt:
你是ESG分析链路中的[AgentName]。
你的职责是[职责边界]。
你只能基于输入材料和检索证据输出。
你必须输出结构化结果。
证据不足时必须标记人工复核。

Task Prompt:
【任务背景】
companyName: {{companyName}}
reportYear: {{reportYear}}
standardScope: {{standardScope}}
batchId: {{batchId}}

【输入材料】
{{inputJson}}

【输出字段】
{{schemaFields}}

【补充约束】
不编造事实；不输出无关解释；结论必须可追溯到证据。
```

## 与前端DemoDataset的关系

多Agent链路输出不是直接面向最终用户的自由文本，而是被整理为前端可读取的结构化数据。前端DemoDataset中的standards、policyDisclosureAnalysis、materialityBenchmark、publicOpinion和auditTrail分别承接标准条款、披露差距、竞对议题、舆情信号和复核记录。前端看板基于这些字段进行展示、筛选、证据追溯和人工复核。

## 正式化处理说明

原始过程性Prompt文件中存在临时占位和部分早期MVP边界限制。本说明已将标准范围正式化为ESRS/GRI披露标准，并删除与当前Demo不一致的过程性限制。正文报告中只引用结构化Prompt与Schema约束方法，不直接引用过程性文件路径。

## 逐Agent Prompt与Schema模板

除本说明中的总纲约束外，项目进一步形成了逐Agent Prompt与Schema模板，分别约束OrchestratorAgent、CorpusAgent、RetrievalAgent、AnalystAgent和AdvisorAgent的System Prompt、Task Prompt、输入字段、输出字段和Guardrails。详细模板见同目录下的`Agent详细Prompt与Schema模板.md`，机器可读字段约束见`agent_specific_schemas.json`。
