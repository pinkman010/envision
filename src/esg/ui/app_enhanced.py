"""增强版ESG分析UI

提供9个模块的高级ESG分析界面：
1. 首页 - 数据导入与概览
2. 议题全景图 - 展示ESG议题热度和趋势
3. 实质性矩阵 - 双重重要性评估
4. 竞争对手分析 - 行业最佳实践对标
5. 权重配置 - AHP层次分析法配置维度权重
6. 差距诊断 - 对标行业标杆进行差距分析
7. AI策略建议 - 基于差距生成改进策略
8. 沟通时机 - 推荐最佳ESG披露时机
9. RAG智能问答 - 基于知识库的AI问答

本模块作为主入口，将各页面模块的渲染函数组合在一起。
为了避免循环依赖，各页面模块使用延迟导入（在函数内部导入）。
"""

# 页面模块导入 - 使用延迟导入避免循环依赖
# 各页面函数的导入在 render_app 中进行


def render_app() -> None:
    """渲染增强版应用"""
    # 导入页面配置和初始化
    from src.esg.ui.app_config import setup_page
    from src.esg.ui.navigation import render_sidebar
    from src.esg.ui.pages import (
        render_competitor_page,
        render_gap_page,
        render_home_page,
        render_materiality_page,
        render_rag_page,
        render_strategies_page,
        render_timing_page,
        render_topics_page,
        render_weights_page,
    )
    from src.esg.ui.state import get_state_manager

    # 页面初始化
    setup_page()

    # 获取配置
    config = render_sidebar()

    # 获取当前页面
    manager = get_state_manager()
    current_page = manager.get_current_page()

    # 路由到对应页面
    if current_page == "home":
        render_home_page(config)
    elif current_page == "topics":
        render_topics_page(config)
    elif current_page == "materiality":
        render_materiality_page(config)
    elif current_page == "competitor":
        render_competitor_page(config)
    elif current_page == "weights":
        render_weights_page(config)
    elif current_page == "gap":
        render_gap_page(config)
    elif current_page == "strategies":
        render_strategies_page(config)
    elif current_page == "timing":
        render_timing_page(config)
    elif current_page == "rag":
        render_rag_page(config)
    else:
        render_home_page(config)


# 直接运行入口
if __name__ == "__main__":
    render_app()
