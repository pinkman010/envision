# AGENTS.md - Envision 项目专用说明

> 本文档面向在本仓库中工作的 AI 编程助手，目标是快速建立当前实现的真实上下文，避免继续沿用旧架构或旧文档说法。

## 1. 先看什么

进入仓库后，优先查看：

1. `README.md`
2. `src/main.py`
3. `src/agent/orchestrator_agent.py`
4. `src/ui/app.py`
5. `src/config/settings.py`

## 2. 当前真实架构

本项目当前是 `1 + 4` Agent 架构：

```text
OrchestratorAgent
├── CorpusAgent
├── RetrievalAgent
├── AnalystAgent
└── AdvisorAgent
```

不要再把以下旧模块当成当前实现：

- `ExtractAgent`
- `ComplianceAgent`
- `ContentAgent`
- `MasterAgent`

这些名称只可能出现在旧文档、注释迁移说明或历史产物中。

## 3. 当前主流程

当前唯一完整打通的流程是：

`single_report_analysis`

执行顺序固定：

1. 语料处理
2. 议题识别与知识库检索
3. 差距分析
4. 优化建议生成

下面两个流程仍是预留接口，不要在文档或实现里误写成已可用：

- `multi_company_benchmark`
- `batch_corpus_processing`

## 4. 模型与外部依赖

当前默认依赖：

- OpenAI 兼容 LLM 接口
- SiliconFlow 嵌入接口
- ChromaDB
- SQLite

不要再把下面这些写成当前默认方案：

- Ollama
- `nomic-embed-text`
- 本地离线嵌入为唯一模式

当前向量兼容性约束：

- 嵌入模型默认是 `BAAI/bge-m3`
- 如果涉及已有向量库复用，不要随意修改嵌入模型

## 5. 关键目录

```text
src/
├── agent/                  # Agent 实现
├── api/                    # FastAPI 路由
├── config/                 # 配置与路径
├── ui/                     # Streamlit 应用
└── utils/                  # Chroma、LLM、审计、规则等工具

templates/
├── prompt_templates/       # Prompt 模板
├── rule_templates/         # 规则配置
└── export_templates/       # 导出模板

data/
├── knowledge_base/         # 标准与同行材料
├── chroma_db/              # 向量库
├── raw_corpus/             # 原始/修复文本
├── sqlite_db/              # 审计日志
└── export_results/         # 导出文件
```

## 6. 文档同步要求

如果改动了以下内容，必须同步更新用户文档：

- 启动方式
- 环境变量
- 上传支持格式
- 页面名称或页面行为
- Agent 架构
- 标准库或同行案例导入方式

尤其注意：

- 首页核心指标目前是静态演示值，不是实时统计
- 对标分析页目前是占位说明，不是已完成能力
- 议题识别页当前是自动触发，不是手动点击开始

## 7. 规则与知识库

当前规则文件：

- `templates/rule_templates/topic_rules.json`
- `templates/rule_templates/esg_standards.json`
- `templates/rule_templates/match_rules.json`
- `templates/rule_templates/esg_indicators.json`
- `templates/rule_templates/unit_conversions.json`

当前 Prompt 文件：

- `templates/prompt_templates/corpus_fix_prompt.j2`
- `templates/prompt_templates/retrieval_prompt.j2`
- `templates/prompt_templates/analyst_prompt.j2`
- `templates/prompt_templates/advisor_prompt.j2`
- `templates/prompt_templates/rag_extraction_enhancement_prompt.j2`

修改规则或 Prompt 时，优先保持输入输出结构稳定。

## 8. 导入数据时的约束

如果你修改同行报告或知识库导入逻辑，优先保留以下 metadata：

- `company`
- `year`
- `industry`
- `topic`

这是当前 `peer_reports` 检索和后续对标兼容性的最低要求。

## 9. 验证策略

当前仓库没有 `tests/` 目录，做改动时优先采用最小验证：

1. 与改动最相关的页面或模块能否正常导入
2. 路径、文件名、环境变量名是否和代码一致
3. 文档中的命令、端口、接口地址是否和当前实现一致

如果你删除或移动文档文件，顺手清理 README 和交叉引用，避免留下坏链接。
