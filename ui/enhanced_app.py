"""远景能源 ESG 智能分析系统 - 兼容性入口

此文件保留用于向后兼容。请使用新的入口：
    streamlit run ui/app.py
    
或直接运行：
    streamlit run main_enhanced.py
"""

import warnings
warnings.warn(
    "ui/enhanced_app.py 已弃用，请使用 ui/app.py 或 main_enhanced.py",
    DeprecationWarning,
    stacklevel=2
)

# 转发到新的应用入口
from ui.app import main

if __name__ == "__main__":
    main()
