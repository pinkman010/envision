@echo off
chcp 65001 >nul
REM ============================================
REM ESG AI Expert System - Windows 一键部署脚本
REM 用途：零Python基础快速部署
REM 运行方式: 双击运行或 cmd 中执行 quick_start.bat
REM ============================================

echo 🌱 新能源行业ESG披露与沟通智能分析系统 - Windows一键部署
echo ========================================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker 未安装
    echo 请先安装 Docker: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker Compose 未安装
    echo 请先安装 Docker Compose: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过

REM 检查.env文件
if not exist ".env" (
    echo ⚠️ 未找到 .env 文件
    if exist ".env.example" (
        echo 📝 正在从 .env.example 创建 .env 文件...
        copy .env.example .env
        echo ⚠️ 请编辑 .env 文件，配置您的 LLM_API_KEY 等敏感信息
        echo    编辑完成后，重新运行此脚本
        pause
        exit /b 0
    ) else (
        echo ❌ 错误: 找不到 .env.example 文件
        pause
        exit /b 1
    )
)

echo ✅ 环境变量配置检查通过

REM 创建必要目录
echo 📁 创建数据存储目录...
if not exist "data\chroma_db" mkdir "data\chroma_db"
if not exist "data\sqlite_db" mkdir "data\sqlite_db"
if not exist "data\raw_corpus\versioned" mkdir "data\raw_corpus\versioned"
if not exist "data\raw_corpus\unversioned" mkdir "data\raw_corpus\unversioned"
if not exist "data\export_results" mkdir "data\export_results"
if not exist "logs" mkdir "logs"

echo ✅ 目录结构创建完成

REM 构建并启动服务
echo 🐳 正在构建 Docker 镜像...
docker-compose -f deploy\docker-compose.yml build
if errorlevel 1 (
    echo ❌ Docker 镜像构建失败
    pause
    exit /b 1
)

echo 🚀 启动服务...
docker-compose -f deploy\docker-compose.yml up -d
if errorlevel 1 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

echo.
echo ========================================================
echo ✅ 部署成功！
echo ========================================================
echo.
echo 📍 前端界面: http://localhost:8501
echo 📍 后端API:  http://localhost:8000
echo 📍 API文档:  http://localhost:8000/docs
echo.
echo 常用命令:
echo   查看日志: docker-compose -f deploy\docker-compose.yml logs -f
echo   停止服务: docker-compose -f deploy\docker-compose.yml down
echo   重启服务: docker-compose -f deploy\docker-compose.yml restart
echo.
echo ⚠️ 提示: 首次启动可能需要几分钟下载依赖，请耐心等待
echo.
pause
