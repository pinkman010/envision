# 项目背景

上海财经大学MBA整合实践项目，合作企业：远景能源有限公司（Envision Energy）。
**课题**：AI驱动的新能源行业ESG披露与沟通智能分析框架研究

**关键时间节点**：4/18 中期Demo → 6/27 结项交付研究报告+Demo代码

---

# 功能规划

| 阶段 | 功能 | 数据库 | 优先级 |
|------|------|--------|--------|
| 中期 4/18 | 单报告分析（议题识别→差距分析→优化建议） | 披露标准条款库 | P0 |
| 中期 4/18 | 对话窗口（检索问答） | 披露标准条款库 + 实质性议题库 | P1 |
| 结项 6/27 | 行业竞品对标与分析 | 竞品对标数据库 | P2 |
| 结项 6/27 | 披露标准版本差异分析 | 披露政策法规库 | P2 |

**数据库说明**：
- 披露标准条款库：现有`standards_kb`（GRI/ISSB条款，已导入）
- 实质性议题库：从`topic_rules.json`升级而来
- 竞品对标数据库：`peer_reports`集合，自行从官网下载维斯塔斯/西门子歌美飒等友商报告
- 披露政策法规库：在标准条款库基础上补入新旧版本，加`version`字段

---

# 系统架构

## 技术栈
- 语言：Python 3.13.11
- LLM：通过 `LLM_BASE_URL` + `LLM_API_KEY` 配置（见 `.env`）
- 向量数据库：ChromaDB（持久化路径见 `CHROMA_DB_PERSIST_DIR`）
- 嵌入模型：硅基流动 `BAAI/bge-m3`（见 `SILICONFLOW_API_KEY`）
- 前端：Streamlit，后端：FastAPI

## Agent架构（1+4）

```
OrchestratorAgent（总控调度，固定流程状态机）
├── CorpusAgent      # 语料解析与向量化
├── RetrievalAgent   # RAG检索 + LLM议题识别
├── AnalystAgent     # 差距分析
└── AdvisorAgent     # 披露建议生成
```

**工作流**：
- `single_report_analysis`：已实现，P0
- `multi_company_benchmark`：结项实现
- `batch_corpus_processing`：不做

## 关键文件路径
- 总控Agent：`src/agent/orchestrator_agent.py`
- 配置入口：`src/config/settings.py`
- 向量库工具：`src/utils/chroma_utils.py`（`search_standards()`、`search_peer_reports()`）
- 标准条款：`data/knowledge_base/standards/standards_kb.xlsx`
- 议题规则：`templates/rule_templates/topic_rules.json`

---

# 核心约束

- 所有配置从 `.env` 读取，不硬编码密钥或路径
- Agent状态统一用 `AgentState` 枚举管理，异常用 `BaseESGException`
- AI输出仅为辅助参考，所有建议需人工复核
- 不过度工程化，保持最小可用原则

---

# 与第一组对接

**必须确认（2条硬约束）**：
1. 嵌入模型：必须是 `BAAI/bge-m3`，向量空间不兼容无法复用
2. metadata字段名：必须包含 `company`、`year`、`industry`、`topic`，代码直接依赖

**建议确认**：
3. 向量库：最好是ChromaDB，否则需要他们提供原始txt+metadata.csv自行导入

**可自行处理**：
- 集合名称：改代码一行配置即可
- chunk_size：不影响兼容性，建议500~1000字符范围给他们参考

---

# 当前待办

- [ ] 与第一组确认2条硬约束
- [ ] 用远景ESG报告跑通 `single_report_analysis` 端到端
- [ ] 修报错，打磨Streamlit输出展示
- [ ] P0稳了再做对话窗口（P1）
- [ ] 结项前自行整理3-4篇友商报告导入`peer_reports`
