# 🌿 ESG智能分析系统

基于AI的新能源行业ESG披露与沟通智能分析框架。

## ✨ 功能特性

### 📊 ESG分析模块
- **PDF报告解析**: 自动提取ESG报告文本和指标
- **智能评分**: 基于E/S/G三维度综合评价
- **差距分析**: 对标行业标杆识别改进空间
- **报告生成**: 自动生成Markdown格式分析报告

### ⚖️ AHP权重配置
- **层次分析法**: 科学的权重计算
- **一致性检验**: 自动检测判断矩阵
- **AI建议**: 基于不同视角的权重推荐

### 💬 RAG智能问答
- **本地大模型**: 基于 DeepSeek-R1:7B
- **知识库检索**: ChromaDB向量数据库
- **思维链展示**: 显示模型深度思考过程
- **溯源追踪**: 显示答案来源文档及位置

## 🚀 快速开始

### 环境要求
- Python >= 3.9
- Ollama (本地大模型服务)

### 安装步骤

```bash
# 克隆项目
git clone <项目地址>
cd esg-intelligent-analysis

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置Ollama
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text
ollama serve
```

### 运行应用

```bash
# 默认启动简洁版
streamlit run main.py

# 启动简洁版（显式）
streamlit run main.py -- --mode simple

# 启动增强版
streamlit run main.py -- --mode enhanced
```

访问 http://localhost:8501

## 📁 项目结构

```
envision/
├── main.py                   # 统一入口（简洁版/增强版）
├── requirements.txt          # 依赖清单
├── README.md                # 项目说明
├── .env.example             # 环境变量示例
│
├── src/                     # 源代码
│   ├── config.py            # 全局配置
│   │
│   ├── core/                # 核心模块
│   │   ├── models.py        # 数据模型(ESGMetrics等)
│   │   └── engine.py        # ESG分析引擎
│   │
│   ├── extractor/           # 信息抽取
│   │   ├── pdf_extractor.py # PDF提取器
│   │   └── metric_extractor.py # 指标提取器
│   │
│   ├── fusion/              # 融合推理
│   │   ├── ahp.py           # AHP层次分析法
│   │   └── rule_engine.py   # 规则引擎
│   │
│   ├── completion/          # 补全生成
│   │   ├── data_completion.py # 数据补全
│   │   └── report_generator.py # 报告生成
│   │
│   ├── analysis/            # 分析模块
│   │   ├── topic_analyzer.py   # 议题分析
│   │   ├── gap_analyzer.py     # 差距分析
│   │   └── strategy_generator.py # 策略生成
│   │
│   ├── rag/                 # RAG问答
│   │   ├── engine.py        # RAG引擎
│   │   └── chat_history.py  # 聊天历史
│   │
│   ├── vector_store/        # 向量存储
│   │   ├── chroma_store.py  # ChromaDB实现
│   │   └── document_loader.py # 文档加载
│   │
│   ├── ui/                  # 用户界面
│   │   ├── app_simple.py    # 简洁版UI
│   │   ├── app_enhanced.py  # 增强版UI
│   │   ├── components.py    # UI组件
│   │   └── state.py         # 状态管理
│   │
│   └── utils/               # 工具函数
│       ├── ollama_client.py # Ollama客户端
│       ├── file_utils.py    # 文件工具
│       └── validators.py    # 数据校验
│
├── data/                    # 数据文件
│   ├── raw/                 # 原始数据(PDF)
│   ├── processed/           # 处理后数据
│   ├── mock/                # 模拟数据
│   └── reports/             # 生成报告
│
├── database/                # 数据库存储
│   └── chroma/              # ChromaDB向量库
│
├── tests/                   # 测试文件
└── docs/                    # 文档
```

## 🔧 配置说明

复制 `.env.example` 为 `.env` 并修改：

```bash
# Ollama服务配置
OLLAMA_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# 模型配置
OLLAMA_LLM_MODEL=deepseek-r1:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 前端框架 | Streamlit |
| 可视化 | Plotly, Matplotlib |
| LLM | Ollama (DeepSeek-R1:7B) |
| 向量库 | ChromaDB |
| 嵌入模型 | nomic-embed-text |
| PDF处理 | pdfplumber, PyPDF2 |

## 📝 使用指南

### 简洁版使用
1. 上传ESG报告PDF
2. 点击"提取ESG指标"
3. 点击"执行分析"
4. 查看雷达图和评分
5. 下载分析报告

### 增强版使用
1. **议题全景图**: 查看行业ESG议题热度和趋势
2. **权重配置**: 使用AHP配置E/S/G权重
3. **差距诊断**: 对标行业标杆识别差距
4. **AI策略**: 生成针对性改进策略
5. **智能问答**: 基于知识库回答ESG问题

---

**版本**: demo v1.2.0  
**更新日期**: 2026-02
