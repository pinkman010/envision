# 常见问题（FAQ）

## 1. 部署与启动

### Q: 当前项目怎么启动？

A: 先创建环境并配置 `.env`，再分别启动后端和前端：

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
streamlit run src/ui/app.py
```

详细步骤见 `docs/部署说明文档.md`。

### Q: 需要哪些外部依赖？

A: 当前实现不依赖 Ollama。默认依赖：

- OpenAI 兼容大模型服务
- SiliconFlow 嵌入服务
- 本地 ChromaDB 持久化目录
- 本地 SQLite 审计日志库

### Q: Python 版本要求是什么？

A: `pyproject.toml` 要求 `Python >=3.10`，仓库自带的 `environment.yml` 使用 `Python 3.13`。

## 2. 配置与模型

### Q: 必填环境变量有哪些？

A: 至少要保证下面几类配置完整：

- 服务基础：`PROJECT_NAME`、`PROJECT_DESCRIPTION`、`VERSION`、`API_PREFIX`
- 运行地址：`ENVIRONMENT`、`HOST`、`PORT`、`API_BASE_URL`、`ALLOWED_ORIGINS`
- 大模型：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`
- 嵌入：`SILICONFLOW_API_KEY`、`EMBEDDING_MODEL`
- 存储：`SQLITE_DB_NAME`、`CHROMA_DB_PERSIST_DIR`

### Q: 嵌入模型可以随便换吗？

A: 不建议。当前仓库默认使用 `BAAI/bge-m3`。如果已经导入过现有知识库或历史语料，改模型会导致向量空间不兼容。

### Q: 系统里的 AI 是怎么接入的？

A: 文本生成走 `LLM_BASE_URL + LLM_API_KEY`，嵌入走 SiliconFlow 的 OpenAI 兼容接口。相关实现见：

- `src/utils/llm_utils.py`
- `src/utils/chroma_utils.py`

## 3. 功能使用

### Q: 支持哪些文件格式？

A: 当前上传入口支持：

- PDF：`.pdf`
- Word：`.docx`、`.doc`
- Excel：`.xlsx`、`.xls`

### Q: 最大文件大小是多少？

A: 由 `.env` 中的 `MAX_FILE_SIZE` 控制，默认示例值是 `52428800`，也就是 `50MB`。

### Q: 议题识别页面需要手动点“开始识别”吗？

A: 不需要。当前页面在拿到 `corpus_result` 后会自动请求 `/retrieval/run`，然后展示识别结果。

### Q: 对标分析现在能用吗？

A: 还不能。前端已有“对标分析”页面，但当前是占位说明；`multi_company_benchmark` 工作流也还是预留接口。

### Q: 规则修改后会立刻生效吗？

A: 会。`RetrievalAgent` 和 `AnalystAgent` 在每次运行前都会重新加载规则或标准配置，规则页面保存后无需重启服务。

## 4. 数据与安全

### Q: 数据保存在什么位置？

A: 当前主要会写入以下目录：

- `data/chroma_db/`：向量库
- `data/raw_corpus/`：原始文本与修复文本
- `data/sqlite_db/audit_log.db`：审计日志
- `data/export_results/`：导出文件

### Q: 数据会不会发送到云端？

A: 分两类：

- 文档、向量库和日志文件默认保存在本地
- 文本片段会发送到你配置的 LLM 服务和嵌入服务

如果你需要完全内网运行，就必须把 `LLM_BASE_URL` 和嵌入服务都换成你自己的兼容部署。

### Q: 如何备份？

A: 至少备份这三部分：

- `.env`
- `data/`
- `templates/rule_templates/`

## 5. 故障排查

### Q: 后端启动直接报错“缺少必需的环境变量”？

A: 说明 `.env` 缺字段。当前 `settings.py` 对多数配置项没有默认兜底，必须补齐。

### Q: 上传文件失败怎么办？

A: 先检查：

1. 文件格式是否受支持
2. 文件大小是否超过限制
3. 文档是否损坏
4. 后端是否正常运行

### Q: 大模型调用失败怎么办？

A: 先检查：

1. `LLM_API_KEY` 是否有效
2. `LLM_BASE_URL` 是否可访问
3. `LLM_MODEL` 是否存在
4. 目标服务是否支持当前请求参数

### Q: 向量库初始化失败怎么办？

A: 先检查：

1. `SILICONFLOW_API_KEY` 是否有效
2. `EMBEDDING_MODEL` 是否正确
3. `data/chroma_db/` 是否可写
4. 到嵌入服务的网络是否正常

### Q: 前端连不上后端怎么办？

A: 先检查：

1. 后端监听地址和端口是否正确
2. `.env` 中 `API_BASE_URL` 是否匹配
3. `.env` 中 `ALLOWED_ORIGINS` 是否包含前端地址

## 6. 扩展与维护

### Q: Prompt 模板在哪里？

A: 当前实际使用的模板在 `templates/prompt_templates/`：

- `corpus_fix_prompt.j2`
- `retrieval_prompt.j2`
- `analyst_prompt.j2`
- `advisor_prompt.j2`
- `rag_extraction_enhancement_prompt.j2`

### Q: 如何添加或修改 ESG 议题？

A: 有两种方式：

- 在“规则配置”页面直接修改
- 手动编辑 `templates/rule_templates/topic_rules.json`

### Q: 如何补充标准条文？

A: 分两层：

- 规则层标准配置：`templates/rule_templates/esg_standards.json`
- 检索层标准知识库：`data/knowledge_base/standards/standards_kb.xlsx`，再用 `scripts/import_standards.py` 导入 Chroma

### Q: 如何新增 Agent？

A: 当前主架构固定为 `Orchestrator + Corpus/Retrieval/Analyst/Advisor`。如果确实要新增：

1. 继承 `BaseAgent`
2. 明确输入输出结构
3. 在 API 或编排层接入
4. 同步更新相关文档和前端流程
