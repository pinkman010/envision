# -*- coding: utf-8 -*-
"""
GPU 诊断脚本
检查 NVIDIA 驱动和 Ollama GPU 状态

运行方法: python check_gpu.py
"""
import subprocess
import requests
import os

print("=" * 60)
print("🔍 GPU 诊断")
print("=" * 60)


# ========== 1. NVIDIA 驱动 ==========
print("\n【1】NVIDIA 驱动")
print("-" * 40)

try:
    result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout.strip())
        
        # 获取更多信息
        result2 = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version,memory.total,memory.used", "--format=csv,noheader"],
            capture_output=True, text=True
        )
        if result2.returncode == 0:
            info = result2.stdout.strip().split(", ")
            print(f"\n驱动版本: {info[0]}")
            print(f"显存总量: {info[1]}")
            print(f"显存占用: {info[2]}")
    else:
        print("❌ nvidia-smi 运行失败")
except FileNotFoundError:
    print("❌ 未找到 nvidia-smi")
    print("   请安装 NVIDIA 驱动")


# ========== 2. Ollama 状态 ==========
print("\n【2】Ollama 模型状态")
print("-" * 40)

try:
    result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
    output = result.stdout.strip()
    
    if output:
        print(output)
        
        # 检查是否使用 GPU
        if "GPU" in output:
            print("\n✅ 模型正在使用 GPU")
        elif "CPU" in output:
            print("\n⚠️ 模型正在使用 CPU（速度较慢）")
    else:
        print("当前没有运行中的模型")
except Exception as e:
    print(f"❌ 检查失败: {e}")


# ========== 3. 环境变量 ==========
print("\n【3】GPU 相关环境变量")
print("-" * 40)

vars_to_check = [
    "CUDA_VISIBLE_DEVICES",
    "OLLAMA_GPU_LAYERS", 
    "OLLAMA_NUM_GPU",
]

for var in vars_to_check:
    val = os.environ.get(var, "未设置")
    print(f"  {var}: {val}")


# ========== 4. 建议 ==========
print("\n【4】如果 GPU 不工作，尝试以下方法")
print("-" * 40)
print("""
  方法1: 重启 Ollama
    taskkill /f /im ollama.exe
    ollama serve

  方法2: 设置环境变量
    $env:OLLAMA_GPU_LAYERS = "-1"
    ollama serve

  方法3: 更新驱动
    访问 https://www.nvidia.com/drivers

  方法4: 安装 CUDA Toolkit
    访问 https://developer.nvidia.com/cuda-downloads
""")

print("=" * 60)