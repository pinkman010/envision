# 开发指南

## 1. 开发环境设置

### 1.1 克隆项目

```bash
git clone <repository-url>
cd envision
```

### 1.2 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 1.3 安装依赖

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 或单独安装
pip install -r requirements.txt
pip install black isort mypy flake8 pytest bandit xenon pre-commit
```

### 1.4 配置pre-commit

```bash
# 安装pre-commit钩子
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

## 2. 代码规范

### 2.1 代码格式化

使用Black进行代码格式化：

```bash
# 格式化所有文件
black .

# 检查格式
black --check .
```

### 2.2 导入排序

使用isort进行导入排序：

```bash
# 排序导入
isort .

# 检查排序
isort --check-only .
```

### 2.3 类型检查

使用mypy进行类型检查：

```bash
mypy src
```

### 2.4 代码检查

使用flake8进行代码检查：

```bash
flake8 src --max-line-length=100
```

### 2.5 安全扫描

使用bandit进行安全扫描：

```bash
bandit -r src
```

### 2.6 复杂度检查

使用xenon检查代码复杂度：

```bash
xenon --max-absolute=15 --max-modules=15 --max-average=A src/
```

## 3. 测试

### 3.1 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行E2E测试
pytest -m e2e

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 3.2 编写测试

```python
import pytest
from src.esg.core.models import ESGMetrics

# 单元测试示例
@pytest.mark.unit
def test_esg_metrics_creation():
    metrics = ESGMetrics(
        environmental={"carbon_emissions": 100},
        social={"employee_count": 1000},
        governance={"board_independence_ratio": 0.8}
    )
    assert metrics.environmental["carbon_emissions"] == 100
    assert metrics.social["employee_count"] == 1000

# 集成测试示例
@pytest.mark.integration
def test_analysis_pipeline():
    # 集成测试代码
    pass

# E2E测试示例
@pytest.mark.e2e
def test_complete_workflow():
    # E2E测试代码
    pass
```

## 4. 代码提交规范

### 4.1 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型说明：**
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式（不影响代码运行的变动）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

**示例：**
```
feat(pdf-extractor): 添加异步PDF提取支持

- 实现AsyncPDFExtractor类
- 支持批量并发处理
- 添加进度回调功能

Closes #123
```

### 4.2 分支策略

- `main`: 主分支，保持稳定
- `develop`: 开发分支，集成新功能
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复分支

## 5. 模块开发指南

### 5.1 创建新模块

1. 在`src/`下创建新目录
2. 添加`__init__.py`文件
3. 编写模块代码
4. 添加类型注解
5. 编写文档字符串
6. 添加测试文件

### 5.2 模块模板

```python
"""模块描述

详细描述模块的功能和使用方法。

Example:
    >>> from src.modules.example import ExampleClass
    >>> example = ExampleClass()
    >>> result = example.do_something()
"""

import logging
from typing import Optional, Dict, Any

# 配置日志
logger = logging.getLogger(__name__)


class ExampleClass:
    """类描述
    
    详细描述类的功能。
    
    Attributes:
        attribute1: 属性1描述
        attribute2: 属性2描述
    
    Example:
        >>> instance = ExampleClass(param1="value")
        >>> instance.method()
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        """初始化
        
        Args:
            param1: 参数1描述
            param2: 参数2描述，默认为None
        """
        self.attribute1 = param1
        self.attribute2 = param2
    
    def method(self, arg: str) -> Dict[str, Any]:
        """方法描述
        
        详细描述方法的功能。
        
        Args:
            arg: 参数描述
            
        Returns:
            返回值描述
            
        Raises:
            ValueError: 当参数无效时
        """
        if not arg:
            raise ValueError("参数不能为空")
        
        # 方法实现
        result = {"key": arg}
        
        logger.debug(f"方法执行完成: {result}")
        return result
```

## 6. 文档编写

### 6.1 文档字符串规范

使用Google风格文档字符串：

```python
def function(param1: int, param2: str) -> bool:
    """简短描述
    
    详细描述（如果需要）
    
    Args:
        param1: 参数1描述
        param2: 参数2描述
        
    Returns:
        返回值描述
        
    Raises:
        ValueError: 当参数无效时
        TypeError: 当类型不匹配时
        
    Example:
        >>> function(1, "test")
        True
    """
    pass
```

### 6.2 生成API文档

```bash
cd docs
make html
```

## 7. 调试技巧

### 7.1 日志配置

```python
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 7.2 性能分析

```python
from src.esg.utils.performance_monitor import track_operation

with track_operation("my_operation") as metric:
    # 你的代码
    pass

# 查看性能统计
from src.esg.utils.performance_monitor import get_monitor
stats = get_monitor().get_statistics("my_operation")
print(stats)
```

## 8. 常见问题

### 8.1 依赖冲突

```bash
# 清理并重新安装
pip uninstall -y -r <(pip freeze)
pip install -e ".[dev]"
```

### 8.2 测试失败

```bash
# 查看详细错误信息
pytest -v --tb=long

# 调试特定测试
pytest -v --pdb test_file.py::test_function
```

### 8.3 类型检查错误

```bash
# 忽略特定模块
mypy src --ignore-missing-imports

# 添加类型忽略注释
# type: ignore
```

## 9. 发布流程

### 9.1 版本更新

1. 更新`pyproject.toml`中的版本号
2. 更新`CHANGELOG.md`
3. 创建Git标签
4. 推送标签触发CI/CD

### 9.2 构建发布

```bash
# 构建包
python -m build

# 上传到PyPI
python -m twine upload dist/*
```

## 10. 获取帮助

- 查看[架构设计文档](./ARCHITECTURE.md)
- 查看[API文档](./api/)
- 提交Issue
- 联系维护团队
