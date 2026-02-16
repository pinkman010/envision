#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合代码复杂度分析工具 (修复版)
修复：极高风险函数显示 + 添加文件路径
"""

import ast
import os
import sys
import traceback
from collections import defaultdict, namedtuple
from datetime import datetime
from pathlib import Path

CC_RATING = {
    (1, 5): ("🟢 简单", "green", "可维护"),
    (5, 10): ("🟡 中等", "yellow", "可接受"),
    (10, 20): ("🟠 复杂", "orange", "需重构"),
    (20, 50): ("🔴 高风险", "red", "必须重构"),
    (50, float("inf")): ("🚫 极高风险", "magenta", "紧急处理"),
}

TIME_RATING = {
    "O(1)": ("🟢", 1),
    "O(log n)": ("🟢", 2),
    "O(n)": ("🟡", 3),
    "O(n log n)": ("🟡", 4),
    "O(n²)": ("🟠", 5),
    "O(n³)": ("🔴", 6),
    "O(2^n)": ("🚫", 7),
    "Recursive": ("🔁", 8),
    "Unknown": ("⚪", 0),
}

ComplexityInfo = namedtuple(
    "ComplexityInfo",
    [
        "name",
        "line",
        "cyclomatic",
        "cc_rating",
        "time_complexity",
        "space_complexity",
        "risk_level",
        "risk_reason",
        "details",
    ],
)


class UnifiedComplexityVisitor(ast.NodeVisitor):
    def __init__(self, func_name):
        self.func_name = func_name
        self.cc_count = 1
        self.loop_depth = 0
        self.max_loop_depth = 0
        self.has_recursion = False
        self.recursive_lines = []
        self.slicing_ops = 0
        self.list_comp_depth = 0
        self.space_allocations = []

    def visit_If(self, node):
        self.cc_count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.cc_count += 1
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_For(self, node):
        self.cc_count += 1
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_ExceptHandler(self, node):
        self.cc_count += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.cc_count += len(node.values) - 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.list_comp_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.list_comp_depth)
        self.space_allocations.append(("list_comp", node.lineno))
        self.generic_visit(node)
        self.list_comp_depth -= 1

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == self.func_name:
            self.has_recursion = True
            self.recursive_lines.append(node.lineno)
            self.cc_count += 1

        if isinstance(node.func, ast.Name):
            if node.func.id in ["sorted", "list", "set", "sum"]:
                self.slicing_ops += 1
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ["sort", "sorted", "copy", "deepcopy"]:
                self.slicing_ops += 1
                if node.func.attr in ["copy", "deepcopy"]:
                    self.space_allocations.append(("copy", node.lineno))

        self.generic_visit(node)

    def visit_Subscript(self, node):
        if isinstance(node.slice, (ast.Slice, ast.Constant)):
            if isinstance(node.ctx, ast.Load):
                self.slicing_ops += 1
        self.generic_visit(node)

    def get_cyclomatic_complexity(self):
        return self.cc_count

    def get_cc_rating(self):
        cc = self.cc_count
        for (low, high), (label, color, desc) in CC_RATING.items():
            if low <= cc < high:
                return label, desc
        return "🚫 极高风险", "紧急处理"

    def get_time_complexity(self):
        if self.has_recursion:
            return "Recursive"

        depth = self.max_loop_depth
        if depth == 0:
            if self.slicing_ops > 0:
                return "O(n log n)" if self.slicing_ops > 1 else "O(n)"
            return "O(1)"
        elif depth == 1:
            return "O(n²)" if self.slicing_ops > 0 else "O(n)"
        elif depth == 2:
            return "O(n³)" if self.slicing_ops > 0 else "O(n²)"
        elif depth == 3:
            return "O(n³)"
        else:
            return f"O(n^{depth})"

    def get_space_complexity(self):
        level = 1
        if self.has_recursion:
            level = 3
        if self.list_comp_depth > 0:
            level = max(level, self.list_comp_depth + 1)
        if self.space_allocations:
            level = max(level, 2)

        mapping = {1: "O(1)", 2: "O(n)", 3: "O(n)", 4: "O(n²)", 5: "O(n²)"}
        return mapping.get(level, "O(n)")

    def get_risk_assessment(self):
        risks = []
        cc = self.cc_count

        if cc >= 20:
            risks.append(f"圈复杂度过高({cc})")
        elif cc >= 10:
            risks.append(f"圈复杂度中等({cc})")

        time = self.get_time_complexity()
        if time in ["O(n³)", "O(2^n)", "Recursive"]:
            risks.append("时间复杂度高")
        elif time == "O(n²)" and self.max_loop_depth >= 2:
            risks.append("嵌套循环性能风险")

        if self.space_allocations and self.max_loop_depth > 1:
            risks.append("大内存分配风险")

        if not risks:
            return "✅ 良好", "代码质量良好"
        elif len(risks) >= 2:
            return "🚨 高风险", "; ".join(risks)
        else:
            return "⚠️  注意", risks[0]


class ComplexityStats:
    def __init__(self, name="全部代码"):
        self.name = name
        self.files_checked = 0
        self.functions = []  # [(filepath, ComplexityInfo), ...]  修改为存储路径
        self.cc_distribution = defaultdict(int)
        self.time_distribution = defaultdict(int)

    def add_function(self, filepath, info: ComplexityInfo):  # 添加filepath参数
        self.functions.append((filepath, info))
        self.cc_distribution[info.cc_rating[0]] += 1
        self.time_distribution[info.time_complexity] += 1

    def add_file(self):
        self.files_checked += 1

    def get_high_risk_functions(self):
        """获取高风险函数（包含极高风险 🚫）"""
        return [
            (fp, f)
            for fp, f in self.functions
            if "🚨" in f.risk_level or "🔴" in f.cc_rating[0] or "🚫" in f.cc_rating[0]
        ]  # 修复：添加极高风险判断

    def avg_cyclomatic(self):
        if not self.functions:
            return 0
        return sum(f.cyclomatic for _, f in self.functions) / len(self.functions)

    def max_cyclomatic(self):
        if not self.functions:
            return 0
        return max(f.cyclomatic for _, f in self.functions)


def analyze_function(func_node, filepath):
    analyzer = UnifiedComplexityVisitor(func_node.name)
    analyzer.visit(func_node)

    cc = analyzer.get_cyclomatic_complexity()
    cc_label, cc_desc = analyzer.get_cc_rating()
    time_complexity = analyzer.get_time_complexity()
    space_complexity = analyzer.get_space_complexity()
    risk_level, risk_reason = analyzer.get_risk_assessment()

    details = []
    if analyzer.max_loop_depth > 0:
        details.append(f"{analyzer.max_loop_depth}层循环")
    if analyzer.has_recursion:
        details.append("递归")
    if analyzer.slicing_ops > 0:
        details.append(f"{analyzer.slicing_ops}次切片/排序")

    return ComplexityInfo(
        name=func_node.name,
        line=func_node.lineno,
        cyclomatic=cc,
        cc_rating=(cc_label, cc_desc),
        time_complexity=time_complexity,
        space_complexity=space_complexity,
        risk_level=risk_level,
        risk_reason=risk_reason,
        details=", ".join(details) if details else "顺序执行",
    )


def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return []

        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"⚠️  语法错误 {filepath}: {e}")
        return []
    except Exception as e:
        print(f"⚠️  无法解析 {filepath}: {e}")
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if len(node.body) < 2:
                continue

            info = analyze_function(node, filepath)
            results.append((str(filepath), info))

    return results


def is_filtered_file(filepath, root_path):
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


def find_project_root(start_path=None):
    if start_path is None:
        start_path = Path(__file__).resolve().parent
    current = start_path
    for _ in range(5):
        markers = [".git", "tests", "test", "src", "pyproject.toml", "setup.py"]
        if any((current / marker).exists() for marker in markers):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start_path.parent.parent


def scan_project(project_root, source_dirs=None):
    if source_dirs is None:
        source_dirs = ["src", ".", project_root.name]

    all_stats = ComplexityStats("全部文件")
    core_stats = ComplexityStats("核心业务代码")

    project_root = Path(project_root).resolve()
    checked_files = set()

    for src_dir in source_dirs:
        scan_path = project_root / src_dir
        if not scan_path.exists():
            continue

        for root, dirs, files in os.walk(scan_path):
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
                }
            ]

            for file in files:
                if not file.endswith(".py"):
                    continue

                filepath = Path(root) / file
                abs_path = filepath.resolve()

                if abs_path in checked_files:
                    continue
                checked_files.add(abs_path)

                results = analyze_file(abs_path)
                if not results:
                    continue

                all_stats.add_file()
                for fp, info in results:
                    all_stats.add_function(fp, info)  # 传递路径

                if not is_filtered_file(abs_path, project_root):
                    core_stats.add_file()
                    for fp, info in results:
                        core_stats.add_function(fp, info)  # 传递路径

    return all_stats, core_stats


def print_bar(value, max_val=20, width=15):
    if isinstance(value, (int, float)):
        filled = min(int(value / max_val * width), width) if max_val > 0 else 0
    else:
        filled = min(value, width)
    return "█" * filled + "░" * (width - filled)


def print_results(all_stats, core_stats, project_root):
    if all_stats.files_checked == 0:
        print("❌ 未找到可分析的Python文件")
        return

    print("\n" + "=" * 95)
    print(f"{'综合代码复杂度分析报告':^95}")
    print(f"{'(圈复杂度 + 时间/空间复杂度)':^95}")
    print("=" * 95)
    print(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 项目路径: {project_root}")

    # 1. 统计汇总
    print(f"\n📊 统计汇总对比")
    print(f"   {'指标':<30} {'全部文件':>20} {'核心业务代码':>25}")
    print(f"   {'-'*30} {'-'*20} {'-'*25}")
    print(f"   {'分析文件数':<30} {all_stats.files_checked:>20} {core_stats.files_checked:>25}")
    print(
        f"   {'分析函数/方法数':<30} {len(all_stats.functions):>20} {len(core_stats.functions):>25}"
    )
    print(
        f"   {'平均圈复杂度':<30} {all_stats.avg_cyclomatic():>20.1f} {core_stats.avg_cyclomatic():>25.1f}"
    )
    print(
        f"   {'最高圈复杂度':<30} {all_stats.max_cyclomatic():>20} {core_stats.max_cyclomatic():>25}"
    )

    high_risk_all = len(all_stats.get_high_risk_functions())
    high_risk_core = len(core_stats.get_high_risk_functions())
    print(f"   {'高风险函数数量':<30} {high_risk_all:>20} {high_risk_core:>25}")

    # 2. 圈复杂度分布
    print(f"\n🔄 圈复杂度分布（核心业务代码）")
    for level in ["🟢 简单", "🟡 中等", "🟠 复杂", "🔴 高风险", "🚫 极高风险"]:
        count = core_stats.cc_distribution.get(level, 0)
        bar = print_bar(count, max(1, len(core_stats.functions)), 20)
        print(f"   {level:<12}: {bar} {count}个")

    # 3. 时间复杂度分布
    print(f"\n⏱️  时间复杂度分布（核心业务代码）")
    time_order = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(n³)", "Recursive"]
    for time in time_order:
        count = core_stats.time_distribution.get(time, 0)
        if count > 0:
            symbol = TIME_RATING.get(time, ("⚪", 0))[0]
            bar = print_bar(count, max(1, len(core_stats.functions)), 15)
            print(f"   {symbol} {time:<10}: {bar} {count}个")

    # 4. 高风险函数 Top 15 - 修复：显示文件路径
    high_risk = core_stats.get_high_risk_functions()
    if high_risk:
        print(f"\n🚨 高风险函数列表（需优先重构）")
        sorted_risk = sorted(
            high_risk,
            key=lambda x: (x[1].cyclomatic, TIME_RATING.get(x[1].time_complexity, (None, 0))[1]),
            reverse=True,
        )

        for i, (filepath, func) in enumerate(sorted_risk[:15], 1):
            # 显示相对路径
            try:
                rel_path = Path(filepath).relative_to(Path(project_root))
                display_path = str(rel_path)[:45]  # 限制长度
            except:
                display_path = str(filepath)[:45]

            cc_bar = print_bar(func.cyclomatic, 50, 10)
            print(f"   {i}. {func.name:<30} @ {display_path}")
            print(
                f"      位置: 第{func.line}行 | 圈复杂度: {func.cyclomatic:>2} {cc_bar} {func.cc_rating[0]}"
            )
            print(f"      复杂度: 时间{func.time_complexity:<6} | 空间{func.space_complexity}")
            print(f"      风险: {func.risk_level} - {func.risk_reason}")
            print(f"      特征: {func.details}")
            if i < len(sorted_risk[:15]):
                print()

        if len(high_risk) > 15:
            print(f"   ... 还有 {len(high_risk)-15} 个高风险函数")

        # 特别显示极高风险（>=50）的函数
        extreme_risk = [(fp, f) for fp, f in high_risk if f.cyclomatic >= 50]
        if extreme_risk:
            print(f"\n🚫🚫🚫 极高风险函数（必须立即重构！）")
            for fp, func in extreme_risk:
                try:
                    rel_path = Path(fp).relative_to(Path(project_root))
                except:
                    rel_path = fp
                print(f"   🔥 {func.name} @ {rel_path}:{func.line}")
                print(
                    f"      圈复杂度: {func.cyclomatic} | 时间: {func.time_complexity} | {func.risk_reason}"
                )

    # 5. 优化建议
    print(f"\n💡 复杂度优化建议")
    suggestions = []
    avg_cc = core_stats.avg_cyclomatic()

    if avg_cc > 10:
        suggestions.append("项目整体圈复杂度偏高，建议引入策略模式减少if-else")
    if any(f.time_complexity == "O(n²)" for _, f in core_stats.functions):
        suggestions.append("存在O(n²)算法，大数据量时可能成为性能瓶颈，考虑使用哈希表优化")
    if any(f.time_complexity == "Recursive" for _, f in core_stats.functions):
        suggestions.append("检测到递归实现，建议改为迭代或使用@lru_cache装饰器")
    if any(f.cyclomatic > 20 for _, f in core_stats.functions):
        suggestions.append("存在极高圈复杂度函数(>20)，建议立即拆分为多个小函数")

    if not suggestions:
        print("   ✅ 代码整体质量良好，继续保持")
    else:
        for i, sug in enumerate(suggestions, 1):
            print(f"   {i}. {sug}")

    print("\n" + "=" * 95)


def main():
    try:
        script_dir = Path(__file__).resolve().parent
        project_root = find_project_root(script_dir)

        print(f"🔍 自动检测到项目根目录: {project_root}")
        print("🧮 正在分析综合复杂度（圈复杂度 + 时间/空间复杂度）...")

        source_dirs = ["src", ".", project_root.name]
        all_stats, core_stats = scan_project(project_root, source_dirs)

        if all_stats.files_checked == 0:
            print("❌ 未找到Python文件")
            input("\n按回车键退出...")
            return

        print_results(all_stats, core_stats, str(project_root))

    except Exception as e:
        print(f"\n❌ 脚本执行出错: {e}")
        traceback.print_exc()

    finally:
        if sys.platform == "win32":
            print("\n")
            input("按回车键退出...")


if __name__ == "__main__":
    main()
