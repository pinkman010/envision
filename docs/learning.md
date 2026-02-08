# 🎓 ESG智能分析系统 - 学习指南

本指南帮助你从0到1理解项目架构和代码实现。

---

## 📋 目录

1. [项目概述](#项目概述)
2. [学习路线图](#学习路线图)
3. [核心概念](#核心概念)
4. [代码阅读顺序](#代码阅读顺序)
5. [实战练习](#实战练习)
6. [调试技巧](#调试技巧)

---

## 项目概述

### 什么是ESG？
ESG = Environmental（环境）+ Social（社会）+ Governance（治理），是企业可持续发展的三大维度。

### 本项目解决什么问题？
- **PDF报告解析**：自动提取ESG报告中的关键指标
- **智能评分**：基于E/S/G三维度综合评价企业ESG表现
- **差距分析**：对标行业标杆，识别改进空间
- **合规检查**：检查是否符合ISSB/GRI/SASB/TCFD等国际标准
- **AI建议**：基于大模型生成改进策略

### 技术架构
```
Streamlit (Web界面)
    ↓
src/esg/ui/ (界面层)
    ↓
src/esg/analysis/ (分析层) / src/esg/fusion/ (融合层)
    ↓
src/esg/core/ (核心模型) / src/esg/extraction/ (数据提取)
    ↓
src/esg/vector_store/ (向量存储) / src/esg/utils/ (工具)
    ↓
Ollama (本地大模型) / ChromaDB (向量数据库)
```

---

## 学习路线图

### 阶段一：全局理解（第1天）

#### 1.1 阅读文档
```bash
# 按顺序阅读
docs/ARCHITECTURE.md    # 架构设计 - 了解整体结构
README.md               # 项目介绍 - 了解功能特性
docs/DEVELOPMENT.md     # 开发指南 - 了解开发规范
```

#### 1.2 理解入口
```python
# main.py - 应用入口
- 解析命令行参数 (--mode simple/enhanced)
- 初始化 Streamlit 页面配置
- 根据模式渲染不同界面
```

#### 1.3 运行应用
```bash
# 启动简洁版
streamlit run main.py -- --mode simple

# 访问 http://localhost:8501
# 点击各个功能，观察输出
```

### 阶段二：数据模型（第2天）

#### 2.1 核心模型
阅读 `src/esg/core/models.py`：

```python
@dataclass
class ESGMetrics:
    """ESG指标数据类"""
    environmental: Dict[str, Any]   # 环境指标
    social: Dict[str, Any]          # 社会指标
    governance: Dict[str, Any]      # 治理指标
    
@dataclass
class AnalysisResult:
    """分析结果"""
    esg_metrics: ESGMetrics
    gap_analysis: GapResult
    strategies: List[Strategy]
```

#### 2.2 配置系统
阅读 `src/esg/config/`：

```python
# base.py - 基础配置
- PROJECT_ROOT: 项目根目录
- DATA_DIR: 数据目录
- MODELS: LLM模型配置

# esg.py - ESG配置
- ESG_DIMENSIONS: ESG三维度定义
- DEFAULT_SCORE: 默认评分
- GAP_THRESHOLD_HIGH/MEDIUM: 差距阈值

# standards.py - 国际标准
- ISSB_S1_CLAUSES: ISSB S1标准条款
- GRI_STANDARDS_CLAUSES: GRI标准条款
- StandardsManager: 标准管理器
```

### 阶段三：功能模块（第3-5天）

#### 3.1 数据提取模块
阅读 `src/esg/extraction/`：

```python
# pdf_extractor.py
class PDFExtractor:
    """PDF提取器"""
    def extract(self, pdf_path) -> PDFContent:
        # 1. 读取PDF文件
        # 2. 提取文本内容
        # 3. 提取元数据
        # 4. 返回结构化数据

# metric_extractor.py
class MetricExtractor:
    """指标提取器"""
    def extract_metrics(self, text) -> Dict:
        # 1. 使用正则表达式匹配指标
        # 2. 使用LLM提取隐含指标
        # 3. 返回结构化指标数据

# carbon_footprint.py
class CarbonFootprintCalculator:
    """碳足迹计算器"""
    def calculate(self, data) -> CarbonFootprintResult:
        # 1. 计算范围1/2/3排放
        # 2. 计算碳强度
        # 3. 生成减排建议
```

#### 3.2 分析模块
阅读 `src/esg/analysis/`：

```python
# gap_analyzer.py
class GapAnalyzer:
    """差距分析器"""
    def analyze(self, company_data, benchmark_data) -> GapResult:
        # 1. 计算各维度差距
        # 2. 识别高优先级差距
        # 3. 生成可视化数据

# strategy_generator.py
class StrategyGenerator:
    """策略生成器"""
    def generate_strategies(self, gap_result) -> List[Strategy]:
        # 1. 分析差距原因
        # 2. 调用LLM生成改进策略
        # 3. 策略优先级排序

# topic_analyzer.py
class TopicAnalyzer:
    """议题分析器"""
    def analyze_topics(self, report_text) -> TopicAnalysis:
        # 1. 识别ESG议题
        # 2. 评估议题重要性
        # 3. 映射到业务单元
```

#### 3.3 融合模块
阅读 `src/esg/fusion/`：

```python
# ahp.py
class AHPFusionEngine:
    """AHP融合引擎"""
    def calculate_weights(self, comparison_matrix) -> Weights:
        # 1. 计算特征向量
        # 2. 一致性检验
        # 3. 返回权重分配

# rule_engine.py
class RuleEngine:
    """规则引擎"""
    def evaluate(self, context) -> RuleResult:
        # 1. 匹配规则条件
        # 2. 执行规则动作
        # 3. 返回评估结果
```

#### 3.4 RAG模块
阅读 `src/esg/rag/`：

```python
# engine.py
class RAGEngine:
    """RAG引擎"""
    def query(self, question) -> RAGResponse:
        # 1. 向量化问题
        # 2. 检索相关文档
        # 3. 构建Prompt
        # 4. 调用LLM生成回答

# chroma_store.py
class ChromaDBStore:
    """向量存储"""
    def add_documents(self, documents):
        # 1. 文档分块
        # 2. 向量化
        # 3. 存入ChromaDB
```

### 阶段四：用户界面（第6天）

阅读 `src/esg/ui/`：

```python
# app_simple.py - 简洁版
- 上传PDF
- 提取指标
- 显示分析结果

# app_enhanced.py - 增强版
- 议题全景图
- AHP权重配置
- 差距诊断
- RAG问答
```

### 阶段五：测试与调试（第7天）

阅读 `src/tests/`：

```python
# 测试用例组织
test_pdf_extractor.py      # PDF提取测试
test_gap_analyzer.py       # 差距分析测试
test_rag_engine.py         # RAG测试
...
```

---

## 核心概念

### 1. ESG评估流程

```
PDF报告 → 提取指标 → 差距分析 → 生成策略 → 报告输出
   ↓          ↓          ↓          ↓          ↓
extraction  metrics    gap        strategy   report
            extraction analyzer   generator  generator
```

### 2. 数据流向

```
用户上传PDF
    ↓
PDFExtractor.extract()
    ↓
MetricExtractor.extract_metrics()
    ↓
ESGMetrics (结构化数据)
    ↓
GapAnalyzer.analyze()
    ↓
StrategyGenerator.generate_strategies()
    ↓
ReportGenerator.generate()
    ↓
用户查看报告
```

### 3. 关键技术点

#### 3.1 PDF提取
- 使用 `pdfplumber` 提取文本和表格
- 使用正则表达式匹配指标
- 使用LLM提取隐含信息

#### 3.2 差距分析
- 对标行业标杆数据
- 计算各维度得分差距
- 识别高/中/低优先级

#### 3.3 AHP权重计算
- 构建判断矩阵
- 计算特征向量
- 一致性检验（CR < 0.1）

#### 3.4 RAG问答
- 文档向量化存储
- 相似度检索
- 上下文增强生成

---

## 代码阅读顺序

### 推荐顺序（由浅入深）

```
1. main.py                    # 入口，了解整体流程
2. src/esg/core/models.py     # 数据模型
3. src/esg/config/base.py     # 基础配置
4. src/esg/config/esg.py      # ESG配置

5. src/esg/extraction/pdf_extractor.py      # PDF提取
6. src/esg/extraction/metric_extractor.py   # 指标提取

7. src/esg/analysis/gap_analyzer.py         # 差距分析
8. src/esg/analysis/strategy_generator.py   # 策略生成

9. src/esg/fusion/ahp.py                    # AHP权重
10. src/esg/completion/report_generator.py  # 报告生成

11. src/esg/rag/engine.py                   # RAG引擎
12. src/esg/vector_store/chroma_store.py    # 向量存储

13. src/esg/ui/app_simple.py                # 简洁版UI
14. src/esg/ui/app_enhanced.py              # 增强版UI

15. src/tests/test_*.py                     # 测试用例
```

---

## 实战练习

### 练习1：跟踪一次完整的分析流程

```python
# 在 main.py 中设置断点，跟踪：
1. 用户上传PDF
2. PDFExtractor.extract()
3. MetricExtractor.extract_metrics()
4. GapAnalyzer.analyze()
5. StrategyGenerator.generate_strategies()
6. ReportGenerator.generate()
```

### 练习2：修改AHP权重

```python
# 在 src/esg/fusion/ahp.py 中：
1. 修改判断矩阵
2. 观察权重变化
3. 验证一致性检验
```

### 练习3：添加新的ESG指标

```python
# 在 src/esg/config/esg.py 中：
1. 添加新的指标定义
2. 在 metric_extractor.py 中添加提取规则
3. 测试是否能正确提取
```

### 练习4：自定义RAG Prompt

```python
# 在 src/esg/rag/engine.py 中：
1. 修改系统Prompt
2. 观察回答质量变化
3. 优化Prompt模板
```

---

## 调试技巧

### 1. 使用断点调试

```python
# 在关键位置添加断点
import pdb; pdb.set_trace()

# 或使用IDE的断点功能
# 在 VS Code 中点击行号左侧
```

### 2. 打印日志

```python
# 使用项目中已有的性能监控
from src.esg.utils.performance_monitor import track_operation

@track_operation("my_operation")
def my_function():
    pass

# 查看性能统计
from src.esg.utils.performance_monitor import get_monitor
stats = get_monitor().get_statistics("my_operation")
```

### 3. 单元测试

```bash
# 运行单个测试
python -m pytest src/tests/test_pdf_extractor.py -v

# 运行所有测试
python -m pytest src/tests/ -v
```

### 4. 交互式调试

```python
# 启动Python交互式环境
python -i -c "from src.esg import *"

# 手动测试函数
extractor = PDFExtractor()
result = extractor.extract("data/uploads/test.pdf")
print(result)
```

---

## 常见问题

### Q1: 如何快速定位功能对应的代码？

**A**: 使用IDE的全局搜索功能：
- 搜索功能按钮的文字
- 搜索相关的类名或函数名
- 查看调用链

### Q2: 如何理解复杂的算法？

**A**: 
1. 先看输入输出
2. 阅读Docstring
3. 画出流程图
4. 添加print语句跟踪执行过程
5. 阅读相关的单元测试

### Q3: 如何添加新功能？

**A**:
1. 在对应模块创建新类/函数
2. 在 `__init__.py` 中导出
3. 在UI中添加调用
4. 编写单元测试
5. 更新文档

---

## 学习资源

### 推荐阅读顺序

1. **架构层面**：docs/ARCHITECTURE.md
2. **开发规范**：docs/DEVELOPMENT.md
3. **核心代码**：src/esg/core/models.py
4. **功能实现**：src/esg/extraction/, src/esg/analysis/
5. **测试用例**：src/tests/test_*.py

### 外部资源

- [Streamlit文档](https://docs.streamlit.io/) - Web界面开发
- [Pydantic文档](https://docs.pydantic.dev/) - 数据验证
- [ChromaDB文档](https://docs.trychroma.com/) - 向量数据库
- [AHP层次分析法](https://en.wikipedia.org/wiki/Analytic_hierarchy_process) - 权重计算方法

---

## 总结

### 关键学习要点

1. **先整体后局部**：先理解架构，再深入代码
2. **带着问题阅读**：不要一行行读，带着问题找答案
3. **动手实践**：修改代码，观察结果变化
4. **画图辅助**：画出数据流和调用关系
5. **测试验证**：通过测试理解预期行为

### 建议的学习时间分配

- 第1-2天：架构和模型
- 第3-5天：核心功能模块
- 第6天：用户界面
- 第7天：测试和调试

---

祝你学习愉快！如有问题，欢迎随时提问。
