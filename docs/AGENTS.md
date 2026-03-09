# AGENTS.md - ESG披露与沟通智能分析系统 (Envision)

> 本文档面向AI编程助手，提供项目架构、开发规范和操作指南的快速参考。

---

## 项目概述

本项目是为**远景能源**打造的**强合规、可落地、规则驱动为主、AI辅助为辅**的ESG分析工具，专注于新能源行业的ESG披露与沟通智能分析。

### 核心设计原则

1. **规则驱动为主、AI辅助为辅** - 所有专业判断由纯代码硬规则完成，AI仅做工具调用
2. **强合规机制** - 字符级双向溯源、白盒规则兜底、全链路审计日志
3. **三重幻觉锁死** - 输入锁死 → 输出锁死 → 校验锁死
4. **人工最终决策** - 所有对外披露内容必须有人工复核留痕

### 核心架构：1+4轻量化Agent混合架构

- **1个总控Agent** (OrchestratorAgent)：固定流程调度、状态跟踪、异常上报
- **4个执行Agent**：
  - CorpusAgent：PDF/Word解析、文本分块、元数据标注
  - RetrievalAgent：RAG检索 + LLM议题识别（检索standards/和peer_reports/集合）
  - AnalystAgent：差距分析（对照标准+同行对比，输出gap_analysis+peer_comparison）
  - AdvisorAgent：披露建议生成（消费notes_gap和notes_peer字段）

---

## 技术栈

| 分类 | 技术选型 |
|------|----------|
| 核心开发语言 | Python 3.10+ |
| 后端框架 | FastAPI |
| 前端框架 | Streamlit |
| 大模型适配 | 兼容所有OpenAI格式的大模型 |
| 向量数据库 | ChromaDB + Ollama嵌入模型 |
| 数据存储 | SQLite（审计日志）、ChromaDB（语料向量） |
| 文档解析 | PyPDF2、python-docx |
| 模板引擎 | Jinja2 |

---

## 项目结构

```
envision/
├── .env.example              # 环境变量配置示例
├── pyproject.toml           # 项目元数据与构建配置
├── Makefile                 # 常用命令快捷方式
├── environment.yml          # Conda环境配置
├── src/                     # 核心源码
│   ├── main.py              # FastAPI后端入口
│   ├── agent/               # Agent模块（1+4架构实现）
│   │   ├── base_agent.py    # 所有Agent的抽象基类
│   │   ├── orchestrator_agent.py  # 总控调度Agent
│   │   ├── corpus_agent.py  # 语料处理Agent
│   │   ├── retrieval_agent.py     # 议题检索Agent
│   │   ├── analyst_agent.py       # 差距分析Agent
│   │   └── advisor_agent.py       # 优化建议Agent
│   ├── api/                 # API路由模块
│   │   ├── router.py        # 全局总路由注册
│   │   ├── corpus_router.py # 语料处理接口
│   │   ├── retrieval_router.py    # 议题检索接口
│   │   ├── analyst_router.py      # 差距分析接口
│   │   └── advisor_router.py      # 优化建议接口
│   ├── config/         # 核心配置
│   │   ├── settings.py      # 环境变量与配置项
│   │   ├── paths.py         # 全局路径统一配置
│   │   └── logging_utils.py # 日志初始化工具
│   ├── ui/                  # Streamlit前端
│   │   ├── app.py           # Streamlit入口
│   │   ├── components/      # 可复用组件
│   │   └── pages/           # 多页面应用页面
│   │       ├── 01_home.py
│   │       ├── 02_corpus.py
│   │       ├── 03_materiality.py
│   │       ├── 04_analysis.py
│   │       ├── 05_review.py
│   │       ├── 06_benchmarking.py
│   │       ├── 07_audit.py
│   │       └── 08_rules.py
│   └── utils/               # 工具模块
│       ├── exception_utils.py  # 全局异常类
│       ├── file_utils.py       # 文件处理
│       ├── llm_utils.py        # 大模型调用封装
│       ├── validate_utils.py   # 校验工具
│       ├── similarity_utils.py # 相似度计算
│       ├── audit_utils.py      # 审计日志
│       ├── hash_utils.py       # SHA-256哈希
│       ├── config_utils.py     # 配置加载
│       ├── rule_match.py       # 规则匹配
│       └── chroma_utils.py     # Chroma向量库
├── templates/                  # 外置配置（业务规则、模板）
│   ├── prompt_templates/    # Prompt模板（Jinja2）
│   │   ├── corpus_prompt.j2
│   │   ├── retrieval_prompt.j2
│   │   ├── analyst_prompt.j2
│   │   └── advisor_prompt.j2
│   ├── rule_templates/      # ESG业务规则（JSON）
│   │   ├── esg_standards.json
│   │   ├── topic_rules.json
│   │   └── match_rules.json
│   └── export_templates/    # 导出模板
├── data/                    # 数据存储（不上传Git）
│   ├── chroma_db/          # 向量数据库
│   ├── sqlite_db/          # SQLite数据库
│   ├── raw_corpus/         # 原始语料
│   └── export_results/     # 导出结果
├── logs/                    # 运行日志（不上传Git）
├── tmp/                     # 临时文件（不上传Git）
├── demo_data/               # 演示数据
└── scripts/                 # 运维脚本
    └── import_standards.py  # 标准条款导入ChromaDB
```

---

## 构建与运行命令

### 安装依赖

```bash
# 使用pip
pip install -e .

# 或使用Makefile
make install-dev
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，填写LLM_API_KEY等必要配置
```

### 启动服务

```bash
# 启动后端（FastAPI）
make run-api
# 或：uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（Streamlit）
make run-ui
# 或：streamlit run src/ui/app.py
```

---

## 代码规范与开发约定

### 代码风格

- **格式化工具**：Black（行长度100字符）
- **类型检查**：mypy（Python 3.10+）
- **代码检查**：flake8
- **编码规范**：PEP 8

### 命名规范

- 模块/包名：小写 + 下划线（如 `corpus_agent.py`）
- 类名：大驼峰（如 `CorpusAgent`）
- 函数/变量名：小写 + 下划线（如 `extract_text`）
- 常量：全大写（如 `SIMILARITY_THRESHOLD`）
- 私有成员：下划线前缀（如 `_execute`）

### 文档字符串规范

所有模块、类、函数必须包含中文文档字符串：

```python
def example_function(param: str) -> dict:
    """
    函数功能的简要说明
    
    :param param: 参数说明
    :return: 返回值说明
    :raises ValidationException: 异常说明
    """
```

### Agent开发规范

1. **所有Agent必须继承BaseAgent**
2. **禁止在Agent中写业务逻辑** - Agent仅做流程调度，业务判断由纯代码硬规则完成
3. **AI仅做工具调用** - LLM仅用于：事实提取、文本修复、风险标注、模板填充
4. **必须实现`_execute`抽象方法**
5. **必须包含审计日志记录** - 使用`write_audit_log()`
6. **必须使用统一异常类** - 继承`BaseESGException`

### 核心合规机制实现要求

1. **字符级双向溯源**：所有AI抽取内容必须绑定原文精确字符起止位置
2. **相似度校验**：抽取结果与原文相似度必须达到阈值（默认0.98）
3. **全链路审计**：所有操作使用`write_audit_log()`记录，带SHA-256哈希
4. **幻觉拦截**：输入/输出/校验三重锁死机制

---

## 测试策略

### 测试原则

1. **Agent测试重点**：状态流转、异常处理、审计日志记录
2. **工具函数测试**：输入输出边界、异常场景
3. **禁止测试**：LLM输出内容（非确定性）

> 注：当前项目未配置测试框架，如需添加测试请参考 `pyproject.toml` 中的 `dev` 依赖。

---

## 安全与合规注意事项

### API密钥保护

- **永远不要**将真实API密钥提交到Git仓库
- `.env`文件已加入`.gitignore`
- 使用`.env.example`作为配置模板

### 数据安全

- 敏感数据存储在`data/`目录（已加入`.gitignore`）
- 审计日志使用SHA-256哈希防篡改
- 临时文件存储在`tmp/`目录（已加入`.gitignore`）

### 合规声明

⚠️ **AI输出仅为辅助参考**：

1. 本系统的AI输出不构成任何披露建议、投资建议或法律意见
2. 所有用于对外披露的内容，必须经企业ESG团队人工复核确认
3. 企业自行承担使用本系统产生的所有法律责任与披露责任

---

## 环境变量说明

详见`.env.example`文件。关键配置项：

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `LLM_API_KEY` | 是 | 大模型API密钥 |
| `LLM_BASE_URL` | 否 | API基础地址，默认OpenAI |
| `LLM_MODEL` | 否 | 模型名称，默认gpt-4o-mini |
| `SIMILARITY_THRESHOLD` | 否 | 相似度阈值，默认0.98 |
| `API_BASE_URL` | 否 | 前端连接后端地址 |

---

## 常见问题排查

### 前端无法连接后端

1. 检查后端服务是否已启动
2. 检查`.env`中`API_BASE_URL`配置是否正确
3. 检查`ALLOWED_ORIGINS`是否包含前端地址

### 大模型调用失败

1. 检查`LLM_API_KEY`是否配置
2. 检查网络是否能访问`LLM_BASE_URL`
3. 查看日志中的详细错误信息

---

## 相关文档

- `README.md` - 项目简介和快速开始
- `CLAUDE.md` - 项目背景和架构说明
- `docs/部署说明文档.md` - 详细部署指南
- `docs/用户操作手册.md` - 用户使用指南
- `docs/FAQ.md` - 常见问题解答
- `docs/DEV_LOG.md` - 开发日志

---

## 许可证

本项目为远景能源MBA整合实践项目，仅供学习和研究使用。
