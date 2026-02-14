# 架构设计文档

## 1. 系统概述

### 1.1 项目简介

ESG智能分析系统是一个基于AI的新能源行业ESG披露与沟通智能分析框架，提供PDF报告解析、智能评分、差距分析、合规检查等功能。

### 1.2 设计目标

- **可扩展性**：模块化设计，易于添加新功能
- **性能**：支持异步处理，多级缓存
- **安全性**：多层安全防护，数据加密
- **可维护性**：清晰的分层，完善的文档

## 2. 架构设计

### 2.1 项目结构（重构后）

```
envision/
├── main.py                    # 应用入口
├── src/                       # 源代码
│   ├── esg/                   # 主包
│   │   ├── extraction/        # 数据提取（合并PDF提取+ESG特性）
│   │   ├── fusion/            # 融合引擎（AHP、规则）
│   │   ├── completion/        # 数据补全、报告生成
│   │   ├── analysis/          # 分析模块（差距、策略、竞争）
│   │   ├── rag/               # RAG问答
│   │   ├── vector_store/      # 向量存储
│   │   ├── config/            # 配置
│   │   ├── core/              # 核心模型
│   │   ├── security/          # 安全模块
│   │   ├── ui/                # 用户界面
│   │   └── utils/             # 工具函数
│   ├── tests/                 # 测试
│   └── scripts/               # 工具脚本
├── data/                      # 数据文件
│   ├── raw/                  # 原始数据
│   ├── mock/                 # 模拟数据
│   ├── reports/              # 下载的报告
│   └── uploads/              # 上传文件
├── storage/                   # 存储
│   └── vector/               # ChromaDB向量库
└── docs/                      # 文档
```

### 2.2 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           入口层                                                     │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────────────────────────────────┐       │
│  │   main.py    │  │ start_windows.py │  │                  配置模块 (src/esg/config/)       │       │
│  │  应用入口     │  │   Windows启动    │  │ base.py, esg.py, standards.py, evaluation.py,     │      │
│  │              │  │                  │  │ communication.py, visualization.py, logging_config│      │
│  └──────────────┘  └──────────────────┘  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           用户界面层                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              Streamlit UI (src/esg/ui/)                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐              │   │
│  │  │ app_simple.py│  │app_enhanced.py│ │  components.py   │  │    state.py      │              │   │
│  │  │  简洁版UI     │  │   增强版UI    │ │   UI组件         │  │    状态管理       │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  └──────────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           应用服务层                                                      │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────────────┐  │
│  │      ESG分析引擎                │  │         RAG引擎                │  │     数据补全与报告生成       │  │
│  │    (src/esg/analysis/)         │  │     (src/esg/rag/)             │  │   (src/esg/completion/)    │  │
│  │                                │  │                                │  │                            │  │
│  │ gap_analyzer.py                │  │ engine.py                      │  │ data_completion.py         │  │
│  │ strategy_generator.py          │  │ chat_history.py                │  │ report_generator.py        │  │
│  │ competitor_analyzer.py         │  │                                │  │                            │  │
│  │ topic_analyzer.py              │  │                                │  │                            │  │
│  │ materiality_matrix.py          │  │                                │  │                            │  │
│  │ business_mapper.py             │  │                                │  │                            │  │
│  │ timing_advisor.py              │  │                                │  │                            │  │
│  │ channel_advisor.py             │  │                                │  │                            │  │
│  │ topic_updater.py               │  │                                │  │                            │  │
│  │ auto_updater.py                │  │                                │  │                            │  │
│  └────────────────────────────────┘  └────────────────────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           核心领域层                                                      │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────────────┐  │
│  │      数据模型                   │  │        合规检查                 │  │       融合计算             │  │
│  │    (src/esg/core/)             │  │    (src/esg/core/)             │  │  (src/esg/fusion/)         │  │
│  │                                │  │                                │  │                            │  │
│  │ models.py                      │  │ compliance_checker.py          │  │ ahp.py                     │  │
│  │ engine.py                      │  │                                │  │ rule_engine.py             │  │
│  │ scoring.py                     │  │                                │  │                            │  │
│  │ constants.py                   │  │                                │  │                            │  │
│  │ cdp_auto_filing.py             │  │                                │  │                            │  │
│  │ climate_scenario.py            │  │                                │  │                            │  │
│  │ sbti_tracker.py                │  │                                │  │                            │  │
│  │ scope3_emissions.py            │  │                                │  │                            │  │
│  └────────────────────────────────┘  └────────────────────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           基础设施层                                                      │
│                                                                                                          │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────────────┐  │
│  │      数据提取                   │  │       向量存储                  │  │      安全模块              │  │
│  │   (src/esg/extraction/)        │  │   (src/esg/vector_store/)      │  │  (src/esg/security/)       │  │
│  │                                │  │                                │  │                            │  │
│  │ pdf_extractor.py               │  │ chroma_store.py                │  │ auth.py                    │  │
│  │ pdf_extractor_async.py         │  │ document_loader.py             │  │ encryption.py              │  │
│  │ metric_extractor.py            │  │                                │  │ csrf.py                    │  │
│  │ carbon_footprint.py            │  │                                │  │                            │  │
│  │ multilingual.py                │  │                                │  │                            │  │
│  └────────────────────────────────┘  └────────────────────────────────┘  └────────────────────────────┘  │
│                                                                                                          │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────────────┐  │
│  │      LLM客户端                  │  │        缓存管理                │  │      性能监控               │  │
│  │  (src/esg/utils/)              │  │  (src/esg/utils/)              │  │  (src/esg/utils/)          │  │
│  │                                │  │                                │  │                            │  │
│  │ ollama_client.py               │  │ cache_manager.py               │  │ performance_monitor.py     │  │
│  └────────────────────────────────┘  └────────────────────────────────┘  └────────────────────────────┘  │
│                                                                                                          │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────────────┐  │
│  │      文件工具                   │  │       HTML净化                 │  │      验证器                 │  │
│  │   (src/esg/utils/)             │  │   (src/esg/utils/)             │  │(src/esg/utils/validators/) │  │
│  │                                │  │                                │  │                            │  │
│  │ file_utils.py                  │  │ html_sanitizer.py              │  │ base.py                    │  │
│  │                                │  │                                │  │ esg_metrics.py             │  │
│  │                                │  │                                │  │ fields.py                  │  │
│  └────────────────────────────────┘  └────────────────────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

#### 2.2.1 核心模块（src/esg/core/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| models.py | 数据模型定义 | ESGMetrics, AnalysisResult, CompanyData |
| engine.py | ESG分析引擎 | ESGAnalysisEngine |
| compliance_checker.py | 合规性检查 | ComplianceChecker |
| constants.py | 常量定义 | ESG常量、阈值 |
| scoring.py | 评分计算 | ScoreCalculator |
| cdp_auto_filing.py | CDP自动申报 | CDPAutoFiler |
| climate_scenario.py | 气候情景分析 | ClimateScenarioAnalyzer |
| sbti_tracker.py | SBTi追踪 | SBTiTracker |
| scope3_emissions.py | 范围3排放计算 | Scope3EmissionsCalculator |

#### 2.2.2 提取模块（src/esg/extraction/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| pdf_extractor.py | PDF文本提取 | PDFExtractor, PDFContent |
| pdf_extractor_async.py | 异步PDF提取 | AsyncPDFExtractor |
| metric_extractor.py | 指标提取 | MetricExtractor |
| carbon_footprint.py | 碳足迹计算 | CarbonFootprintCalculator |
| multilingual.py | 多语言处理 | MultilingualProcessor |

#### 2.2.3 分析模块（src/esg/analysis/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| gap_analyzer.py | 差距分析 | GapAnalyzer |
| business_mapper.py | 业务映射 | BusinessMapper |
| strategy_generator.py | 策略生成 | StrategyGenerator |
| topic_analyzer.py | 议题分析 | TopicAnalyzer |
| competitor_analyzer.py | 竞争分析 | CompetitorAnalyzer |
| auto_updater.py | 自动更新 | AutoUpdater |
| channel_advisor.py | 通道顾问 | ChannelAdvisor |
| materiality_matrix.py | 物质性矩阵 | MaterialityMatrix |
| timing_advisor.py | 时机顾问 | TimingAdvisor |
| topic_updater.py | 主题更新 | TopicUpdater |

#### 2.2.4 RAG模块（src/esg/rag/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| engine.py | RAG引擎 | RAGEngine |
| chat_history.py | 聊天历史 | ChatHistory |

#### 2.2.5 向量存储（src/esg/vector_store/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| chroma_store.py | ChromaDB封装 | ChromaDBStore |
| document_loader.py | 文档加载 | DocumentLoader |

#### 2.2.6 融合模块（src/esg/fusion/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| ahp.py | AHP层次分析法 | AHPFusionEngine |
| rule_engine.py | 规则引擎 | RuleEngine |

#### 2.2.7 补全模块（src/esg/completion/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| data_completion.py | 数据补全 | DataCompleter |
| report_generator.py | 报告生成 | ReportGenerator |

#### 2.2.8 安全模块（src/esg/security/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| auth.py | 认证授权 | AuthManager, User |
| encryption.py | 数据加密 | EncryptionManager |
| csrf.py | CSRF防护 | CSRFProtection |

#### 2.2.9 配置模块（src/esg/config/）

| 模块 | 职责 | 关键类/配置项 |
|------|------|--------|
| base.py | 基础配置 | PROJECT_ROOT, ANALYSIS_YEARS, 版本信息 |
| esg.py | ESG维度配置 | ESG_DIMENSIONS, ESG_COLORS, 指标阈值 |
| standards.py | 标准配置 | ISSB, GRI 标准条款 |
| communication.py | 传播策略 | COMMUNICATION_CALENDAR 沟通日历 |
| evaluation.py | 评估配置 | EVALUATION_PERSPECTIVES, BENCHMARK_COMPANIES |
| visualization.py | 可视化配置 | 图表颜色、主题配置 |
| logging_config.py | 日志配置 | 日志级别、格式 |

#### 2.2.10 UI模块（src/esg/ui/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| app_simple.py | 简洁版UI | SimpleESGApp |
| app_enhanced.py | 增强版UI | EnhancedESGApp |
| components.py | UI组件 | 图表、表格组件 |
| state.py | 状态管理 | AppState |

#### 2.2.11 工具模块（src/esg/utils/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| performance_monitor.py | 性能监控 | PerformanceMonitor |
| cache_manager.py | 缓存管理 | CacheManager |
| ollama_client.py | LLM客户端 | OllamaClient |
| html_sanitizer.py | HTML净化 | HTMLSanitizer |
| validators.py | 数据验证 | 验证函数集 |
| file_utils.py | 文件工具 | 工具函数集 |

#### 2.2.12 验证器子模块（src/esg/utils/validators/）

| 模块 | 职责 | 关键类 |
|------|------|--------|
| base.py | 基础验证器 | BaseValidator |
| esg_metrics.py | ESG指标验证 | ESGMetricsValidator |
| fields.py | 字段验证 | FieldValidator |

## 3. 数据流

### 3.1 ESG分析流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   PDF报告     │───▶│   文本提取   │───▶│   指标提取   │
└──────────────┘    └──────────────┘    └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   报告生成   │◀───│   策略建议   │◀───│   差距分析   │
└──────────────┘    └──────────────┘    └──────────────┘
                                                 ▲
                                                 │
                                         ┌──────────────┐
                                         │   标杆对比   │
                                         └──────────────┘
```

### 3.2 RAG问答流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   用户问题   │───▶│   向量化     │───▶│   向量搜索   │
└──────────────┘    └──────────────┘    └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   展示答案   │◀───│   生成回答   │◀───│   构建提示   │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 4. 技术栈

### 4.1 核心依赖

| 组件 | 技术 | 版本 |
|------|------|------|
| Web框架 | Streamlit | >=1.28.0 |
| 数据处理 | Pandas, NumPy | >=2.0.0, >=1.24.0 |
| 可视化 | Plotly, Matplotlib, WordCloud | >=5.15.0, >=3.7.0, >=1.9.0 |
| PDF处理 | pdfplumber, PyPDF2 | >=0.9.0, >=3.0.0 |
| 文档生成 | python-docx, markdown | >=0.8.11, >=3.5.0 |
| 向量数据库 | ChromaDB | >=0.4.0 |
| LLM服务 | Ollama | - |
| 数据验证 | Pydantic | >=2.0.0 |
| 异步HTTP | aiohttp | >=3.9.0 |
| 异步缓存 | aiocache | >=0.12.0 |
| 密码哈希 | bcrypt | >=4.1.0 |
| 加密 | cryptography | >=41.0.0 |
| 认证 | PyJWT | >=2.8.0 |
| 进度条 | tqdm | >=4.65.0 |
| 监控指标 | prometheus-client | >=0.19.0 |

### 4.2 开发工具

| 工具 | 用途 |
|------|------|
| pytest | 测试框架 |
| pytest-asyncio | 异步测试支持 |
| pytest-cov | 覆盖率报告 |
| pytest-mock | 模拟测试 |
| black | 代码格式化 |
| isort | 导入排序 |
| mypy | 类型检查 |
| flake8 | 代码检查 |
| pylint | 静态代码分析 |
| bandit | 安全扫描 |
| safety | 依赖漏洞扫描 |
| xenon | 复杂度检查 |
| radon | 代码度量 |
| pre-commit | 预提交钩子 |
| sphinx | 文档生成 |

## 5. 安全设计

### 5.1 安全架构

```
┌─────────────────────────────────────────────────────────────┐
│                         安全层                               │
├─────────────────────────────────────────────────────────────┤
│  输入验证  │  权限控制  │  数据加密  │  CSRF防护  │ 审计日志  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 安全措施

1. **输入验证**：所有用户输入经过验证和清理
2. **权限控制**：基于角色的访问控制（RBAC）
3. **数据加密**：敏感数据AES-256加密存储
4. **传输安全**：JWT令牌认证
5. **CSRF防护**：双重提交Cookie模式
6. **审计日志**：记录关键操作

## 6. 性能设计

### 6.1 性能优化策略

1. **异步处理**：PDF提取等IO密集型操作异步化
2. **多级缓存**：内存缓存 + 文件缓存
3. **连接池**：HTTP连接复用
4. **批量处理**：支持批量PDF处理
5. **懒加载**：按需加载资源

### 6.2 监控指标

- 请求响应时间
- PDF提取时间
- 向量搜索时间
- LLM调用时间
- 缓存命中率
- 内存使用率

## 7. 扩展性设计

### 7.1 扩展点

1. **指标提取**：可添加新的提取模式
2. **分析算法**：可集成新的分析算法
3. **报告模板**：可自定义报告格式
4. **数据源**：可添加新的数据源适配器
5. **可视化**：可添加新的图表类型

### 7.2 插件机制

```python
# 示例：自定义指标提取器
from src.extractor.metric_extractor import MetricExtractor

class CustomMetricExtractor(MetricExtractor):
    def extract(self, text: str) -> Dict[str, Any]:
        # 自定义提取逻辑
        return super().extract(text)
```

## 8. 部署架构

### 8.1 开发环境

```
┌─────────────────────────────────────────────────────────────┐
│                      开发工作站                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Docker Compose                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │   App    │  │ Ollama   │  │   ChromaDB       │   │  │
│  │  │          │  │          │  │                  │   │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 生产环境

```
┌─────────────────────────────────────────────────────────────┐
│                       生产环境                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   LB     │  │   App    │  │   App    │  │   App    │  │
│  │ (Nginx)  │  │  Node 1  │  │  Node 2  │  │  Node 3  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐ │
│  │  Redis   │  │ChromaDB  │  │   Ollama Cluster        │ │
│  │ (Cache)  │  │ (Vector) │  │                         │ │
│  └──────────┘  └──────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 9. 开发规范

### 9.1 代码规范

- 遵循PEP 8规范
- 使用类型注解
- 编写文档字符串
- 保持函数简洁（<50行）
- 控制圈复杂度（<15）

### 9.2 测试规范

- 单元测试覆盖率 > 80%
- 集成测试覆盖关键路径
- E2E测试覆盖完整流程
- 性能测试记录基线

### 9.3 文档规范

- 所有公共API都有文档
- 复杂逻辑有注释说明
- 架构变更更新本文档
- 版本发布更新CHANGELOG

## 10. 模块详细说明（v1.3.6）

本节详细列出所有.py文件及其功能说明。

### 10.1 核心模块（src/esg/core/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 核心模块初始化 | - |
| `models.py` | 数据模型定义 | ESGMetrics, AnalysisResult, CompanyData |
| `engine.py` | ESG分析引擎 | ESGAnalysisEngine |
| `compliance_checker.py` | 合规性检查 | ComplianceChecker |
| `constants.py` | 常量定义 | ESG常量、阈值 |
| `scoring.py` | 评分计算 | ScoreCalculator |
| `cdp_auto_filing.py` | CDP自动申报 | CDPAutoFiler |
| `climate_scenario.py` | 气候情景分析 | ClimateScenarioAnalyzer |
| `sbti_tracker.py` | SBTi追踪 | SBTiTracker |
| `scope3_emissions.py` | 范围3排放计算 | Scope3EmissionsCalculator |

### 10.2 提取模块（src/esg/extraction/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 提取模块初始化 | - |
| `pdf_extractor.py` | PDF文本提取 | PDFExtractor, PDFContent |
| `pdf_extractor_async.py` | 异步PDF提取 | AsyncPDFExtractor |
| `metric_extractor.py` | 指标提取 | MetricExtractor |
| `carbon_footprint.py` | 碳足迹计算 | CarbonFootprintCalculator |
| `multilingual.py` | 多语言处理 | MultilingualProcessor |

### 10.3 分析模块（src/esg/analysis/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 分析模块初始化 | - |
| `gap_analyzer.py` | 差距分析 | GapAnalyzer |
| `business_mapper.py` | 业务映射 | BusinessMapper |
| `strategy_generator.py` | 策略生成 | StrategyGenerator |
| `topic_analyzer.py` | 议题分析 | TopicAnalyzer |
| `competitor_analyzer.py` | 竞争分析 | CompetitorAnalyzer |
| `auto_updater.py` | 自动更新 | AutoUpdater |
| `channel_advisor.py` | 通道顾问 | ChannelAdvisor |
| `materiality_matrix.py` | 物质性矩阵 | MaterialityMatrix |
| `timing_advisor.py` | 时机顾问 | TimingAdvisor |
| `topic_updater.py` | 主题更新 | TopicUpdater |

### 10.4 RAG模块（src/esg/rag/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | RAG模块初始化 | - |
| `engine.py` | RAG引擎 | RAGEngine |
| `chat_history.py` | 聊天历史 | ChatHistory |

### 10.5 向量存储（src/esg/vector_store/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 向量存储模块初始化 | - |
| `chroma_store.py` | ChromaDB封装 | ChromaDBStore |
| `document_loader.py` | 文档加载 | DocumentLoader |

### 10.6 融合模块（src/esg/fusion/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 融合模块初始化 | - |
| `ahp.py` | AHP层次分析法 | AHPFusionEngine |
| `rule_engine.py` | 规则引擎 | RuleEngine |

### 10.7 补全模块（src/esg/completion/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 补全模块初始化 | - |
| `data_completion.py` | 数据补全 | DataCompleter |
| `report_generator.py` | 报告生成 | ReportGenerator |

### 10.8 安全模块（src/esg/security/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 安全模块初始化 | - |
| `auth.py` | 认证授权 | AuthManager, User |
| `encryption.py` | 数据加密 | EncryptionManager |
| `csrf.py` | CSRF防护 | CSRFProtection |

### 10.9 配置模块（src/esg/config/）

| 文件 | 职责 | 关键类/配置项 |
|------|------|------------|
| `__init__.py` | 配置模块初始化 | - |
| `base.py` | 基础配置 | PROJECT_ROOT, ANALYSIS_YEARS, 版本信息 |
| `esg.py` | ESG维度配置 | ESG_DIMENSIONS, ESG_COLORS, 指标阈值 |
| `standards.py` | 标准配置 | ISSB, GRI 标准条款 |
| `communication.py` | 传播策略 | COMMUNICATION_CALENDAR 沟通日历 |
| `evaluation.py` | 评估配置 | EVALUATION_PERSPECTIVES, BENCHMARK_COMPANIES |
| `visualization.py` | 可视化配置 | 图表颜色、主题配置 |
| `logging_config.py` | 日志配置 | 日志级别、格式 |

### 10.10 UI模块（src/esg/ui/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | UI模块初始化 | - |
| `app_simple.py` | 简洁版UI | SimpleESGApp |
| `app_enhanced.py` | 增强版UI | EnhancedESGApp |
| `components.py` | UI组件 | 图表、表格组件 |
| `state.py` | 状态管理 | AppState |

### 10.11 工具模块（src/esg/utils/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 工具模块初始化 | - |
| `performance_monitor.py` | 性能监控 | PerformanceMonitor |
| `cache_manager.py` | 缓存管理 | CacheManager |
| `ollama_client.py` | LLM客户端 | OllamaClient |
| `html_sanitizer.py` | HTML净化 | HTMLSanitizer |
| `validators.py` | 数据验证 | 验证函数集 |
| `file_utils.py` | 文件工具 | 工具函数集 |

#### 10.11.1 验证器子模块（src/esg/utils/validators/）

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `__init__.py` | 验证器初始化 | - |
| `base.py` | 基础验证器 | BaseValidator |
| `esg_metrics.py` | ESG指标验证 | ESGMetricsValidator |
| `fields.py` | 字段验证 | FieldValidator |

### 10.12 测试模块（src/tests/）

| 文件 | 职责 |
|------|------|
| `test_competitor_feature.py` | 竞争功能测试 |
| `test_compliance.py` | 合规测试 |
| `test_comprehensive.py` | 综合测试 |
| `test_e2e.py` | 端到端测试 |
| `test_edge_cases.py` | 边界用例测试 |
| `test_exceptions.py` | 异常处理测试 |
| `test_ollama_client.py` | Ollama客户端测试 |
| `test_pdf_extractor.py` | PDF提取测试 |
| `test_rag_engine.py` | RAG引擎测试 |
| `test_topic_updater.py` | 主题更新测试 |
| `test_validators.py` | 验证器测试 |

### 10.13 脚本模块（src/scripts/）

| 文件 | 职责 |
|------|------|
| `check_docstring_coverage.py` | 文档字符串覆盖率检查 |

## 11. 演进路线

### 11.1 短期目标（v1.3）

- [x] 多语言报告支持（中文、英文、繁体中文）
- [x] 数据可视化仪表板
- [ ] API接口完善
- [ ] 更多语言支持（日语、韩语、德语、法语、西班牙语）- 后续版本

### 11.2 中期目标（v2.0）

- [ ] 支持更多ESG标准
- [ ] 机器学习模型集成
- [ ] 实时数据同步

### 11.3 长期目标（v3.0）

- [ ] 区块链存证
- [ ] 行业对比平台
- [ ] 预测性分析

---

**版本**: v1.3.6  
**更新日期**: 2026-02-14
