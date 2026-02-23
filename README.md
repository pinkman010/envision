# 新能源行业ESG披露与沟通智能分析系统 (Envision)

## 项目简介

本项目是为远景能源打造的**强合规、可落地、规则驱动为主、AI辅助为辅**的ESG分析工具，核心是新能源行业ESG专业分析框架落地。

## 核心架构设计

采用**「1+5轻量化Agent混合架构」**：
- **1个总控Agent** (MasterAgent)：固定流程调度、状态跟踪、异常上报
- **5个执行Agent**：
  - CorpusAgent：PDF/Word解析、文本分块、元数据标注
  - ExtractAgent：按预设固定字段提取原文事实+字符级锚点
  - ComplianceAgent：按预设标准做合规风险高亮标注
  - ContentAgent：按固定模板填充人工确认后的结构化数据

## 技术栈

| 分类 | 技术选型 |
|------|----------|
| 核心开发语言 | Python 3.10+ |
| 后端框架 | FastAPI |
| 前端框架 | Streamlit |
| 大模型适配 | 兼容所有OpenAI格式的大模型 |
| 核心工具库 | PyPDF2/python-docx、Jinja2、SQLite |

## 项目结构

```
envision/
├── .env.example              # 环境变量配置示例
├── requirements.txt          # Python依赖
├── streamlit_app.py          # Streamlit前端入口
├── src/
│   ├── main.py               # FastAPI后端入口
│   ├── agent/                # Agent模块
│   ├── api/                  # API路由模块
│   ├── core_config/          # 核心配置
│   ├── ui/                   # Streamlit页面
│   └── utils/                # 工具模块
└── config/
    ├── prompt_templates/     # Prompt模板
    └── rule_templates/       # ESG业务规则
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，填写实际的API密钥等配置
```

### 3. 启动后端服务

```bash
python -m src.main
```

或

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动前端界面

```bash
streamlit run streamlit_app.py
```

## 核心功能

1. **ESG语料管理中心**：上传PDF/Word格式的ESG报告，自动解析和分块
2. **实质性议题分析中心**：AI提取关键信息，字符级溯源，相似度校验
3. **ESG对标分析中心**：多企业ESG指标横向对比（开发中）
4. **披露优化与策略助手**：合规风险提示（仅参考，无决策权限）
5. **审计日志中心**：全链路操作留痕、可追溯（开发中）
6. **规则配置中心**：零代码可视化配置（开发中）
7. **人工复核中心**：AI输出内容人工复核（开发中）

## 合规声明

⚠️ **重要提示**：

1. 本系统的AI输出仅为辅助参考，不构成任何披露建议、投资建议或法律意见
2. 所有用于对外披露的内容，必须经企业ESG团队人工复核确认
3. 企业自行承担使用本系统产生的所有法律责任与披露责任

## 核心合规机制

1. **字符级双向溯源**：AI抽取的所有内容必须绑定原文精确字符起止位置
2. **白盒规则兜底**：所有专业判断、议题匹配、合规判定由纯代码硬规则完成
3. **全链路审计日志**：所有操作永久留痕，带SHA-256哈希防篡改
4. **三重幻觉锁死机制**：输入锁死 → 输出锁死 → 校验锁死
5. **人工最终决策**：所有对外披露内容必须有人工复核留痕

## 许可证

本项目为远景能源MBA整合实践项目，仅供学习和研究使用。
