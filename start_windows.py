"""Windows平台启动脚本

解决PYTHONPATH和模块导入问题，提供一键启动功能。
"""

import sys
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_environment():
    """设置运行环境"""
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    
    # 添加项目根目录到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 添加src目录到Python路径
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)
    
    logger.info(f"✅ 环境设置完成")
    logger.info(f"   项目根目录: {project_root}")
    logger.info(f"   Python路径: {sys.path[:2]}")


def run_streamlit(mode="simple"):
    """运行Streamlit应用"""
    import subprocess
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "main.py",
        "--", "--mode", mode
    ]
    
    logger.info(f"\n🚀 启动ESG智能分析系统 ({mode}模式)...\n")
    subprocess.run(cmd, cwd=str(Path(__file__).parent))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ESG智能分析系统 - Windows启动器")
    parser.add_argument(
        "--mode",
        choices=["simple", "enhanced"],
        default="enhanced",
        help="运行模式: simple(简洁版) 或 enhanced(增强版)"
    )
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 运行应用
    run_streamlit(args.mode)
