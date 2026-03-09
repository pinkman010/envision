#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest 覆盖率检测工具 (核心业务版)
只检测真正的核心业务代码覆盖率（esg/目录下除config外 + main.py + start_windows.py）
"""

import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 尝试导入coverage
try:
    import coverage
except ImportError:
    print("❌ 缺少依赖: pip install coverage pytest pytest-cov")
    input("按回车键退出...")
    sys.exit(1)


class CoverageStats:
    def __init__(self, name="全部代码"):
        self.name = name
        self.files = {}
        self.total_lines = 0
        self.missed_lines = 0
        self.covered_lines = 0

    def add_file(self, filepath, file_data):
        self.files[filepath] = file_data
        self.total_lines += file_data.get("lines_total", 0)
        self.missed_lines += file_data.get("lines_missed", 0)
        self.covered_lines += file_data.get("lines_covered", 0)

    def line_rate(self):
        if self.total_lines == 0:
            return 0.0
        return self.covered_lines / self.total_lines * 100

    def get_uncovered_files(self):
        return [f for f, d in self.files.items() if d.get("lines_covered", 0) == 0]

    def get_low_coverage_files(self, threshold=50):
        low_files = []
        for f, d in self.files.items():
            total = d.get("lines_total", 0)
            covered = d.get("lines_covered", 0)
            if total > 0 and (covered / total * 100) < threshold:
                low_files.append((f, covered / total * 100))
        return sorted(low_files, key=lambda x: x[1])


def find_project_root(start_path=None):
    """智能查找项目根目录"""
    if start_path is None:
        start_path = Path(__file__).resolve().parent

    current = start_path
    for _ in range(5):
        markers = [".git", "tests", "test", "src", "pyproject.toml", "setup.py", "requirements.txt"]
        if any((current / marker).exists() for marker in markers):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start_path.parent.parent


def find_test_dir(project_root):
    """自动查找测试目录"""
    possible_names = ["tests", "test", "Testing", "testing"]
    for name in possible_names:
        test_path = project_root / name
        if test_path.exists() and test_path.is_dir():
            return test_path
    return project_root


def is_core_business_file(filepath, root_path):
    """
    判断是否为真正的核心业务代码
    ✅ 核心业务：esg/目录下(除templates/外) + main.py + start_windows.py
    ❌ 排除：tests/, scripts/, logs/, esg/templates/, temp_chroma_test/, egg-info等
    """
    path = Path(filepath)
    try:
        relative_path = path.relative_to(Path(root_path))
    except ValueError:
        return False

    parts = relative_path.parts
    filename = path.name

    # 1. 排除特定目录（非业务代码）
    exclude_dirs = {
        "tests",
        "test",
        "scripts",
        "logs",
        "temp_chroma_test",
        "esg_intelligent_analysis.egg-info",
        "__pycache__",
        ".git",
        "venv",
        ".venv",
        "env",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "dist",
        "build",
    }
    if any(p in exclude_dirs for p in parts):
        return False

    # 2. 排除 esg/templates/ 目录（纯配置数据）
    if "esg" in parts and "templates" in parts:
        try:
            esg_idx = parts.index("esg")
            config_idx = parts.index("templates")
            # 确保是 esg/ 直接下的 templates/
            if config_idx == esg_idx + 1:
                return False
        except ValueError:
            pass

    # 3. 排除特定文件
    if filename in {".coverage", "test_report_sample.md", "__init__.py"}:
        return False

    # 4. 只保留 .py 文件
    if not filename.endswith(".py"):
        return False

    # 5. ✅ 核心业务代码判定
    # 5.1 esg/ 目录下的文件（已通过上面的config过滤）
    if "esg" in parts:
        return True

    # 5.2 入口文件（无论在根目录还是src目录）
    if filename in ("main.py", "start_windows.py"):
        return True

    # 其他都视为非核心业务
    return False


def run_pytest(test_path, cov_sources, project_root):
    """运行pytest并生成覆盖率数据"""
    cov_arg = ",".join(cov_sources) if isinstance(cov_sources, list) else cov_sources

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_path),
        f"--cov={cov_arg}",
        "--cov-report=term-missing",
        "--cov-branch",
        "-v",
    ]

    print(f"🧪 运行测试: {' '.join(cmd)}")
    print(f"📂 项目根目录: {project_root}")
    print("=" * 80)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=False,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            print("\n⚠️  部分测试失败，但仍将继续分析覆盖率数据...")
        return True

    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False


def analyze_coverage(project_root, data_file=".coverage"):
    """分析覆盖率数据 - 只统计核心业务代码"""
    data_file = Path(project_root) / data_file

    if not data_file.exists():
        return None, None

    try:
        cov = coverage.Coverage(data_file=str(data_file))
        cov.load()
    except Exception as e:
        print(f"❌ 读取覆盖率数据失败: {e}")
        return None, None

    # 只创建核心业务代码统计（不再区分全部 vs 核心，避免混淆）
    core_stats = CoverageStats("核心业务代码")
    non_core_files = []  # 记录被过滤的文件用于调试

    measured_files = cov.get_data().measured_files()

    for filepath in measured_files:
        abs_path = Path(filepath).resolve()

        if not abs_path.exists():
            continue

        # 严格过滤：只处理核心业务代码
        if not is_core_business_file(abs_path, project_root):
            try:
                rel_path = Path(abs_path).relative_to(Path(project_root))
                non_core_files.append(str(rel_path))
            except:
                non_core_files.append(str(abs_path))
            continue

        try:
            analysis = cov.analysis2(str(abs_path))
            _, statements, excluded, missing, _ = analysis

            total_lines = len(statements)
            missed_lines = len(missing)
            covered_lines = total_lines - missed_lines

            if total_lines == 0:
                continue

            file_data = {
                "path": str(abs_path),
                "lines_total": total_lines,
                "lines_missed": missed_lines,
                "lines_covered": covered_lines,
                "missing_lines": list(missing),
            }

            core_stats.add_file(str(abs_path), file_data)

        except Exception as e:
            continue

    if non_core_files:
        print(f"\nℹ️  已排除 {len(non_core_files)} 个非核心业务文件 (tests, scripts, config等)")

    return core_stats, non_core_files


def get_dir_coverage(stats, project_root):
    """按目录统计覆盖率（按模块分组）"""
    dir_stats = defaultdict(lambda: {"total": 0, "covered": 0, "files": 0})

    for filepath, data in stats.files.items():
        try:
            rel_path = Path(filepath).relative_to(Path(project_root))
            # 按业务模块分组（如 esg/analysis, esg/core 等）
            parts = rel_path.parts
            if "esg" in parts:
                esg_idx = parts.index("esg")
                if len(parts) > esg_idx + 1 and parts[esg_idx + 1] != "__pycache__":
                    dir_name = f"esg/{parts[esg_idx + 1]}"
                else:
                    dir_name = "esg/root"
            else:
                dir_name = "[根目录入口]"
        except:
            dir_name = "[其他]"

        dir_stats[dir_name]["total"] += data["lines_total"]
        dir_stats[dir_name]["covered"] += data["lines_covered"]
        dir_stats[dir_name]["files"] += 1

    results = []
    for dir_name, data in dir_stats.items():
        if data["total"] > 0:
            rate = data["covered"] / data["total"] * 100
            results.append((dir_name, rate, data["files"], data["total"]))

    return sorted(results, key=lambda x: x[1], reverse=True)


def print_coverage_bar(rate, width=20):
    filled = int(rate / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {rate:.1f}%"


def print_results(core_stats, project_root):
    """打印核心业务代码覆盖率报告"""
    if not core_stats or not core_stats.files:
        print("❌ 没有收集到核心业务代码的覆盖率数据")
        print("💡 可能原因：")
        print("   1. 测试未运行成功")
        print("   2. 测试未覆盖到 esg/ 目录下的代码")
        print("   3. .coverage 文件未生成或路径错误")
        return

    print("\n" + "=" * 85)
    print(f"{'核心业务代码覆盖率报告':^85}")
    print(f"{'(esg/目录除config外 + main.py + start_windows.py)':^85}")
    print("=" * 85)
    print(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 项目路径: {project_root}")
    print(f"📊 统计范围: {len(core_stats.files)} 个核心业务文件")

    # 总体统计
    print(f"\n📈 总体覆盖率")
    core_line = core_stats.line_rate()
    print(f"   行覆盖率: {print_coverage_bar(core_line)}")
    print(f"   代码总行数: {core_stats.total_lines:,} 行")
    print(f"   已覆盖: {core_stats.covered_lines:,} 行")
    print(f"   未覆盖: {core_stats.missed_lines:,} 行")

    # 按业务模块排名
    print(f"\n📂 各业务模块覆盖率排名")
    dir_cov = get_dir_coverage(core_stats, project_root)

    # 定义模块重要性（可选）
    critical_modules = {"esg/core", "esg/analysis", "esg/rag"}

    for i, (dir_name, rate, file_count, total_lines) in enumerate(dir_cov[:15], 1):
        status = "✅" if rate >= 80 else "⚠️ " if rate >= 50 else "❌"
        importance = "🔥" if dir_name in critical_modules else "  "
        print(
            f"   {importance}{status} {i}. {dir_name:<25} {rate:>6.1f}% "
            f"({file_count}文件, {total_lines}行)"
        )

    # 未覆盖文件（核心业务）
    uncovered = core_stats.get_uncovered_files()
    if uncovered:
        print(f"\n❌ 核心业务代码中完全未覆盖的文件 ({len(uncovered)}个):")
        for f in uncovered[:15]:
            try:
                rel_path = Path(f).relative_to(Path(project_root))
                print(f"      • {rel_path}")
            except:
                print(f"      • {f}")
        if len(uncovered) > 15:
            print(f"      ... 还有 {len(uncovered)-15} 个文件")

    # 低覆盖率警告（核心业务）
    low_cov = core_stats.get_low_coverage_files(threshold=50)
    if low_cov:
        print(f"\n🔶 核心业务代码中覆盖率低于50%的文件 ({len(low_cov)}个):")
        for f, rate in low_cov[:10]:
            try:
                rel_path = Path(f).relative_to(Path(project_root))
                print(f"      • {rel_path}: {rate:.1f}%")
            except:
                print(f"      • {f}: {rate:.1f}%")

    # 质量评估
    print(f"\n💡 业务代码质量评估")
    if core_line >= 80:
        print("   ✅ 优秀：核心业务代码覆盖率高，质量有保障")
    elif core_line >= 60:
        print("   🟡 良好：覆盖率尚可，建议补充关键路径测试")
    elif core_line >= 40:
        print("   🟠 一般：覆盖率偏低，存在业务风险")
    else:
        print("   🔴 较差：核心业务代码测试严重不足，建议优先补充")

    print("\n" + "=" * 85)


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = find_project_root(script_dir)

    print(f"🔍 自动检测到项目根目录: {project_root}")
    print(f"🎯 检测范围: esg/目录(除config) + main.py + start_windows.py")

    # 自动查找测试目录
    test_dir = find_test_dir(project_root)
    print(f"📂 测试目录: {test_dir}")

    # 自动运行测试
    print(f"\n🚀 自动运行测试...")
    # cov_source 设为项目根目录，确保能扫描到所有代码
    run_pytest(test_dir, ".", project_root)

    # 分析覆盖率（只分析核心业务）
    print(f"\n📊 正在分析核心业务代码覆盖率...")
    core_stats, excluded_files = analyze_coverage(str(project_root))

    if core_stats:
        print_results(core_stats, str(project_root))

        if sys.platform == "win32" and "pythonw" not in sys.executable:
            print("\n")
            input("按回车键退出...")
    else:
        print("❌ 分析失败，请检查测试是否正确运行")
        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
