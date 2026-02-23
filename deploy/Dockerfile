# ============================================
# ESG AI Expert System - Docker 镜像构建文件
# 用途：一键构建后端+前端一体化容器
# ============================================

FROM python:3.10-slim

LABEL maintainer="Envision ESG Team"
LABEL description="新能源行业ESG披露与沟通智能分析系统"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY demo_data/ ./demo_data/
COPY docs/ ./docs/

# 暴露端口
# 8000: FastAPI后端
# 8501: Streamlit前端
EXPOSE 8000 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动脚本
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
