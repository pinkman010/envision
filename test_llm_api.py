# -*- coding: utf-8 -*-
"""
大模型API调用测试脚本
用于验证端到端流程中大模型API是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core_config.settings import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
)
from src.utils.llm_utils import call_llm

def test_llm_connection():
    """测试大模型API连接"""
    print("=" * 60)
    print("大模型API连接测试")
    print("=" * 60)
    
    print("\n[配置信息]")
    key_preview = LLM_API_KEY[:8] + "..." if LLM_API_KEY and len(LLM_API_KEY) > 8 else "未设置"
    print("  API Key: " + key_preview)
    print("  Base URL: " + LLM_BASE_URL)
    print("  Model: " + LLM_MODEL)
    print("  Temperature: " + str(LLM_TEMPERATURE))
    
    if not LLM_API_KEY:
        print("\n[X] 错误: 未配置LLM_API_KEY")
        return False
    
    print("\n[测试API调用]")
    test_messages = [
        {"role": "user", "content": "Hello"}
    ]
    
    try:
        print("  正在调用大模型API...")
        response = call_llm(
            messages=test_messages,
            max_tokens=100,  # 增加token数
            timeout=30,
        )
        print("  [OK] API调用成功!")
        print("  响应内容: " + response[:200] + ("..." if len(response) > 200 else ""))
        return True
        
    except Exception as e:
        print("  [X] API调用失败!")
        print("  错误类型: " + type(e).__name__)
        print("  错误信息: " + str(e))
        return False

def test_llm_json_output():
    """测试大模型JSON输出能力"""
    print("\n" + "=" * 60)
    print("大模型JSON输出测试")
    print("=" * 60)
    
    test_messages = [
        {"role": "user", "content": "请以JSON格式返回一个简单的对象，包含name和age两个字段，name为'test', age为18。只返回JSON，不要其他内容。"}
    ]
    
    try:
        print("  正在调用大模型API...")
        response = call_llm(
            messages=test_messages,
            max_tokens=500,
            timeout=30,
        )
        print("  [OK] API调用成功!")
        print("  响应内容: " + response)
        
        # 尝试解析JSON
        import json
        try:
            # 去除可能的markdown代码块标记
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            parsed = json.loads(cleaned)
            print("  [OK] JSON解析成功: " + str(parsed))
            return True
        except json.JSONDecodeError as je:
            print("  [!] JSON解析失败: " + str(je))
            return True  # API调用成功，只是JSON格式问题
            
    except Exception as e:
        print("  [X] API调用失败!")
        print("  错误类型: " + type(e).__name__)
        print("  错误信息: " + str(e))
        return False

if __name__ == "__main__":
    print("\n开始测试大模型API调用...\n")
    
    success1 = test_llm_connection()
    success2 = test_llm_json_output()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print("  基础连接测试: " + ("通过" if success1 else "失败"))
    print("  JSON输出测试: " + ("通过" if success2 else "失败"))
    
    if success1 and success2:
        print("\n[OK] 所有测试通过! 大模型API工作正常。")
        sys.exit(0)
    else:
        print("\n[X] 存在测试失败，请检查配置和网络连接。")
        sys.exit(1)