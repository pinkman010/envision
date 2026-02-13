# ESG智能分析系统 - 学习指南

## 快速入门

### 启动应用
```bash
streamlit run main.py                    # 简洁版
streamlit run main.py -- --mode enhanced # 增强版
# 访问 http://localhost:8501
```

## 界面版本

### 简洁版 (app_simple.py)
- 简化流程：上传PDF → 提取指标 → 分析 → 下载报告
- 支持示例数据快速体验（优秀/平均/待改进案例）
- 适合快速上手和基础分析

### 增强版 (app_enhanced.py)
- 完整功能：议题全景图/AHP权重/差距诊断/RAG问答
- 适合深度分析和专业用户

## 架构概览

```
Streamlit UI
    ├── app_simple.py (简洁版)
    └── app_enhanced.py (增强版)
            ↓
    analysis/ → fusion/ → completion/
            ↓
    core/ (模型) + extraction/ (PDF提取)
            ↓
    Ollama (LLM) + ChromaDB (向量存储)
```

## 代码阅读顺序

1. `main.py` - 入口
2. `src/esg/ui/app_simple.py` - 简洁版UI
3. `src/esg/ui/app_enhanced.py` - 增强版UI
4. `src/esg/core/models.py` - 数据模型
5. `src/esg/extraction/pdf_extractor.py` - PDF提取
6. `src/esg/extraction/metric_extractor.py` - 指标提取
7. `src/esg/analysis/gap_analyzer.py` - 差距分析
8. `src/esg/analysis/strategy_generator.py` - 策略生成
9. `src/esg/fusion/ahp.py` - AHP权重
10. `src/esg/rag/engine.py` - RAG问答
11. `src/esg/ui/state.py` - 状态管理

## 核心概念

### ESG评估流程
```
PDF → 文本提取 → 指标提取 → 差距分析 → 策略生成 → 报告输出
```

### 示例数据
简洁版提供三种示例数据：
- 🌟 优秀案例：绿色能源集团（碳排放50000吨，可再生能源85%）
- 📊 平均案例：新能源科技有限公司（碳排放150000吨，可再生能源45%）
- ⚠️ 待改进案例：传统能源企业（碳排放500000吨，可再生能源15%）

### AHP权重计算
构建判断矩阵 → 特征向量 → 一致性检验(CR<0.1)

### RAG问答
向量化问题 → 相似度检索 → 上下文增强 → LLM生成

## 测试
```bash
python -m pytest src/tests/ -v        # 运行全部测试
python -m pytest src/tests/ -m unit  # 仅单元测试
python -m pytest src/tests/ -m e2e   # 端到端测试
```

## 常见问题

**Q: 如何添加新指标？**  
A: 在 `src/esg/config/esg.py` 添加定义 → `metric_extractor.py` 添加提取逻辑

**Q: 如何调试？**  
A: 使用 `import pdb; pdb.set_trace()` 或IDE断点

**Q: 示例数据按钮消失怎么办？**  
A: 使用"重新开始"按钮重置状态，系统会自动处理缓存
