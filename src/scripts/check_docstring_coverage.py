#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docstring 覆盖率检测工具
统计项目中的函数和类是否有文档字符串
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path


class DocstringStats:
    def __init__(self, name="全部代码"):
        self.name = name
        self.files_checked = 0  # 检查的.py文件数
        self.total_nodes = 0  # 总函数/类数
        self.with_docstring = 0  # 有docstring的数量
        self.missing_list = []  # 缺失列表：(文件路径, [(名称, 行号), ...])

    def add_file(self, filepath, total, with_doc, missing):
        self.files_checked += 1
        self.total_nodes += total
        self.with_docstring += with_doc
        if missing:
            self.missing_list.append((filepath, missing))

    def coverage_rate(self):
        if self.total_nodes == 0:
            return 0.0
        return (self.with_docstring / self.total_nodes) * 100

    def missing_count(self):
        return self.total_nodes - self.with_docstring


def is_filtered_file(filepath, root_path):
    """判断文件是否应该被过滤（排除 __init__.py、tests目录、scripts目录）"""
    path = Path(filepath)
    try:
        relative_path = path.relative_to(Path(root_path))
    except ValueError:
        return False

    parts = relative_path.parts

    if path.name == "__init__.py":
        return True
    if any(p in ("tests", "test") for p in parts):
        return True
    if any(p in ("scripts", "script") for p in parts):
        return True

    return False


def check_file(filepath):
    """检查单个文件的docstring"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return 0, 0, []  # 空文件

        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"⚠️  语法错误 {filepath}: {e}")
        return 0, 0, []
    except Exception as e:
        print(f"⚠️  无法解析 {filepath}: {e}")
        return 0, 0, []

    total = 0
    with_doc = 0
    missing = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            # 跳过私有方法（单下划线开头但非双下划线）
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue
            # 跳过 property 装饰器的方法（通常不需要独立docstring）
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(
                    isinstance(dec, ast.Name) and dec.id == "property"
                    for dec in node.decorator_list
                ):
                    continue

            total += 1
            if ast.get_docstring(node):
                with_doc += 1
            else:
                missing.append((node.name, node.lineno))

    return total, with_doc, missing


def scan_project(project_root, source_dirs=None):
    """
    扫描项目
    返回 (all_stats, core_stats)
    """
    if source_dirs is None:
        source_dirs = ["src", "."]  # 默认扫描src目录和根目录

    all_stats = DocstringStats("全部文件")
    core_stats = DocstringStats("核心业务代码(排除tests,scripts,__init__)")

    project_root = Path(project_root).resolve()
    checked_files = set()  # 防止重复检查

    for src_dir in source_dirs:
        scan_path = project_root / src_dir
        if not scan_path.exists():
            continue

        for root, dirs, files in os.walk(scan_path):
            # 排除缓存和依赖目录
            dirs[:] = [
                d
                for d in dirs
                if d
                not in {
                    "__pycache__",
                    ".git",
                    "node_modules",
                    "venv",
                    ".venv",
                    "env",
                    "build",
                    "dist",
                    ".pytest_cache",
                    ".mypy_cache",
                    "egg-info",
                    ".tox",
                }
            ]

            for file in files:
                if not file.endswith(".py"):
                    continue

                filepath = Path(root) / file
                abs_path = filepath.resolve()

                # 避免重复检查
                if abs_path in checked_files:
                    continue
                checked_files.add(abs_path)

                # 检查文件
                total, with_doc, missing = check_file(abs_path)

                # 如果没有找到任何函数/类，可能不是业务代码，跳过统计
                if total == 0:
                    continue

                all_stats.add_file(str(abs_path), total, with_doc, missing)

                # 核心业务代码统计
                if not is_filtered_file(abs_path, project_root):
                    core_stats.add_file(str(abs_path), total, with_doc, missing)

    return all_stats, core_stats


def print_coverage_bar(rate, width=20):
    """打印ASCII进度条"""
    filled = int(rate / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {rate:.1f}%"


def print_results(all_stats, core_stats, project_root):
    """打印格式化报告"""
    print("\n" + "=" * 80)
    print(f"{'Docstring 覆盖率检测报告':^80}")
    print("=" * 80)
    print(f"📁 项目路径: {project_root}")

    # 1. 总体统计
    print(f"\n📊 总体统计对比")
    print(f"   {'指标':<25} {'全部文件':>20} {'核心业务代码':>25}")
    print(f"   {'-'*25} {'-'*20} {'-'*25}")
    print(f"   {'检查.py文件数':<25} {all_stats.files_checked:>20} {core_stats.files_checked:>25}")
    print(f"   {'函数/类总数':<25} {all_stats.total_nodes:>20} {core_stats.total_nodes:>25}")
    print(f"   {'有Docstring':<25} {all_stats.with_docstring:>20} {core_stats.with_docstring:>25}")
    print(
        f"   {'缺失Docstring':<25} {all_stats.missing_count():>20} {core_stats.missing_count():>25}"
    )

    # 覆盖率对比
    all_rate = all_stats.coverage_rate()
    core_rate = core_stats.coverage_rate()
    print(
        f"   {'Docstring覆盖率':<25} {print_coverage_bar(all_rate):>20} {print_coverage_bar(core_rate):>25}"
    )

    # 2. 文件级明细（核心业务代码）
    if core_stats.missing_list:
        print(f"\n📄 核心业务代码中缺失 Docstring 的文件 ({len(core_stats.missing_list)}个):")

        # 按缺失数量排序
        sorted_missing = sorted(core_stats.missing_list, key=lambda x: len(x[1]), reverse=True)

        for i, (filepath, items) in enumerate(sorted_missing[:10], 1):
            try:
                rel_path = Path(filepath).relative_to(Path(project_root))
            except:
                rel_path = filepath

            missing_count = len(items)
            total_in_file = missing_count + sum(
                1 for f, m in core_stats.missing_list if f == filepath
            )

            print(f"\n   {i}. {rel_path} ({missing_count}个缺失):")

            # 显示前3个缺失项
            for name, lineno in items[:3]:
                print(f"      - {name} (第{lineno}行)")
            if len(items) > 3:
                print(f"      ... 还有 {len(items)-3} 个")

        if len(sorted_missing) > 10:
            print(f"\n   ... 还有 {len(sorted_missing)-10} 个文件存在缺失")

    # 3. 优秀文件展示 (>90% 覆盖率)
    good_files = []
    for filepath, missing in core_stats.missing_list:
        # 反向查找该文件的总数（这里简化处理，实际应该存储更多信息）
        pass  # 简化版本不展示

    # 4. 建议
    print(f"\n💡 改进建议:")
    if core_rate < 30:
        print("   🔴 覆盖率较低，建议优先为核心类添加模块说明文档")
    elif core_rate < 60:
        print("   🟡 覆盖率中等，建议为公开API函数添加参数说明")
    else:
        print("   🟢 覆盖率良好，建议为复杂算法添加实现细节说明")

    # 5. 快速修复命令（生成TODO列表）
    if core_stats.missing_list:
        print(f"\n📝 快速修复清单 (前5个):")
        for filepath, items in core_stats.missing_list[:5]:
            try:
                rel_path = Path(filepath).relative_to(Path(project_root))
            except:
                rel_path = filepath
            print(f"   # {rel_path}")
            for name, lineno in items[:2]:
                print(f"   # TODO: Line {lineno} - {name}")

    print("\n" + "=" * 80)


def export_report(all_stats, core_stats, project_root, output_file="docstring_report.md"):
    """导出Markdown报告"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Docstring 覆盖率检测报告\n\n")
            f.write(f"**项目路径:** `{project_root}`\n\n")

            f.write("## 统计汇总\n\n")
            f.write("| 指标 | 全部文件 | 核心业务代码 |\n")
            f.write("|------|---------|-------------|\n")
            f.write(f"| 检查.py文件数 | {all_stats.files_checked} | {core_stats.files_checked} |\n")
            f.write(f"| 函数/类总数 | {all_stats.total_nodes} | {core_stats.total_nodes} |\n")
            f.write(f"| 有Docstring | {all_stats.with_docstring} | {core_stats.with_docstring} |\n")
            f.write(
                f"| Docstring覆盖率 | {all_stats.coverage_rate():.1f}% | {core_stats.coverage_rate():.1f}% |\n\n"
            )

            if core_stats.missing_list:
                f.write("## 需要补充Docstring的函数/类\n\n")
                f.write("| 文件路径 | 函数/类名 | 行号 |\n")
                f.write("|----------|----------|------|\n")

                for filepath, items in sorted(core_stats.missing_list):
                    try:
                        rel_path = Path(filepath).relative_to(Path(project_root))
                    except:
                        rel_path = filepath

                    for name, lineno in items:
                        f.write(f"| {rel_path} | {name} | {lineno} |\n")
            else:
                f.write("✅ 所有函数/类都有docstring！\n")

        print(f"\n✅ 报告已导出: {output_file}")
    except Exception as e:
        print(f"❌ 导出报告失败: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Docstring 覆盖率检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 检测当前目录
  %(prog)s --src src,lib      # 指定源码目录(逗号分隔)
  %(prog)s --export report.md # 导出Markdown报告
        """,
    )
    parser.add_argument("path", nargs="?", default=".", help="项目根目录 (默认: 当前目录)")
    parser.add_argument("--src", default="src,.", help="源码目录(逗号分隔，默认: src,.)")
    parser.add_argument(
        "--export", "-o", nargs="?", const="docstring_report.md", help="导出Markdown报告"
    )

    args = parser.parse_args()

    project_root = Path(args.path).resolve()
    if not project_root.exists():
        print(f"❌ 目录不存在: {project_root}")
        sys.exit(1)

    source_dirs = [d.strip() for d in args.src.split(",") if d.strip()]

    print(f"🔍 正在扫描项目: {project_root}")
    print(f"📂 源码目录: {', '.join(source_dirs)}")

    all_stats, core_stats = scan_project(project_root, source_dirs)

    if all_stats.files_checked == 0:
        print("❌ 未找到Python文件")
        sys.exit(1)

    print_results(all_stats, core_stats, str(project_root))

    if args.export:
        export_report(all_stats, core_stats, str(project_root), args.export)


if __name__ == "__main__":
    main()
