# -*- coding: utf-8 -*-
"""
系统环境检查脚本
检查：Python环境 → 依赖包 → Ollama服务 → 模型 → 知识库

运行方法: python test_system.py
"""
import sys
import os

print("=" * 60)
print("🔍 ESG 智能助手 - 系统检查")
print("=" * 60)

# 记录是否全部通过
all_passed = True


# ========== 1. Python 环境 ==========
print("\n【1】Python 环境")
print("-" * 40)
print(f"  路径: {sys.executable}")
print(f"  版本: {sys.version.split()[0]}")

# 检查版本
version = sys.version_info
if version.major == 3 and version.minor >= 9:
    print("  ✅ Python 版本符合要求 (>=3.9)")
else:
    print("  ⚠️ 建议使用 Python 3.9+")


# ========== 2. 依赖包检查 ==========
print("\n【2】依赖包检查")
print("-" * 40)

packages = {
    "streamlit": "Web界面",
    "langchain": "LangChain框架",
    "langchain_community": "LangChain社区包",
    "chromadb": "向量数据库",
    "requests": "HTTP请求",
    "pypdf": "PDF解析",
}

for pkg, desc in packages.items():
    try:
        __import__(pkg)
        print(f"  ✅ {pkg:25} ({desc})")
    except ImportError:
        print(f"  ❌ {pkg:25} ({desc}) - 未安装")
        all_passed = False


# ========== 3. Ollama 服务 ==========
print("\n【3】Ollama 服务")
print("-" * 40)

import requests

ollama_ok = False
try:
    resp = requests.get("http://localhost:11434", timeout=3)
    print("  ✅ Ollama 服务运行中")
    ollama_ok = True
except:
    print("  ❌ Ollama 未运行")
    print("     请运行: ollama serve")
    all_passed = False


# ========== 4. 模型检查 ==========
print("\n【4】模型检查")
print("-" * 40)

required_models = ["deepseek-r1:1.5b", "nomic-embed-text"]

if ollama_ok:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        installed = [m["name"] for m in resp.json().get("models", [])]
        
        for model in required_models:
            found = any(model in m for m in installed)
            if found:
                print(f"  ✅ {model}")
            else:
                print(f"  ❌ {model} - 未安装")
                print(f"     运行: ollama pull {model}")
                all_passed = False
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        all_passed = False
else:
    print("  ⏭️ 跳过（Ollama未运行）")


# ========== 5. 项目文件 ==========
print("\n【5】项目文件")
print("-" * 40)

project_root = os.path.dirname(os.path.abspath(__file__))
required_files = [
    "app.py",
    "scripts/ollama_utils.py",
    "scripts/rag_system.py",
    "scripts/create_vector_db.py",
]

for f in required_files:
    path = os.path.join(project_root, f)
    if os.path.exists(path):
        print(f"  ✅ {f}")
    else:
        print(f"  ❌ {f} - 不存在")
        all_passed = False


# ========== 6. 数据目录 ==========
print("\n【6】数据目录")
print("-" * 40)

data_path = os.path.join(project_root, "data")
db_path = os.path.join(project_root, "vector_db")

# data 目录
if os.path.exists(data_path):
    pdfs = [f for f in os.listdir(data_path) if f.endswith('.pdf')]
    print(f"  ✅ data/ 目录 ({len(pdfs)} 个PDF)")
else:
    print(f"  ⚠️ data/ 目录不存在，请创建并放入PDF")

# vector_db 目录
if os.path.exists(db_path) and os.listdir(db_path):
    print(f"  ✅ vector_db/ 知识库已创建")
else:
    print(f"  ⚠️ vector_db/ 未创建")
    print(f"     运行: python scripts/create_vector_db.py")


# ========== 7. 快速功能测试 ==========
print("\n【7】快速功能测试")
print("-" * 40)

if ollama_ok:
    try:
        # 测试嵌入模型
        resp = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": "测试"},
            timeout=30
        )
        if resp.status_code == 200:
            vec_dim = len(resp.json()["embedding"])
            print(f"  ✅ 嵌入模型正常 (维度: {vec_dim})")
        else:
            print(f"  ❌ 嵌入模型异常: {resp.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 嵌入测试失败: {e}")
        all_passed = False
    
    try:
        # 测试对话模型
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "deepseek-r1:1.5b", "prompt": "你好", "stream": False},
            timeout=60
        )
        if resp.status_code == 200:
            print(f"  ✅ 对话模型正常")
        else:
            print(f"  ❌ 对话模型异常: {resp.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 对话测试失败: {e}")
        all_passed = False
else:
    print("  ⏭️ 跳过（Ollama未运行）")


# ========== 总结 ==========
print("\n" + "=" * 60)
if all_passed:
    print("✅ 所有检查通过！")
    print("\n可以运行: streamlit run app.py")
else:
    print("⚠️ 存在问题，请根据提示解决")
print("=" * 60)