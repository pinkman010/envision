"""增强版主入口

启动重构后的ESG智能分析系统。
"""

import sys
import os

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入重构后的应用
from ui.app import main

if __name__ == "__main__":
    main()
