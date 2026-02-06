# /envision/fusion/__init__.py
"""融合推理模块 - MVP使用AHP，未来升级为神经符号"""

from .ahp_fusion import AHPFusionEngine
from .rule_engine import RuleEngine

__all__ = ['AHPFusionEngine', 'RuleEngine']