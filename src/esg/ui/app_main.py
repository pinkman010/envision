"""增强版ESG分析UI（简化版）

提供简化的ESG分析界面：
1. 首页 - 数据导入与概览
2. 差距诊断 - 对标行业标杆进行差距分析

简化版：只导入和路由home和gap页面
"""

# 页面模块导入 - 使用延迟导入避免循环依赖


def render_app() -> None:
    """渲染增强版应用（简化版）"""
    # 导入页面配置和初始化
    from src.esg.ui.app_config import setup_page
    from src.esg.ui.gap import render_gap_page
    from src.esg.ui.home import render_home_page
    from src.esg.ui.navigation import render_sidebar
    from src.esg.ui.state import get_state_manager

    # 页面初始化
    setup_page()

    # 获取配置
    config = render_sidebar()

    # 获取当前页面
    manager = get_state_manager()
    current_page = manager.get_current_page()

    # 路由到对应页面（简化版：只路由home和gap）
    if current_page == "home":
        render_home_page(config)
    elif current_page == "gap":
        render_gap_page(config)
    else:
        # 默认显示首页
        render_home_page(config)


# 直接运行入口
if __name__ == "__main__":
    render_app()
