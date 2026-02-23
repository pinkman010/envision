"""
配置加载工具：统一加载环境变量、JSON配置文件、Prompt模板
无业务耦合，仅做配置读取
"""

import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, BaseLoader, Template

from src.core_config.paths import (
    CONFIG_DIR,
    PROMPT_TEMPLATES_DIR,
    RULE_TEMPLATES_DIR,
)


def load_json_config(file_path: Path) -> Dict[str, Any]:
    """
    加载JSON配置文件
    :param file_path: JSON文件路径
    :return: 配置字典
    """
    if not file_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_topic_rules() -> Dict[str, Any]:
    """加载实质性议题规则配置"""
    return load_json_config(RULE_TEMPLATES_DIR / "topic_rules.json")


def load_esg_standards() -> Dict[str, Any]:
    """加载ESG披露标准配置"""
    return load_json_config(RULE_TEMPLATES_DIR / "esg_standards.json")


def load_match_rules() -> Dict[str, Any]:
    """加载白盒规则匹配配置"""
    return load_json_config(RULE_TEMPLATES_DIR / "match_rules.json")


def load_prompt_template(template_name: str) -> Template:
    """
    加载Prompt模板（支持.j2和.json格式）
    :param template_name: 模板文件名（如extract_prompt.j2或extract_prompt.json）
    :return: Jinja2模板对象
    """
    # 尝试不同的扩展名
    possible_names = [template_name]
    if not template_name.endswith('.j2') and not template_name.endswith('.json'):
        possible_names.extend([f"{template_name}.j2", f"{template_name}.json"])
    
    template_path = None
    for name in possible_names:
        path = PROMPT_TEMPLATES_DIR / name
        if path.exists():
            template_path = path
            break
    
    if not template_path:
        # 如果找不到，尝试直接用传入的名字
        template_path = PROMPT_TEMPLATES_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt模板不存在: {template_name}")
    
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 创建Jinja2模板
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    return env.from_string(content)
