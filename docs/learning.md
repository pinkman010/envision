# ESG智能分析系统 - 学习指南

## 快速入门

### 启动应用
```bash
streamlit run main.py                    # 简洁版
streamlit run main.py -- --mode enhanced # 增强版
# 访问 http://localhost:8501
```

## 架构概览

```
Streamlit UI
    ├── app_simple.py (简洁版)
    └── app_enhanced.py (增强版: 议题全景图/AHP权重/差距诊断/RAG问答)
            ↓
    analysis/ → fusion/ → completion/
            ↓
    core/ (模型) + extraction/ (PDF提取)
            ↓
    Ollama (LLM) + ChromaDB (向量存储)
```

## 代码阅读顺序

1. `main.py` - 入口
2. `src/esg/core/models.py` - 数据模型
3. `src/esg/extraction/pdf_extractor.py` - PDF提取
4. `src/esg/analysis/gap_analyzer.py` - 差距分析
5. `src/esg/fusion/ahp.py` - AHP权重
6. `src/esg/rag/engine.py` - RAG问答

## 核心概念

### ESG评估流程
```
PDF → 指标提取 → 差距分析 → 策略生成 → 报告输出
```

### AHP权重计算
构建判断矩阵 → 特征向量 → 一致性检验(CR<0.1)

### RAG问答
向量化问题 → 相似度检索 → 上下文增强 → LLM生成

## 测试
```bash
python -m pytest src/tests/ -v  # 运行全部测试
```

## 常见问题

**Q: 如何添加新指标？**  
A: 在 `src/esg/config/esg.py` 添加定义 → `metric_extractor.py` 添加提取逻辑

**Q: 如何调试？**  
A: 使用 `import pdb; pdb.set_trace()` 或IDE断点
