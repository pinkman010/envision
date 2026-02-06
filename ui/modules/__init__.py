"""UI模块包

四大功能模块：
- topic_analysis: 议题全景图
- weight_config: 智能权重配置
- gap_analysis: 披露差距诊断
- strategy_generator: AI策略建议
"""

from ui.modules import topic_analysis, weight_config, gap_analysis, strategy_generator

__all__ = ['topic_analysis', 'weight_config', 'gap_analysis', 'strategy_generator']
