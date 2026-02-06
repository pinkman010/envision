# 项目结构迁移指南

## 旧结构 → 新结构映射

| 旧文件路径 | 新文件路径 | 说明 |
|-----------|-----------|------|
| `main.py` | `app.py` | 主应用入口简化 |
| `core/data_models.py` | `src/models/esg.py` | 数据模型归类 |
| `core/esg_engine.py` | `src/services/esg_analysis.py` | 分析服务化 |
| `core/rag_engine.py` | `src/services/rag.py` | RAG服务化 |
| `fusion/ahp_fusion.py` | `src/services/ahp.py` | AHP服务化 |
| `vector_db/chroma_store.py` | `src/services/vector_store.py` | 向量存储服务化 |
| `extractor/pdf_extractor.py` | `src/extractors/pdf.py` | 提取器归类 |
| `extractor/metric_extractor.py` | `src/extractors/metrics.py` | 提取器归类 |
| `completion/report_generator.py` | `src/generators/report.py` | 生成器归类 |
| `utils/ollama_utils.py` | `src/utils/ollama.py` | 工具归类 |
| `utils/file_utils.py` | `src/utils/file.py` | 工具归类 |
| `chroma_db/` | `database/chroma/` | 数据库存储分离 |
| `data/` (根目录) | `data/raw/`, `data/processed/` | 数据分层 |

## 主要改进

### 1. 命名规范化
- 使用简短准确的文件名
- 统一使用小写+下划线命名
- 去除冗余后缀如 `_utils`, `_engine`

### 2. 目录结构清晰
```
src/              # 源代码
├── models/       # 数据模型
├── services/     # 业务逻辑
├── extractors/   # 数据提取
├── generators/   # 内容生成
└── utils/        # 工具函数

data/             # 数据文件
├── raw/          # 原始数据
├── processed/    # 处理后数据
└── mock/         # 模拟数据

database/         # 数据库存储
└── chroma/       # ChromaDB向量库
```

### 3. 源码与数据分离
- 所有代码放在 `src/`
- 所有数据放在 `data/` 和 `database/`
- 配置集中管理

### 4. 根目录简化
```
envision/
├── app.py              # 唯一入口
├── requirements.txt    # 依赖清单
├── README.md          # 项目说明
├── .env.example       # 环境变量示例
├── src/               # 源代码
├── data/              # 数据文件
├── database/          # 数据库存储
└── docs/              # 文档
```

## 迁移步骤

1. 备份旧项目
2. 创建新目录结构
3. 按映射表迁移文件
4. 更新导入语句
5. 测试功能完整性
