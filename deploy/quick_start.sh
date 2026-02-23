#!/bin/bash
# ============================================
# ESG AI Expert System - Linux/Mac 一键部署脚本
# 用途：零Python基础快速部署
# 运行方式: chmod +x quick_start.sh && ./quick_start.sh
# ============================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_NAME="Envision ESG System"
echo -e "${GREEN}🌱 ${PROJECT_NAME} 一键部署脚本${NC}"
echo "================================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker Compose 未安装${NC}"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker 环境检查通过${NC}"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ 未找到 .env 文件${NC}"
    if [ -f ".env.example" ]; then
        echo "📝 正在从 .env.example 创建 .env 文件..."
        cp .env.example .env
        echo -e "${YELLOW}⚠️ 请编辑 .env 文件，配置您的 LLM_API_KEY 等敏感信息${NC}"
        echo "   编辑完成后，重新运行此脚本"
        exit 0
    else
        echo -e "${RED}❌ 错误: 找不到 .env.example 文件${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 环境变量配置检查通过${NC}"

# 创建必要目录
echo "📁 创建数据存储目录..."
mkdir -p data/chroma_db
mkdir -p data/sqlite_db
mkdir -p data/raw_corpus/versioned
mkdir -p data/raw_corpus/unversioned
mkdir -p data/export_results
mkdir -p logs

echo -e "${GREEN}✅ 目录结构创建完成${NC}"

# 构建并启动服务
echo "🐳 正在构建 Docker 镜像..."
docker-compose -f deploy/docker-compose.yml build

echo "🚀 启动服务..."
docker-compose -f deploy/docker-compose.yml up -d

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ ${PROJECT_NAME} 部署成功！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "📍 前端界面: ${BLUE}http://localhost:8501${NC}"
echo -e "📍 后端API:  ${BLUE}http://localhost:8000${NC}"
echo -e "📍 API文档:  ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose -f deploy/docker-compose.yml logs -f"
echo "  停止服务: docker-compose -f deploy/docker-compose.yml down"
echo "  重启服务: docker-compose -f deploy/docker-compose.yml restart"
echo ""
echo -e "${YELLOW}⚠️ 提示: 首次启动可能需要几分钟下载依赖，请耐心等待${NC}"
