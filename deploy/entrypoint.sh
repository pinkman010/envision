#!/bin/bash
# ============================================
# ESG AI Expert System - 容器入口脚本
# 用途：根据启动模式启动不同服务
# ============================================

set -e

echo "🌱 启动新能源行业ESG披露与沟通智能分析系统"
echo "================================================"

# 检查必要的环境变量
if [ -z "$LLM_API_KEY" ]; then
    echo "⚠️ 警告: LLM_API_KEY 未设置，部分功能可能无法使用"
fi

# 创建必要的目录
mkdir -p /app/logs
mkdir -p /app/data/chroma_db
mkdir -p /app/data/sqlite_db
mkdir -p /app/data/raw_corpus/versioned
mkdir -p /app/data/raw_corpus/unversioned
mkdir -p /app/data/export_results

echo "📁 目录结构初始化完成"

# 根据启动参数决定启动什么服务
if [ "$1" = "api" ] || [ -z "$1" ]; then
    echo "🚀 启动 FastAPI 后端服务..."
    echo "📍 访问地址: http://localhost:8000"
    echo "📍 API文档: http://localhost:8000/docs"
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
elif [ "$1" = "ui" ]; then
    echo "🎨 启动 Streamlit 前端服务..."
    echo "📍 访问地址: http://localhost:8501"
    exec streamlit run src/ui/app.py --server.port=8501 --server.address=0.0.0.0
else
    echo "❌ 未知的启动参数: $1"
    echo "用法: docker run <image> [api|ui]"
    exit 1
fi
