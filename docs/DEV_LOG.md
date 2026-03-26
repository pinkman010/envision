# 开发日志（DEV_LOG）

## 2026-03-26 当前状态快照

本文件记录当前仓库的实现状态，不再沿用早期的旧模块命名。

## 1. 当前已落地能力

### 1.1 单报告分析主链路

已实现并可从前端串起来的主流程：

`CorpusAgent -> RetrievalAgent -> AnalystAgent -> AdvisorAgent`

对应能力：

- 报告解析与分块
- 议题识别与知识库检索
- 差距分析
- 优化建议生成
- 人工复核导出

### 1.2 审计与规则管理

当前已经具备：

- 审计日志写入、查询、导出、哈希校验
- 规则页面可视化编辑
- 规则备份与恢复

### 1.3 知识库导入

当前仓库中可用的导入脚本：

- `scripts/import_standards.py`
- `scripts/import_peer_reports.py`

## 2. 当前架构结论

### 2.1 Agent 架构

当前架构是 `1 + 4`：

```text
OrchestratorAgent
├── CorpusAgent
├── RetrievalAgent
├── AnalystAgent
└── AdvisorAgent
```

### 2.2 已废弃的旧命名

以下命名不应再被视为当前模块：

- `ExtractAgent`
- `ComplianceAgent`
- `ContentAgent`
- `MasterAgent`

如果在仓库中看到这些名字，通常是历史注释、旧文档或迁移说明。

## 3. 当前技术栈

- Python `>=3.10`，推荐按 `environment.yml` 使用 `3.13`
- 前端：Streamlit
- 后端：FastAPI
- LLM：OpenAI 兼容接口
- 向量库：ChromaDB
- 嵌入模型：SiliconFlow `BAAI/bge-m3`
- 审计存储：SQLite

## 4. 当前前端状态

### 4.1 已可用页面

- 首页概览
- 报告上传
- 议题识别
- 差距分析
- 人工复核
- 审计日志
- 规则配置

### 4.2 占位页面

- 对标分析：页面已存在，但当前是规划说明，不是已实现能力

### 4.3 页面行为说明

- 首页核心指标是静态演示值
- 议题识别页在已有 `corpus_result` 时会自动发起检索
- 差距分析与建议生成目前仍由用户在页面手动点击触发

## 5. 当前数据层状态

### 5.1 本地持久化

当前运行时会使用：

- `data/chroma_db/`
- `data/raw_corpus/`
- `data/sqlite_db/audit_log.db`
- `data/export_results/`

### 5.2 知识库目录

当前知识库材料位于：

- `data/knowledge_base/standards/`
- `data/knowledge_base/peer_reports/`
- `data/knowledge_base/topic_taxonomy/`

## 6. 当前未完成项

以下功能仍未真正落地：

- 多企业对标工作流
- 对话式检索问答
- 披露标准版本差异分析

## 7. 本次文档同步说明

本轮已完成以下同步动作：

- 重写部署说明文档
- 重写 FAQ
- 重写用户操作手册
- 重写项目模型说明文档
- 重写项目专用 AGENTS 文档
- 删除两份与当前实现不一致的历史文档

后续如果再次调整架构、环境变量或前端行为，应优先更新文档，避免继续积累“文档比代码老一代”的问题。
