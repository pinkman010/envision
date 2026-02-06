"""Session State管理

集中管理Streamlit session state的初始化和访问。
"""

from typing import Any, Dict, Optional
import streamlit as st


class AppState:
    """应用状态管理器"""
    
    # 默认值配置
    DEFAULTS = {
        'current_module': 0,
        'analysis_year': '2025',
        'benchmark_company': '维斯塔斯',
        'ahp_matrix': None,
        'ahp_weights': None,
        'ahp_cr': None,
        'ai_suggestions': None,
        'perspective': 'balanced',
        'gap_analysis': None,
        'diagnosis': None,
        'strategies': None,
        'ollama_status': False,
        'metrics': None,
        'result': None,
        'show_report': False
    }
    
    @classmethod
    def init(cls) -> None:
        """初始化所有session state变量"""
        for key, value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """获取state值"""
        return st.session_state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """设置state值"""
        st.session_state[key] = value
    
    @classmethod
    def reset_analysis(cls) -> None:
        """重置分析相关状态"""
        analysis_keys = ['gap_analysis', 'diagnosis', 'strategies', 'result']
        for key in analysis_keys:
            st.session_state[key] = None
    
    @classmethod
    def switch_module(cls, module_index: int) -> None:
        """切换模块"""
        st.session_state.current_module = module_index
    
    @classmethod
    def get_current_module(cls) -> int:
        """获取当前模块索引"""
        return cls.get('current_module', 0)
