#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目代码统计工具 (核心业务版)
只统计核心业务代码：src/main.py、src/start_windows.py、src/esg/目录(除__init__.py外)
"""

import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


class CodeStats:
    def __init__(self, name="全部文件"):
        self.name = name
        self.total_files = 0
        self.total_lines = 0
        self.code_lines = 0  # 实际代码行
        self.blank_lines = 0  # 空行
        self.comment_lines = 0  # 注释行
        self.file_details = []  # 单个文件详情

    def add_file(self, filepath, lines, code, blank, comment):
        self.total_files += 1
        self.total_lines += lines
        self.code_lines += code
        self.blank_lines += blank
        self.comment_lines += comment
        self.file_details.append(
            {"path": filepath, "total": lines, "code": code, "blank": blank, "comment": comment}
        )

    def avg_lines_per_file(self):
        return self.total_lines / self.total_files if self.total_files > 0 else 0


def find_project_root(start_path=None):
    """
    智能查找项目根目录（包含 src/ 目录的父目录）
    如果从 src/scripts 运行，应该返回 envision/ 而不是 envision/src/
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent

    current = start_path

    # 向上查找，直到找到包含 src 目录的目录（且 src 里有 esg 或 main.py）
    for _ in range(5):
        # 检查当前目录是否包含 src 子目录，且 src 看起来像业务代码目录
        src_dir = current / "src"
        if src_dir.exists() and src_dir.is_dir():
            # 进一步确认：src 里应该有 esg/ 或 main.py
            if (src_dir / "esg").exists() or (src_dir / "main.py").exists():
                return current  # 返回包含 src 的父目录（envision）

        # 如果没有，检查当前目录本身是否是 src（向上回溯的情况）
        if current.name == "src":
            parent = current.parent
            if parent.exists():
                return parent

        # 检查其他项目标志
        markers = [".git", "tests", "test", "pyproject.toml", "setup.py", "requirements.txt"]
        if any((current / marker).exists() for marker in markers):
            # 如果找到了项目标志，检查是否有 src 子目录
            if (current / "src").exists():
                return current

        parent = current.parent
        if parent == current:  # 到达根目录
            break
        current = parent

    # 如果都没找到，返回脚本所在目录的父目录（假设在 src/scripts/）
    return start_path.parent.parent


def analyze_file(filepath):
    """分析单个 Python 文件的行数统计"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"⚠️  无法读取文件 {filepath}: {e}")
        return None

    total_lines = len(lines)
    code_lines = 0
    blank_lines = 0
    comment_lines = 0
    in_multiline_string = False

    for line in lines:
        stripped = line.strip()

        # 空行检测
        if not stripped:
            blank_lines += 1
            continue

        # 多行字符串检测 (""" 或 ''')
        if '"""' in stripped or "'''" in stripped:
            quote_count = stripped.count('"""') + stripped.count("'''")
            if quote_count % 2 == 1:
                in_multiline_string = not in_multiline_string

        if in_multiline_string:
            comment_lines += 1
            continue

        # 单行注释检测
        if stripped.startswith("#"):
            comment_lines += 1
        else:
            code_lines += 1

    return {
        "total": total_lines,
        "code": code_lines,
        "blank": blank_lines,
        "comment": comment_lines,
    }


def is_core_business_file(filepath, root_path):
    """
    判断是否为真正的核心业务代码：
    ✅ 包含：src/main.py、src/start_windows.py、src/esg/下非__init__.py的文件
    ❌ 排除：其他所有文件（包括src/utils/、src/templates/、tests/、scripts/等）
    """
    path = Path(filepath)
    try:
        relative_path = path.relative_to(Path(root_path))
    except ValueError:
        return False

    parts = relative_path.parts
    filename = path.name

    # 1. 只处理 .py 文件
    if not filename.endswith(".py"):
        return False

    # 2. 排除 __init__.py
    if filename == "__init__.py":
        return False

    # 3. 排除 tests 和 scripts 目录
    if "tests" in parts or "test" in parts:
        return False
    if "scripts" in parts or "script" in parts:
        return False

    # 4. 必须位于 src 目录下
    if "src" not in parts:
        return False

    src_idx = parts.index("src")
    remaining_parts = parts[src_idx + 1 :]  # src 之后的相对路径部分

    # 5. src 根目录下的文件：只保留 main.py 和 start_windows.py
    if len(remaining_parts) == 1:
        return filename in ("main.py", "start_windows.py")

    # 6. src/esg/ 目录及其子目录下的文件：保留（核心业务）
    if len(remaining_parts) >= 1 and remaining_parts[0] == "esg":
        return True

    # 7. 其他 src/ 子目录（如 src/utils/、src/config/ 等）：排除
    return False


def scan_directory(directory):
    """
    递归扫描目录
    返回 (all_stats, core_stats, dir_stats)
    """
    exclude_dirs = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "env",
        "node_modules",
        ".idea",
        ".vscode",
        "build",
        "dist",
        "egg-info",
        ".tox",
        "logs",
        "temp_chroma_test",
    }

    all_stats = CodeStats("全部文件")
    core_stats = CodeStats("核心业务代码")
    dir_stats = defaultdict(lambda: {"files": 0, "lines": 0})

    directory = Path(directory).resolve()

    if not directory.exists():
        print(f"❌ 目录不存在 {directory}")
        return None, None, None

    print(f"🔍 扫描目录: {directory}")
    found_src = False

    for root, dirs, files in os.walk(directory):
        # 排除缓存和依赖目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        current_dir = Path(root)

        # 检查是否是 src 目录（用于调试）
        if current_dir.name == "src" and "esg" in dirs:
            found_src = True
            print(f"   ✅ 发现 src 目录: {current_dir}")

        for filename in files:
            if not filename.endswith(".py"):
                continue

            filepath = current_dir / filename

            # 计算相对于项目根目录的路径
            try:
                relative_path = filepath.relative_to(directory)
            except ValueError:
                continue

            result = analyze_file(filepath)
            if not result:
                continue

            # 始终加入全部统计
            all_stats.add_file(
                str(relative_path),
                result["total"],
                result["code"],
                result["blank"],
                result["comment"],
            )

            # 判断是否为核心业务代码
            if is_core_business_file(filepath, directory):
                core_stats.add_file(
                    str(relative_path),
                    result["total"],
                    result["code"],
                    result["blank"],
                    result["comment"],
                )
                # 按目录分组统计（显示 esg/ 下的子目录）
                rel_str = str(relative_path)
                if "esg" in rel_str:
                    # 提取 esg/ 下的第一级子目录
                    parts = relative_path.parts
                    if "esg" in parts:
                        esg_idx = parts.index("esg")
                        if len(parts) > esg_idx + 1:
                            dir_name = f"esg/{parts[esg_idx + 1]}"
                        else:
                            dir_name = "esg"
                    else:
                        dir_name = "esg"
                else:
                    dir_name = str(relative_path.parent)
                    if dir_name == ".":
                        dir_name = "[根目录]"

                dir_stats[dir_name]["files"] += 1
                dir_stats[dir_name]["lines"] += result["total"]

    if not found_src:
        print(f"   ⚠️  警告: 未找到 src/ 目录，请确认项目结构")

    return all_stats, core_stats, dir_stats


def print_bar(value, max_val, width=20):
    """打印ASCII进度条"""
    if max_val == 0:
        filled = 0
    else:
        filled = min(int(value / max_val * width), width)
    return "█" * filled + "░" * (width - filled)


def print_results(all_stats, core_stats, dir_stats, project_root):
    """格式化输出统计结果"""
    if all_stats.total_files == 0:
        print("❌ 未找到 Python 文件")
        return

    print("\n" + "=" * 85)
    print(f"{'envision 项目代码统计报告':^85}")
    print("=" * 85)
    print(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 项目路径: {project_root}")
    print(f"📊 统计范围: 核心业务代码 (src/main.py, src/start_windows.py, src/esg/*)")

    # 1. 全部文件统计（参考）
    print(f"\n📁 【项目全部文件统计】（参考）")
    print(f"   文件总数: {all_stats.total_files} 个")
    print(f"   总行数:   {all_stats.total_lines:,} 行")
    print(
        f"   代码行:   {all_stats.code_lines:,} 行 ({all_stats.code_lines/all_stats.total_lines*100:.1f}%)"
    )
    print(
        f"   注释行:   {all_stats.comment_lines:,} 行 ({all_stats.comment_lines/all_stats.total_lines*100:.1f}%)"
    )
    print(
        f"   空行:     {all_stats.blank_lines:,} 行 ({all_stats.blank_lines/all_stats.total_lines*100:.1f}%)"
    )

    # 2. 核心业务代码统计
    print(f"\n🎯 【核心业务代码统计】")
    if core_stats.total_files > 0:
        print(f"   文件总数: {core_stats.total_files} 个")
        print(f"   总行数:   {core_stats.total_lines:,} 行")
        print(
            f"   代码行:   {core_stats.code_lines:,} 行 ({core_stats.code_lines/core_stats.total_lines*100:.1f}%)"
        )
        print(
            f"   注释行:   {core_stats.comment_lines:,} 行 ({core_stats.comment_lines/core_stats.total_lines*100:.1f}%)"
        )
        print(
            f"   空行:     {core_stats.blank_lines:,} 行 ({core_stats.blank_lines/core_stats.total_lines*100:.1f}%)"
        )
        print(f"   平均每文件: {core_stats.avg_lines_per_file():.0f} 行")
    else:
        print("   ⚠️  未找到核心业务代码文件")
        print("   检查: 项目根目录是否正确？是否包含 src/esg/ 目录？")
        return

    # 3. 业务代码 vs 其他对比
    print(f"\n📊 核心业务代码占比")
    print(f"   {'指标':<20} {'全部项目':>12} {'核心业务':>12} {'占比':>10}")
    print(f"   {'-'*20} {'-'*12} {'-'*12} {'-'*10}")

    if all_stats.total_files > 0:
        file_ratio = core_stats.total_files / all_stats.total_files * 100
        print(
            f"   {'文件数量':<20} {all_stats.total_files:>12} {core_stats.total_files:>12} {file_ratio:>9.1f}%"
        )

    if all_stats.total_lines > 0:
        line_ratio = core_stats.total_lines / all_stats.total_lines * 100
        print(
            f"   {'代码总行数':<20} {all_stats.total_lines:>12,} {core_stats.total_lines:>12,} {line_ratio:>9.1f}%"
        )

    if all_stats.code_lines > 0:
        code_ratio = core_stats.code_lines / all_stats.code_lines * 100
        print(
            f"   {'实际代码行':<20} {all_stats.code_lines:>12,} {core_stats.code_lines:>12,} {code_ratio:>9.1f}%"
        )

    # 4. 核心业务目录分布 (Top 15)
    if dir_stats and core_stats.total_files > 0:
        print(f"\n📂 【核心业务目录分布】")
        sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]["lines"], reverse=True)
        max_lines = max(x[1]["lines"] for x in sorted_dirs) if sorted_dirs else 0

        for i, (dir_name, info) in enumerate(sorted_dirs[:15], 1):
            bar = print_bar(info["lines"], max_lines, 20)
            print(f"   {i:2d}. {dir_name:<35} {bar} {info['files']:>3}文件, {info['lines']:>6,}行")

    # 5. 最大核心业务文件 Top 10
    if core_stats.file_details:
        print(f"\n📝 【最大核心业务文件 Top 10】")
        sorted_files = sorted(core_stats.file_details, key=lambda x: x["total"], reverse=True)
        for i, f in enumerate(sorted_files[:10], 1):
            print(
                f"   {i:2d}. {f['path']:<50} {f['total']:>6,}行 "
                f"(代码:{f['code']:>6}, 注释:{f['comment']:>5}, 空行:{f['blank']:>5})"
            )

    # 6. 代码密度分析
    if core_stats.file_details:
        high_code_density = [
            f for f in core_stats.file_details if f["total"] > 50 and f["code"] / f["total"] > 0.8
        ]
        if high_code_density:
            print(f"\n🎯 【高代码密度文件】(>80%实际代码, 超过50行)")
            for f in high_code_density[:5]:
                ratio = f["code"] / f["total"] * 100
                print(f"   • {f['path']}: {ratio:.1f}% 为实际代码 ({f['code']}/{f['total']}行)")

    print("\n" + "=" * 85)


def main():
    try:
        # 智能检测项目根目录
        script_dir = Path(__file__).resolve().parent
        project_root = find_project_root(script_dir)

        print(f"🔍 脚本位置: {script_dir}")
        print(f"🔍 检测到项目根目录: {project_root}")
        print("📊 正在统计核心业务代码...")
        print("   (范围: src/main.py, src/start_windows.py, src/esg/*)")

        all_stats, core_stats, dir_stats = scan_directory(project_root)

        if all_stats is None:
            print("❌ 扫描失败")
            input("\n按回车键退出...")
            return

        if all_stats.total_files == 0:
            print("❌ 未找到 Python 文件")
            input("\n按回车键退出...")
            return

        print_results(all_stats, core_stats, dir_stats, str(project_root))

    except Exception as e:
        print(f"\n❌ 脚本执行出错: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if sys.platform == "win32":
            print("\n")
            input("按回车键退出...")


if __name__ == "__main__":
    main()
