.PHONY: help install install-dev run-api run-ui test lint format clean
PYTHON := python

# 显示帮助
help:
	@echo "ESG AI Expert System - 可用命令:"
	@echo "  make install      - 安装生产环境依赖"
	@echo "  make install-dev  - 安装开发环境依赖（含代码检查工具）"
	@echo "  make run-api      - 启动FastAPI后端服务"
	@echo "  make run-ui       - 启动Streamlit前端服务"
	@echo "  make test         - 运行测试用例"
	@echo "  make lint         - 运行代码检查（flake8, mypy）"
	@echo "  make format       - 运行代码格式化（black）"
	@echo "  make clean        - 清理临时文件、缓存"

# 安装生产环境依赖
install:
	pip install --upgrade pip
	pip install -e .

# 安装开发环境依赖
install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	pre-commit install

# 启动FastAPI后端服务
run-api:
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 启动Streamlit前端服务
run-ui:
	streamlit run src/app.py

# 运行测试用例
test:
	pytest tests/ -v --cov=src --cov-report=html

# 运行代码检查
lint:
	flake8 src/ tests/
	mypy src/

# 运行代码格式化
format:
	black src/ tests/

# 清理临时文件、缓存
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf tmp/debug_cache/
	rm -rf tmp/test_output/